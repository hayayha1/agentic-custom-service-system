import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app, seed_demo_data
from app.db.session import init_db


@pytest_asyncio.fixture
async def client():
    await init_db()
    await seed_demo_data()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as connection:
        yield connection


USER = {"X-User-Role": "user", "X-User-Id": "user_001"}
ADMIN = {"X-User-Role": "tenant_admin", "X-User-Id": "admin_tenant"}


@pytest.mark.asyncio
async def test_login_token_carries_stable_customer_identity(client):
    login = (await client.post("/api/v1/auth/login", json={"username": "end_user", "password": "user123"})).json()
    me = (await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + login["token"]})).json()
    assert me["user_id"] == login["user_id"]


@pytest.mark.asyncio
async def test_customer_impersonation_and_cross_tenant_session_denied(client):
    wrong = await client.post("/api/v1/chat/sessions", headers=USER, json={"customer_id": "user_002", "customer_name": "其他人"})
    assert wrong.status_code == 403
    created = await client.post("/api/v1/chat/sessions", headers=USER, json={
        "customer_id": "user_001", "customer_name": "测试", "force_new": True})
    session = created.json()["id"]
    query = {"customer_id": "user_001", "session_id": session, "query": "查一下我的订单"}
    wrong = await client.post("/api/v1/chat", headers={**USER, "X-Tenant-Id": "other_tenant"}, json=query)
    assert wrong.status_code == 403
    wrong = await client.post("/api/v1/chat", headers=USER, json={**query, "customer_id": "user_002"})
    assert wrong.status_code == 403


@pytest.mark.asyncio
async def test_trace_access_is_scoped_and_redacted(client):
    created = await client.post("/api/v1/chat/sessions", headers=USER, json={
        "customer_id": "user_001", "customer_name": "测试", "force_new": True})
    response = await client.post("/api/v1/chat", headers=USER, json={
        "customer_id": "user_001", "session_id": created.json()["id"], "query": "查一下我的订单"})
    trace_id = response.json()["agent_trace_id"]
    assert trace_id
    assert (await client.get("/api/v1/agent/traces/" + trace_id, headers=USER)).status_code == 403
    assert (await client.get("/api/v1/agent/traces/" + trace_id, headers=ADMIN)).status_code == 200
    assert (await client.get("/api/v1/agent/traces/" + trace_id, headers={**ADMIN, "X-Tenant-Id": "other"})).status_code == 404
    assert (await client.get("/api/v1/agent/metrics", headers=USER)).status_code == 403
    assert "agent_events_total" in (await client.get("/api/v1/agent/metrics", headers={"X-User-Role": "platform_admin"})).text


@pytest.mark.asyncio
async def test_old_approval_card_cannot_authorize_current_operation(client):
    created = await client.post("/api/v1/chat/sessions", headers=USER, json={
        "customer_id": "user_001", "customer_name": "测试", "force_new": True})
    request = {"customer_id": "user_001", "session_id": created.json()["id"]}
    pending = await client.post("/api/v1/chat", headers=USER, json={**request,
        "query": "订单 ORD-20261025-8891 申请退款，原因是拍错了"})
    approval = pending.json()["business_data"]["approval_id"]
    stale = await client.post("/api/v1/chat", headers=USER, json={**request, "query": "确认", "approval_id": "old_card"})
    assert stale.status_code == 200
    assert stale.json()["business_data"]["card_type"] == "CONFIRMATION_CARD"
    assert "已失效" in stale.json()["content"]
    cancelled = await client.post("/api/v1/chat", headers=USER, json={**request, "query": "取消", "approval_id": approval})
    assert cancelled.status_code == 200
    assert "已安全取消" in cancelled.json()["content"]
