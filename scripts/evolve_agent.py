"""Mine failures and evaluate an isolated candidate before queuing a release.

The candidate never changes the running Agent. Equal scores are rejected.
"""
import argparse
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from app.services.agent.evolution import evolution_service
from app.services.agent.storage import agent_store
from app.services.model_service import model_service
from scripts.evaluate_agent import run as evaluate_run


async def run(args):
    if not args.live:
        model_service.llm_api_key = ""
        model_service.embedding_api_key = ""
        model_service.rerank_api_key = ""
    trace_ids = args.trace_id or [trace["trace_id"] for trace in (await evolution_service.mine(args.tenant_id))[:20]]
    candidate = await evolution_service.propose(args.tenant_id, trace_ids)
    output = Path(args.output_dir) / candidate["id"]
    output.mkdir(parents=True, exist_ok=True)
    policy = output / "candidate-policy.json"
    policy.write_text(json.dumps(candidate["diagnosis"]["candidate"], ensure_ascii=False, indent=2), encoding="utf-8")
    common = {"dataset": args.dataset, "live": args.live, "judge_model": args.judge_model, "baseline": None}
    baseline_path = Path(args.baseline) if args.baseline else output / "baseline.json"
    if not args.baseline:
        await evaluate_run(SimpleNamespace(**common, policy=None, output=str(baseline_path)))
    candidate_report_path = output / "candidate-report.json"
    await evaluate_run(SimpleNamespace(**common, policy=str(policy), output=str(candidate_report_path)))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    report = json.loads(candidate_report_path.read_text(encoding="utf-8"))
    decision = await evolution_service.queue(args.tenant_id, candidate["id"], baseline, report)
    (output / "decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"candidate_id": candidate["id"], "status": decision["status"], "gate": decision["gate"]}, ensure_ascii=False))
    return 0 if decision["status"] == "release_pending" else 1


async def main_async(args):
    try:
        return await run(args)
    finally:
        await agent_store.engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--trace-id", action="append", default=[])
    parser.add_argument("--dataset", default="data/evaluation/agent_regression.jsonl")
    parser.add_argument("--output-dir", default="scratch/agent-evolution")
    parser.add_argument("--baseline")
    parser.add_argument("--judge-model", action="append", default=[])
    parser.add_argument("--live", action="store_true")
    return asyncio.run(main_async(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
