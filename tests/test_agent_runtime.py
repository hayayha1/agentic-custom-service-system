"""Behavioral regression for durable execution, authorization and offline gates."""
import asyncio
import copy
import json
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio

from app.core.config import settings
from app.services.agent.contracts import RequestIdentity, Observation
from app.services.agent.evaluation import EvaluationCase, assert_trace, evaluate, load_cases
from app.services.agent.evolution import EvolutionService
from app.services.agent.gateway import ToolGateway
from app.services.agent.llm import native_client
from app.services.agent.memory import DurableMemory
from app.services.agent.planner import TaskPlan, SubTask, goal_planner
from app.services.agent.safety import confirmation_answer, redact
from app.services.agent.storage import AgentStore, SessionBusy, scope_key, tenant_key
from app.services.model_service import model_service
from app.workflow.agent_runtime import AgentRuntime


@pytest_asyncio.fixture
async def store(tmp_path, monkeypatch):
    monkeypatch.setattr(model_service, "llm_api_key", "")
    monkeypatch.setattr(model_service, "embedding_api_key", "")
    monkeypatch.setattr(model_service, "rerank_api_key", "")
    storage = AgentStore("sqlite+aiosqlite:///" + (tmp_path / "agent.db").as_posix(), redis_url="")
    yield storage
    await storage.engine.dispose()


def identity(tenant="tenant_a", session="session", customer="user_001"):
    return RequestIdentity(tenant_id=tenant, session_id=session, customer_id=customer, user_id=customer, role="user")


def state(query, tenant="tenant_a", session="session", customer="user_001"):
    return {**identity(tenant, session, customer).model_dump(), "kb_id": "kb", "product_code": "SAAS_CLOUD", "raw_query": query}


REFUND = "订单 ORD-20261025-8891 申请退款，原因是拍错了"


@pytest.mark.asyncio
async def test_approval_survives_new_runtime_and_store(store):
    runtime = AgentRuntime(store)
    pending = await runtime.ainvoke(state(REFUND))
    assert pending["status"] == "waiting_approval"
    assert pending["observations"] == []
    other_store = AgentStore(str(store.engine.url), redis_url="")
    try:
        resumed = await AgentRuntime(other_store).ainvoke(state("确认"))
        assert resumed["status"] == "completed"
        assert resumed["business_data"]["card_type"] == "REFUND_CARD"
        assert len(resumed["observations"]) == 1
        assert resumed["parameters"] == {}
        assert resumed["approval"] == {}
        duplicate = await AgentRuntime(other_store).ainvoke(state("确认"))
        assert duplicate["observations"] == []
        assert "暂无" in duplicate["final_content"]
    finally:
        await other_store.engine.dispose()


@pytest.mark.asyncio
async def test_compound_task_never_bypasses_approval(store):
    runtime = AgentRuntime(store)
    result = await runtime.ainvoke(state("查一下订单 ORD-20261025-8891 的物流，顺便申请退款，原因是拍错了"))
    assert result["status"] == "waiting_approval"
    assert [o["call"]["name"] for o in result["observations"]] == ["query_logistics"]
    result = await runtime.ainvoke(state("确认"))
    assert result["status"] == "completed"
    assert [o["call"]["name"] for o in result["observations"]] == ["query_logistics", "apply_refund"]


@pytest.mark.asyncio
async def test_clarification_survives_restart_with_bare_slot_answers(store):
    result = await AgentRuntime(store).ainvoke(state("我想申请退款"))
    assert result["business_data"]["missing_slot"] == "order_id"
    result = await AgentRuntime(store).ainvoke(state("ORD-20261025-8891"))
    assert result["business_data"]["missing_slot"] == "refund_reason"
    result = await AgentRuntime(store).ainvoke(state("退款原因：拍错了"))
    assert result["status"] == "waiting_approval"
    result = await AgentRuntime(store).ainvoke(state("不确认"))
    assert result["status"] == "cancelled"
    assert result["observations"] == []


