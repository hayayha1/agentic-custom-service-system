"""Prediction worker: input only, with a runtime read guard against reference answers.

Run this process to completion BEFORE starting score_route_planner.py.
The worker imports the unchanged production GoalPlanner and executes no handlers.
"""
import argparse
import asyncio
import hashlib
import json
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.route_planner_common import DATASET, ROOT, file_hash, read_public, source_hashes, write_json


def install_read_guard():
    reads = set()
    forbidden = [str(DATASET / "private").casefold(), str(DATASET / "results").casefold(),
                 str(ROOT / "scripts/build_route_planner_dataset.py").casefold()]
    blocked = []
    def audit(event, args):
        if event != "open" or not isinstance(args[0], (str, bytes)):
            return
        path = str(Path(args[0]).resolve())
        if any(path.casefold().startswith(prefix) for prefix in forbidden):
            blocked.append(path)
            raise PermissionError("Blind inference cannot read reference answers or their builder")
        mode = args[1]
        if mode is None or "r" in str(mode):
            reads.add(path)
    sys.addaudithook(audit)
    return reads, blocked


def safe_error(exc):
    import httpx
    from pydantic import ValidationError
    if isinstance(exc, ValidationError):
        return {"type": type(exc).__name__, "fields": [
            {"loc": list(e["loc"]), "type": e["type"]} for e in exc.errors(include_input=False)]}
    if isinstance(exc, httpx.HTTPStatusError):
        return {"type": type(exc).__name__, "status_code": exc.response.status_code}
    return {"type": type(exc).__name__}


async def probe():
    from pydantic import BaseModel
    from app.services.agent.contracts import function_schema
    from app.services.agent.llm import native_client
    class Probe(BaseModel):
        available: bool
    if not native_client.enabled:
        raise RuntimeError("No native model credentials; refuse to report offline execution as live")
    result = await native_client.call([
        {"role": "system", "content": "连接测试，请只调用 connection_check 并将 available 设为 true。"},
        {"role": "user", "content": "检查连接"}
    ], [function_schema("connection_check", "检查原生工具调用连通性", Probe)], force="connection_check")
    print(json.dumps({"probe": "ok", "function": result["name"], "usage": result.get("usage", {})}), flush=True)


async def run(args):
    reads, blocked = install_read_guard()
    if args.probe:
        await probe()
        return 0
    from app.services.agent.llm import native_client
    from app.services.agent.planning import GoalPlanner
    from app.services.model_service import model_service
    from app.services.agent.safety import redact
    cases = read_public(args.inputs)
    if args.mode == "native" and not native_client.enabled:
        raise RuntimeError("Native evaluation requires credentials; offline fallback is forbidden")
    if args.mode == "offline":
        model_service.llm_api_key = ""
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    started_at = datetime.now(timezone.utc).isoformat()
    original_hashes = source_hashes()
    input_digest = file_hash(args.inputs)
    jobs = [(repeat, case) for repeat in range(1, args.repeats + 1) for case in cases]
    random.Random(20261107).shuffle(jobs)
    semaphore = asyncio.Semaphore(args.concurrency)
    counters = Counter()
    predictions_path = output / "predictions.jsonl"

    async def predict(repeat, case):
        async with semaphore:
            planner = GoalPlanner()
            route_times, calls = [], []
            original_route = planner.fast_route
            original_call = native_client.call
            # GoalPlanner uses a module global client. Use ContextVar dispatch
            # below so concurrent requests cannot record each other's payloads.
            def measured_route(query):
                t0 = time.perf_counter()
                result = original_route(query)
                route_times.append({"elapsed_ms": (time.perf_counter() - t0) * 1000,
                                    "matched_fast": result is not None})
                return result
            planner.fast_route = measured_route
            token = active_calls.set(calls)
            started = time.perf_counter()
            plan, error = None, None
            try:
                plan = await planner.analyze_and_plan(
                    query=case.query, customer_id="benchmark_customer",
                    session_id="benchmark_session", context=case.context)
            except Exception as exc:
                error = safe_error(exc)
            finally:
                active_calls.reset(token)
            elapsed = (time.perf_counter() - started) * 1000
            route = "Fast-Path" if route_times and route_times[0]["matched_fast"] else "Deep-Path"
            record = {"case_id": case.case_id, "repeat": repeat, "mode": args.mode,
                "observed_route": route, "route_latency_ms": route_times[0]["elapsed_ms"] if route_times else None,
                "planning_latency_ms": elapsed,
                "planner_calls": sum(call["force"] == "submit_plan" for call in calls),
                "model_call_count": len(calls), "plan": plan.model_dump() if plan else None,
                "error": error, "calls": calls, "business_handler_calls": 0}
            with predictions_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(redact(record), ensure_ascii=False) + "\n")
                stream.flush()
            counters["completed"] += 1
            counters[route] += 1
            if error:
                counters["errors"] += 1
            if counters["completed"] % 10 == 0 or counters["completed"] == len(jobs):
                print(json.dumps({"progress": counters["completed"], "total": len(jobs), "errors": counters["errors"]}), flush=True)

    from contextvars import ContextVar
    active_calls = ContextVar("blind_benchmark_calls", default=None)
    production_call = native_client.call
    async def audited_call(messages, tools, force=None):
        sink = active_calls.get()
        payload = {"messages": messages, "tools": tools, "force": force}
        # The full, secret-free request projection is retained for leak audits.
        event = {"force": force, "request": payload,
                 "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
        if sink is not None:
            sink.append(event)
        t0 = time.perf_counter()
        try:
            result = await production_call(messages, tools, force)
            event["response"] = result
            return result
        except Exception as exc:
            event["error"] = safe_error(exc)
            raise
        finally:
            event["elapsed_ms"] = (time.perf_counter() - t0) * 1000
    native_client.call = audited_call
    status = "complete"
    try:
        await asyncio.gather(*(predict(repeat, case) for repeat, case in jobs))
    except BaseException:
        status = "interrupted"
        raise
    finally:
        native_client.call = production_call
        current_hashes = source_hashes()
        audit = {"status": status, "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
            "model": native_client.model_name if args.mode == "native" else None,
            "endpoint": model_service.llm_base_url if args.mode == "native" else None,
            "repeats": args.repeats, "concurrency": args.concurrency,
            "unique_cases": len(cases), "expected_predictions": len(jobs), "counters": dict(counters),
            "input_sha256": input_digest, "prediction_sha256": file_hash(predictions_path) if predictions_path.exists() else None,
            "sources_before": original_hashes, "sources_after": current_hashes,
            "sources_unchanged": original_hashes == current_hashes,
            "reference_reads_blocked": blocked,
            "reference_answers_loaded": False,
            "file_reads": sorted(reads),
            "business_handler_calls": 0}
        write_json(output / "inference_seal.json", audit)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=DATASET / "inputs.jsonl")
    parser.add_argument("--output", default="scratch/route-planner-native")
    parser.add_argument("--mode", choices=["native", "offline"], default="native")
    parser.add_argument("--repeats", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--concurrency", type=int, choices=range(1, 5), default=3)
    parser.add_argument("--probe", action="store_true")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
