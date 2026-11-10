"""Isolated Agent regression runner. Default: offline fixtures, no live writes.

python -m scripts.evaluate_agent --output scratch/agent-baseline.json
--live enables native planner/judges, while ERP remains an isolated demo adapter.
"""
import argparse
import asyncio
import json
import tempfile
import uuid
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch, AsyncMock

import httpx

from app.services.agent.evaluation import evaluate, load_cases
from app.services.agent.evolution import EvolutionService
from app.services.agent.knowledge_tool import KnowledgeCollaboratorResult
from app.services.agent.llm import NativeToolClient
from app.services.agent.policy import AgentPolicy
from app.services.agent.storage import AgentStore
from app.services.model_service import model_service
from app.workflow.agent_runtime import AgentRuntime


async def run(args):
    cases = load_cases(args.dataset)
    policy = AgentPolicy.model_validate_json(Path(args.policy).read_text(encoding="utf-8")) if args.policy else AgentPolicy()
    if not args.live:
        model_service.llm_api_key = ""
        model_service.embedding_api_key = ""
        model_service.rerank_api_key = ""
    judges = [NativeToolClient(model=name) for name in args.judge_model]
    if judges and not args.live:
        raise ValueError("Judges require --live and model credentials")
    with tempfile.TemporaryDirectory(prefix="agent-eval-") as directory:
        url = "sqlite+aiosqlite:///" + Path(directory, "state.db").as_posix()
        store = AgentStore(url, redis_url="")
        runtime = AgentRuntime(store, policy=policy)

        async def run_case(case):
            state = {"tenant_id": "eval_" + case.id, "customer_id": "user_001", "user_id": "user_001",
                     "role": "user", "session_id": str(uuid.uuid4()), "product_code": "SAAS_CLOUD", "kb_id": "fixture"}
            if case.fixture in {"unpaid", "refunding"}:
                from app.services.agent.contracts import RequestIdentity
                from app.services.business_service import business_service
                backend = await runtime.gateway._backend_customer(RequestIdentity(**{k: state[k] for k in (
                    "tenant_id", "customer_id", "user_id", "role", "session_id")}))
                orders = await business_service.get_customer_orders(backend)
                orders[0]["status"] = "UNPAID" if case.fixture == "unpaid" else "REFUNDING"
                if case.fixture == "refunding":
                    orders[0]["refund_info"] = {"refund_id": "REF-FIXTURE", "refund_amount": "¥12,800.00",
                                                 "reason": "拍错了", "stage": "审核中"}
                await store.put("business:" + backend, orders)
            # Offline fixtures exercise workflow behavior; they do not measure live retrieval quality.
            with ExitStack() as stack:
                if case.fixture == "logistics_500":
                    stack.enter_context(patch.dict(runtime.gateway.center.handlers, {
                        "query_logistics": AsyncMock(side_effect=httpx.ConnectError("fixture dependency failure"))}))
                if case.fixture in {"policy", "missing_policy"}:
                    found = case.fixture == "policy"
                    result = KnowledgeCollaboratorResult(
                        content="根据售后规则，符合条件的商品支持七天无理由退货。" if found else "未找到可核验的政策，请联系人工客服。",
                        sources=[{"doc_id": "doc", "doc_name": "售后政策", "chunk_id": "chunk", "snippet": "七天无理由退货"}] if found else [],
                        top_score=.95 if found else .1, reply_type="DIRECT_ANSWER" if found else "FALLBACK")
                    stack.enter_context(patch("app.workflow.agent_runtime.knowledge_tool.execute_retrieval", AsyncMock(return_value=result)))
                turns = []
                for query in case.turns:
                    turns.append(await runtime.ainvoke({**state, "raw_query": query}))
                return turns

        try:
            report = await evaluate(cases, run_case, judges=judges, policy_digest=policy.digest,
                                    mode="native_fixture" if args.live else "offline_fixture")
        finally:
            await store.engine.dispose()
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        report["gate"] = EvolutionService.gate(baseline, report)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass_rate": report["pass_rate"], "score": report["score"],
                      "gate": report.get("gate"), "output": str(output)}, ensure_ascii=False))
    return 0 if all(c["passed"] for c in report["cases"]) and ("gate" not in report or report["gate"]["accepted"]) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="data/evaluation/agent_regression.jsonl")
    parser.add_argument("--output", default="scratch/agent-evaluation.json")
    parser.add_argument("--policy")
    parser.add_argument("--baseline")
    parser.add_argument("--judge-model", action="append", default=[])
    parser.add_argument("--live", action="store_true")
    return asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