@pytest.mark.parametrize("text", ["不确认", "不要确认", "取消", "暂不取消", "不同意"])
def test_negative_confirmation_cannot_authorize(text):
    assert confirmation_answer(text) is False


@pytest.mark.parametrize("text", ["我不确定要不要确认", "好的，但不要退款", "确认修改为其他地址", "确认？先等等", "办理"])
def test_ambiguous_confirmation_cannot_authorize(text):
    assert confirmation_answer(text) is None


@pytest.mark.asyncio
async def test_tenant_customer_session_isolation(store):
    a = AgentRuntime(store)
    await a.ainvoke(state(REFUND, tenant="a"))
    b = await a.ainvoke(state("确认", tenant="b"))
    assert b["observations"] == []
    wrong_session = await a.ainvoke(state("确认", tenant="a", session="other"))
    assert wrong_session["observations"] == []
    assert (await a.ainvoke(state("确认", tenant="a")))["status"] == "completed"
    a_orders = await a.gateway.execute("query_orders", {}, identity("a"), "read")
    b_orders = await a.gateway.execute("query_orders", {}, identity("b"), "read")
    assert a_orders.data["orders"][0]["status"] == "REFUNDING"
    assert b_orders.data["orders"][0]["status"] == "PAID"
    assert scope_key("a:b", "c") != scope_key("a", "b:c")


@pytest.mark.asyncio
async def test_foreign_order_and_injected_identity_denied(store):
    gateway = ToolGateway(store)
    result = await gateway.execute("query_logistics", {"order_id": "ORD-20261020-3320"}, identity(), "foreign")
    assert result.status == "denied"
    result = await gateway.execute("apply_invoice", {"order_id": "ORD-20261025-8891", "invoice_title": "测试公司",
                                                   "customer_id": "user_002"}, identity(), "injected")
    assert result.status == "validation_error"
    attacker = identity().model_copy(update={"user_id": "user_002"})
    assert (await gateway.execute("query_orders", {}, attacker, "impersonate")).status == "denied"


@pytest.mark.asyncio
async def test_write_idempotency_and_uncertain_timeout(store, monkeypatch):
    gateway = ToolGateway(store)
    handler = AsyncMock(return_value=__import__("app.services.agent.tools", fromlist=["ToolExecutionResult"]).ToolExecutionResult(
        success=True, tool_name="apply_invoice", message="已提交"))
    monkeypatch.setitem(gateway.center.handlers, "apply_invoice", handler)
    params = {"order_id": "ORD-20261025-8891", "invoice_title": "测试有限公司"}
    first = await gateway.execute("apply_invoice", params, identity(), "same")
    second = await gateway.execute("apply_invoice", params, identity(), "same")
    assert first.status == second.status == "success"
    assert handler.await_count == 1
    handler.side_effect = TimeoutError()
    third = await gateway.execute("apply_invoice", params, identity(), "timeout")
    fourth = await gateway.execute("apply_invoice", params, identity(), "timeout")
    assert third.status == fourth.status == "uncertain"
    assert handler.await_count == 2


@pytest.mark.asyncio
async def test_gateway_high_risk_cannot_execute_without_authorization(store):
    result = await ToolGateway(store).execute("apply_refund", {"order_id": "ORD-20261025-8891", "refund_reason": "拍错了"}, identity(), "unapproved")
    assert result.status == "approval_required"


@pytest.mark.asyncio
async def test_retry_circuit_and_rate_limit(store, monkeypatch):
    gateway = ToolGateway(store)
    handler = AsyncMock(side_effect=httpx.ConnectError("offline"))
    monkeypatch.setitem(gateway.center.handlers, "query_logistics", handler)
    monkeypatch.setattr(settings, "AGENT_CIRCUIT_THRESHOLD", 2)
    result = await gateway.execute("query_logistics", {}, identity(), "read")
    assert result.status == "unavailable"
    assert handler.await_count == 2
    result = await gateway.execute("query_logistics", {}, identity(), "read2")
    assert result.status == "unavailable"
    assert handler.await_count == 2
    monkeypatch.setattr(settings, "AGENT_TOOL_RATE_LIMIT", 1)
    params = {"order_id": "ORD-20261025-8891"}
    assert (await gateway.execute("expedite_shipping", params, identity(), "write1")).success
    assert (await gateway.execute("expedite_shipping", params, identity(), "write2")).status == "unavailable"


