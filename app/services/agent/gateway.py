"""The only workflow entry to business handlers, including composite and resumed tasks."""
import asyncio
import time
from decimal import Decimal, InvalidOperation

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.services.agent.contracts import ARGUMENT_MODELS, Observation
from app.services.agent.storage import agent_store, scope_key, SessionBusy
from app.services.agent.tools import action_tool_center
from app.services.business_service import business_service


class ToolGateway:
    def __init__(self, store=agent_store, center=action_tool_center):
        self.store, self.center = store, center

    def validate(self, name, arguments):
        if name not in ARGUMENT_MODELS or name == "knowledge_retriever":
            raise ValueError("未知业务工具")
        return ARGUMENT_MODELS[name].model_validate(arguments).model_dump(exclude_none=True)

    async def execute(self, name, arguments, identity, operation_id, *, approved=False):
        tool = self.center.get_tool(name)
        if not tool or not identity.can_act():
            return Observation(status="denied", tool_name=name, message="当前身份无权办理该业务。")
        try:
            params = self.validate(name, arguments)
        except (ValidationError, ValueError) as exc:
            errors = exc.errors(include_input=False) if isinstance(exc, ValidationError) else []
            return Observation(status="validation_error", tool_name=name, message="请补全或更正业务参数。",
                               data={"errors": [{"field": str(e["loc"][0]), "type": e["type"]} for e in errors]})

        # The demo ERP has no tenant column. Copy it into a tenant/customer-scoped
        # adapter before use; never share mutable customer records across tenants.
        # All tools touching one customer's simulated ERP share a lease. This
        # also serializes mutations made from different sessions or tool types.
        guard_key = "gateway:" + scope_key(identity.tenant_id, identity.customer_id)
        try:
            async with self.store.lock(guard_key):
                backend_customer = await self._backend_customer(identity)
                return await self._authorized_call(name, params, identity, backend_customer, operation_id, tool, approved)
        except SessionBusy:
            return Observation(status="unavailable", tool_name=name, message="该业务正在处理中，请稍后重试。", retryable=True)

    async def _authorized_call(self, name, params, identity, backend_customer, operation_id, tool, approved):
        orders = await business_service.get_customer_orders(backend_customer)
        order = None
        if params.get("order_id"):
            order = next((o for o in orders if o["order_id"].lower() == params["order_id"].lower()), None)
            if not order:
                return Observation(status="denied", tool_name=name, message="未在当前客户名下找到该订单，请核对订单号。")
        if name == "apply_refund" and params.get("refund_amount") is not None:
            try:
                total = Decimal(str(order["amount"]).replace("¥", "").replace("￥", "").replace(",", ""))
                if Decimal(str(params["refund_amount"])) > total:
                    raise ValueError("超出订单金额")
            except (InvalidOperation, ValueError, KeyError):
                return Observation(status="validation_error", tool_name=name, message="退款金额超出订单金额或订单金额无法核验。")
        if name == "cancel_unpaid_order" and order.get("status") != "UNPAID":
            return Observation(status="failed", tool_name=name, message="仅支持取消未支付订单；已支付订单请申请售后。")
        if tool.action_type == "WRITE" and tool.risk_level in {"HIGH", "MEDIUM"} and not approved:
            return Observation(status="approval_required", tool_name=name, message="该操作需要再次确认。", data=params)

        return await self._protected_call(name, params, identity, backend_customer, operation_id, tool)

    async def _backend_customer(self, identity):
        """Persist the demo ERP state; production adapters must pass tenant_id upstream."""
        import copy
        backend_id = "agent-" + scope_key(identity.tenant_id, identity.customer_id)
        key = "business:" + backend_id
        data = await self.store.get(key)
        if data is None:
            data = copy.deepcopy(await business_service.get_customer_orders(identity.customer_id))
            await self.store.put(key, data)
        business_service.orders[backend_id] = data
        return backend_id

    async def _protected_call(self, name, params, identity, backend_customer, operation_id, tool):
        import json
        op_key = "operation:" + scope_key(identity.tenant_id, identity.customer_id, identity.session_id, operation_id)
        fingerprint = scope_key(name, json.dumps(params, sort_keys=True, ensure_ascii=False))
        if tool.action_type == "WRITE":
            previous = await self.store.get(op_key)
            if previous:
                if previous.get("fingerprint") != fingerprint:
                    return Observation(status="denied", tool_name=name, message="重复提交的业务参数不一致，请核实待办操作。")
                if previous.get("result"):
                    return Observation.model_validate(previous["result"])
                return Observation(status="uncertain", tool_name=name, message="该操作已受理，结果待核实，请勿重复提交，可联系人工确认。")
        now = time.time()
        health_key = "health:" + scope_key(identity.tenant_id, name)
        health = await self.store.get(health_key, {})
        if health.get("open_until", 0) > now:
            return Observation(status="unavailable", tool_name=name, message="业务系统暂时不可用，请稍后重试。",
                               data={"reason": "circuit_open"}, retryable=True)
        rate_key = "rate:" + scope_key(identity.tenant_id, identity.customer_id, name, str(int(now // 60)))
        rate = await self.store.get(rate_key, {"count": 0})
        if tool.action_type == "WRITE" and rate["count"] >= settings.AGENT_TOOL_RATE_LIMIT:
            return Observation(status="unavailable", tool_name=name, message="操作过于频繁，请稍后重试。", data={"reason": "rate_limit"})
        rate["count"] += 1
        await self.store.put(rate_key, rate, ttl=120)

        if tool.action_type == "WRITE":
            if not await self.store.reserve(op_key, {"status": "started", "tool": name, "fingerprint": fingerprint}):
                return Observation(status="uncertain", tool_name=name, message="该操作正在受理，请勿重复提交。")

        # Read retries are safe. A write can only retry explicit pre-acceptance
        # failures; ambiguous timeouts must never repeat a financial side effect.
        for attempt in range(settings.AGENT_TOOL_RETRIES + 1):
            try:
                async with asyncio.timeout(settings.AGENT_TOOL_TIMEOUT_SECONDS):
                    result = await self.center.handlers[name](customer_id=backend_customer, **params)
                observation = Observation(status="success" if result.success else "failed", tool_name=name,
                                          message=result.message, data=result.data or {}, card_data=result.card_data)
                await self.store.update_json(health_key, lambda _: {"failures": 0})
                if tool.action_type == "WRITE":
                    await self.store.put("business:" + backend_customer, business_service.orders[backend_customer])
                    await self.store.put(op_key, {"result": observation.model_dump(), "fingerprint": fingerprint})
                return observation
            except (httpx.TransportError, httpx.HTTPStatusError, TimeoutError, ConnectionError) as exc:
                transient = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code >= 500
                if not transient:
                    return Observation(status="failed", tool_name=name, message="业务请求未通过校验，请核对后重试。")
                def failure(previous):
                    updated = {**previous, "failures": previous.get("failures", 0) + 1}
                    if updated["failures"] >= settings.AGENT_CIRCUIT_THRESHOLD:
                        updated["open_until"] = time.time() + settings.AGENT_CIRCUIT_RESET_SECONDS
                    return updated
                health = await self.store.update_json(health_key, failure, default={})
                if tool.action_type == "WRITE":
                    return Observation(status="uncertain", tool_name=name, message="业务系统响应中断，结果待核实，请联系人工，避免重复操作。")
                if attempt >= settings.AGENT_TOOL_RETRIES or health.get("open_until", 0) > time.time():
                    break
                await asyncio.sleep(0.1 * 2 ** attempt)
            except Exception:
                return Observation(status="uncertain" if tool.action_type == "WRITE" else "failed", tool_name=name,
                                   message="业务处理异常，请联系人工客服核实。")
        return Observation(status="unavailable", tool_name=name, message="业务系统暂时不可用，已停止重试，请稍后再试。", retryable=True)


tool_gateway = ToolGateway()