@pytest.mark.asyncio
async def test_validation_boundaries(store):
    gateway = ToolGateway(store)
    for amount in [-1, 0, float("nan"), float("inf"), 10000001]:
        result = await gateway.execute("apply_refund", {"order_id": "ORD-20261025-8891", "refund_reason": "拍错了",
                                                       "refund_amount": amount}, identity(), str(amount), approved=True)
        assert result.status == "validation_error"
    too_much = await gateway.execute("apply_refund", {"order_id": "ORD-20261025-8891", "refund_reason": "拍错了",
                                                     "refund_amount": 999999.0}, identity(), "excess", approved=True)
    assert too_much.status == "validation_error"


@pytest.mark.asyncio
async def test_cross_instance_lease_rejects_concurrent_resume(store):
    second = AgentStore(str(store.engine.url), redis_url="")
    try:
        async with store.lock("session:test"):
            with pytest.raises(SessionBusy):
                async with second.lock("session:test"):
                    pytest.fail("two workers acquired one session")
        async with second.lock("session:test"):
            pass
    finally:
        await second.engine.dispose()


@pytest.mark.asyncio
async def test_iteration_guard_stops_remaining_steps(store, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MAX_ITERATIONS", 1)
    result = await AgentRuntime(store).ainvoke(state("查一下订单 ORD-20261025-8891 的物流，顺便申请退款，原因是拍错了"))
    assert result["status"] == "iteration_limit"
    assert result["iterations"] == 1
    assert [o["call"]["name"] for o in result["observations"]] == ["query_logistics"]


@pytest.mark.asyncio
async def test_timeout_is_bounded(store, monkeypatch):
    runtime = AgentRuntime(store)
    async def slow(**kwargs):
        await asyncio.sleep(2)
    monkeypatch.setitem(runtime.gateway.center.handlers, "query_logistics", slow)
    monkeypatch.setattr(settings, "AGENT_TIMEOUT_SECONDS", .5)
    result = await runtime.ainvoke(state("查一下我的物流"))
    assert result["status"] == "timeout"


@pytest.mark.asyncio
async def test_memory_compression_profiles_and_tenant_boundaries(store, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MEMORY_WINDOW", 3)
    memory = DurableMemory(store)
    who = identity()
    await memory.set_profile(who, {"invoice_title": "明确提供的公司"})
    for index in range(7):
        await memory.remember(who, "退款原因" + str(index), "已记录", {"order_id": "ORD-20261025-8891"})
    recalled = await DurableMemory(store).load(who)
    assert len(recalled["episode"]["turns"]) <= 3
    assert recalled["episode"]["summary"]
    assert recalled["episode"]["entities"]["order_id"] == "ORD-20261025-8891"
    assert recalled["profile"]["invoice_title"] == "明确提供的公司"
    assert (await memory.load(identity("other")))["profile"] == {}
    assert await memory.recall(who, "退款原因")


def test_recursive_pii_masking():
    raw = {"content": "电话13911112222 身份证110101199001011234 卡号6222021234567890123 邮箱test@example.com",
           "card": {"phone": "13911112222", "api_key": "sensitive"}}
    masked = json.dumps(redact(raw))
    for secret in ["13911112222", "110101199001011234", "6222021234567890123", "test@example.com", "sensitive"]:
        assert secret not in masked


def test_dag_rejects_cycles_and_misclassified_writes():
    with pytest.raises(ValueError):
        TaskPlan(intent_category="TASK_EXECUTION", subtasks=[SubTask(step_id=1, task_type="WRITE_TOOL",
                 tool_name="apply_refund", description="refund", depends_on=[1])])
    with pytest.raises(ValueError):
        TaskPlan(intent_category="TASK_EXECUTION", subtasks=[SubTask(step_id=1, task_type="READ_TOOL",
                 tool_name="apply_refund", description="refund")])


@pytest.mark.asyncio
async def test_native_plan_react_observation_and_finish(store, monkeypatch):
    monkeypatch.setattr(model_service, "llm_api_key", "fixture")
    plan = goal_planner.offline_plan("查一下我的物流").model_dump()
    calls = []
    async def native(messages, tools, force=None):
        calls.append((messages, tools, force))
        if force == "submit_plan":
            return {"name": force, "arguments": plan, "id": "plan", "usage": {"total_tokens": 10}}
        if force == "finish":
            assert "observations" in messages[-1]["content"]
            return {"name": force, "arguments": {"completed": True}, "usage": {"total_tokens": 3}}
        return {"name": "query_logistics", "arguments": {}, "id": "call", "usage": {"total_tokens": 5}}
    monkeypatch.setattr(native_client, "call", native)
    result = await AgentRuntime(store).ainvoke(state("查一下我的物流"))
    assert result["status"] == "completed"
    assert result["tokens"] == 18
    assert [c[2] for c in calls] == ["submit_plan", None, "finish"]
    assert result["plan"]["planner_mode"] == "native"


@pytest.mark.asyncio
async def test_native_reacts_to_observation_and_repairs_arguments(store, monkeypatch):
    monkeypatch.setattr(model_service, "llm_api_key", "fixture")
    plan = goal_planner.offline_plan("查一下我的物流").model_dump()
    invocation = 0
    async def native(messages, tools, force=None):
        nonlocal invocation
        if force == "submit_plan":
            return {"arguments": plan, "usage": {}}
        if force == "finish":
            return {"arguments": {"completed": True}, "usage": {}}
        invocation += 1
        if invocation == 2:
            assert any(m["role"] == "tool" for m in messages)
        return {"name": "query_logistics", "arguments": {}, "usage": {}}
    monkeypatch.setattr(native_client, "call", native)
    gateway = ToolGateway(store)
    calls = 0
    original = gateway.execute
    async def execute(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Observation(status="validation_error", tool_name="query_logistics", message="请核对查询条件")
        return await original(*args, **kwargs)
    runtime = AgentRuntime(store)
    monkeypatch.setattr(runtime.gateway, "execute", execute)
    result = await runtime.ainvoke(state("查一下我的物流"))
    assert result["status"] == "completed"
    assert result["iterations"] == 2


def report(scores, passed=None):
    return {"dataset_digest": "same", "mode": "offline_fixture", "judge_models": [], "cases": [
        {"id": str(i), "score": score, "passed": passed[i] if passed else True, "failures": []}
        for i, score in enumerate(scores)]}


def test_gate_requires_strict_improvement_and_zero_regression():
    assert EvolutionService.gate(report([.5, .8]), report([.7, .8]))["accepted"]
    assert not EvolutionService.gate(report([.5, .8]), report([.5, .8]))["accepted"]
    assert not EvolutionService.gate(report([.5, .8]), report([1, .7]))["accepted"]
    wrong_set = {**report([1, 1]), "dataset_digest": "other"}
    assert not EvolutionService.gate(report([.5, .8]), wrong_set)["accepted"]
    assert not EvolutionService.gate(report([.5, .8]), report([1]))["accepted"]
    assert not EvolutionService.gate(report([.5]), report([float("nan")]))["accepted"]


@pytest.mark.asyncio
async def test_feedback_diagnostics_and_candidate_never_activates_online(store):
    runtime = AgentRuntime(store)
    result = await runtime.ainvoke(state("你好"))
    service = EvolutionService(store)
    await store.put(tenant_key("message_trace", "tenant_a", "message"), {"trace_id": result["trace_id"]})
    await service.record_feedback("tenant_a", "message", "没有解决问题")
    candidate = await service.propose("tenant_a", [result["trace_id"]])
    assert candidate["status"] == "candidate"
    baseline = report([.5])
    evaluation = {**report([1]), "policy_digest": candidate["policy_digest"]}
    queued = await service.queue("tenant_a", candidate["id"], baseline, evaluation)
    assert queued["status"] == "release_pending"
    assert runtime.policy.digest != candidate["policy_digest"]
    assert await service.mine("other_tenant") == []


@pytest.mark.asyncio
async def test_rule_failures_cannot_be_overridden_by_judges():
    case = EvaluationCase(id="wrong_tool", category="standard", turns=["物流"],
                          expected_tools=["query_logistics"], expected_status="completed")
    async def run(case):
        return [{"status": "completed", "events": [], "iterations": 0}]
    judges = [type("Judge", (), {"model_name": "judge_a", "call": AsyncMock()})(),
              type("Judge", (), {"model_name": "judge_b", "call": AsyncMock()})()]
    result = await evaluate([case], run, judges=judges)
    assert result["pass_rate"] == 0
    assert all(j.call.await_count == 0 for j in judges)


@pytest.mark.asyncio
async def test_native_http_uses_function_call_protocol(store, monkeypatch):
    from app.services.agent.llm import NativeToolClient
    from app.services.agent.contracts import ARGUMENT_MODELS, function_schema
    monkeypatch.setattr(model_service, "llm_api_key", "fixture")
    original = httpx.AsyncClient
    def handle(request):
        body = json.loads(request.content)
        assert body["tools"][0]["function"]["name"] == "query_orders"
        assert body["tool_choice"]["function"]["name"] == "query_orders"
        assert "customer_id" not in body["tools"][0]["function"]["parameters"]["properties"]
        return httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"id": "call_1", "type": "function",
            "function": {"name": "query_orders", "arguments": "{}"}}]}}], "usage": {"total_tokens": 7}})
    monkeypatch.setattr("app.services.agent.llm.httpx.AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    result = await NativeToolClient().call([{"role": "user", "content": "我的订单"}],
        [function_schema("query_orders", "查询订单", ARGUMENT_MODELS["query_orders"])], force="query_orders")
    assert result["arguments"] == {}
    assert result["usage"]["total_tokens"] == 7


@pytest.mark.asyncio
async def test_handoff_cancels_pending_approval(store):
    runtime = AgentRuntime(store)
    await runtime.ainvoke(state(REFUND))
    await runtime.cancel(identity())
    result = await runtime.ainvoke(state("确认"))
    assert result["observations"] == []
    assert "暂无" in result["final_content"]


@pytest.mark.asyncio
async def test_expired_approval_is_rejected(store, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MEMORY_TTL_SECONDS", -1)
    runtime = AgentRuntime(store)
    await runtime.ainvoke(state(REFUND))
    result = await runtime.ainvoke(state("确认"))
    assert result["status"] == "cancelled"
    assert "过期" in result["final_content"]
    assert result["observations"] == []


@pytest.mark.asyncio
async def test_redis_outage_preserves_sql_recovery(store):
    store.redis_url = "redis://fixture"
    redis = AsyncMock()
    redis.get.side_effect = ConnectionError("redis offline")
    redis.set.side_effect = ConnectionError("redis offline")
    store._redis = redis
    await store.put("hot-memory", {"fact": "durable"}, ttl=60, cached=True)
    assert await store.get("hot-memory", cached=True) == {"fact": "durable"}


@pytest.mark.asyncio
async def test_tenant_prefix_isolation_for_failure_mining(store):
    await store.put(tenant_key("badtrace", "tenant:a", "trace"), {"trace_id": "trace"})
    assert await EvolutionService(store).mine("tenant") == []
    assert len(await EvolutionService(store).mine("tenant:a")) == 1
