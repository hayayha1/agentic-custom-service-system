import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_business_chain_same_tenant_group():
    """
    验证全链路业务闭环（同一租户 tenant_default 与同一分组 SAAS_CLOUD）：
    1. 终端用户 (end_user) 登录进线，智能答疑检索
    2. 转接人工客服，技术坐席 (service_agent) 接单接待
    3. 技术坐席提交新知识草稿
    4. 知识主管 (knowledge_master) 审核并发布知识文档入库
    5. 企业超管 (tenant_admin) 配置双模型、产品线与坐席人员
    6. 平台超管 (platform_admin) 查看履约账单台账、调整弹性配额与生命周期状态
    """
    # ----------------------------------------------------
    # Step 1: 终端用户登录
    # ----------------------------------------------------
    user_login = client.post("/api/v1/auth/login", json={"username": "end_user", "password": "user123"})
    assert user_login.status_code == 200, user_login.text
    user_data = user_login.json()
    assert user_data["tenant_id"] == "tenant_default"
    assert user_data["product_code"] == "SAAS_CLOUD"
    assert user_data["group_name"] == "云创云服务客服组"
    user_token = user_data["token"]
    customer_id = user_data["user_id"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 用户进线创建会话
    create_session = client.post("/api/v1/chat/sessions", json={
        "product_code": "SAAS_CLOUD",
        "customer_id": customer_id,
        "customer_name": "张先生"
    }, headers=user_headers)
    assert create_session.status_code == 200, create_session.text
    session_id = create_session.json()["id"]

    # 用户智能问答 (调用 LangGraph 与知识库检索)
    bot_msg = client.post("/api/v1/chat", json={
        "product_code": "SAAS_CLOUD",
        "customer_id": customer_id,
        "session_id": session_id,
        "query": "请问SaaS平台支持多租户数据隔离吗？"
    }, headers=user_headers)
    assert bot_msg.status_code == 200, bot_msg.text
    bot_res = bot_msg.json()
    assert bot_res["reply_type"] in ["DIRECT_ANSWER", "RECOMMEND_QUESTIONS", "HUMAN_AGENT", "TRANSACTION", "CHITCHAT", "FALLBACK"]

    # 用户申请转接人工
    transfer_res = client.post("/api/v1/chat/transfer-human", json={
        "session_id": session_id,
        "customer_id": customer_id
    }, headers=user_headers)
    assert transfer_res.status_code == 200, transfer_res.text

    # ----------------------------------------------------
    # Step 2: 技术坐席登录并处理会话
    # ----------------------------------------------------
    agent_login = client.post("/api/v1/auth/login", json={"username": "service_agent", "password": "agent123"})
    assert agent_login.status_code == 200
    agent_data = agent_login.json()
    assert agent_data["tenant_id"] == "tenant_default"
    assert agent_data["product_code"] == "SAAS_CLOUD"
    assert agent_data["group_name"] == "云创云服务客服组"
    agent_token = agent_data["token"]
    agent_headers = {"Authorization": f"Bearer {agent_token}"}

    # 坐席完成接待，结束人工会话
    finish_res = client.post(f"/api/v1/chat/finish-human?session_id={session_id}", headers=agent_headers)
    assert finish_res.status_code == 200, finish_res.text

    # ----------------------------------------------------
    # Step 3: 坐席提报知识库草稿
    # ----------------------------------------------------
    doc_res = client.get("/api/v1/documents", headers=agent_headers)
    assert doc_res.status_code == 200
    docs = doc_res.json()
    kb_id = docs[0]["kb_id"] if docs else "kb_saas_01"

    doc_draft = client.post("/api/v1/documents", json={
        "kb_id": kb_id,
        "name": "SaaS全链路租户隔离与双模型最佳实践.txt",
        "title": "SaaS全链路租户隔离与双模型最佳实践",
        "content": "SaaS客户服务平台采用双模型架构，支持对话LLM与向量Embedding灵活插拔，保障数据合规。",
        "doc_type": "TXT"
    }, headers=agent_headers)
    assert doc_draft.status_code in [200, 201], doc_draft.text
    doc_id = doc_draft.json()["id"]

    # ----------------------------------------------------
    # Step 4: 知识主管登录并终审发布
    # ----------------------------------------------------
    km_login = client.post("/api/v1/auth/login", json={"username": "knowledge_master", "password": "km123"})
    assert km_login.status_code == 200
    km_data = km_login.json()
    assert km_data["tenant_id"] == "tenant_default"
    assert km_data["product_code"] == "SAAS_CLOUD"
    km_headers = {"Authorization": f"Bearer {km_data['token']}"}

    # 知识主管审核通过文档 (POST)
    approve_res = client.post(f"/api/v1/documents/{doc_id}/approve", headers=km_headers)
    assert approve_res.status_code == 200, approve_res.text
    assert approve_res.json()["status"] == "ACTIVE"

    # ----------------------------------------------------
    # Step 5: 企业超管登录并治理双模型、产品线与团队坐席
    # ----------------------------------------------------
    ta_login = client.post("/api/v1/auth/login", json={"username": "tenant_admin", "password": "admin123"})
    assert ta_login.status_code == 200
    ta_data = ta_login.json()
    assert ta_data["tenant_id"] == "tenant_default"
    ta_headers = {"Authorization": f"Bearer {ta_data['token']}"}

    # 5.1 配置双模型
    models_get = client.get("/api/v1/tenants/current/models", headers=ta_headers)
    assert models_get.status_code == 200
    models_cfg = models_get.json()
    models_cfg["llm_config"]["temperature"] = 0.8
    models_put = client.put("/api/v1/tenants/current/models", json={
        "llm_config": models_cfg["llm_config"],
        "embedding_config": models_cfg["embedding_config"]
    }, headers=ta_headers)
    assert models_put.status_code == 200

    # 5.2 连通性测试
    test_llm = client.post("/api/v1/tenants/current/models/test-llm", json={"llm_config": models_cfg["llm_config"]}, headers=ta_headers)
    assert test_llm.status_code == 200
    assert test_llm.json()["success"] is True

    test_emb = client.post("/api/v1/tenants/current/models/test-embedding", json={"embedding_config": models_cfg["embedding_config"]}, headers=ta_headers)
    assert test_emb.status_code == 200
    assert test_emb.json()["success"] is True

    # 5.3 1:N 产品线治理
    pl_res = client.get("/api/v1/tenants/current/product-lines", headers=ta_headers)
    assert pl_res.status_code == 200
    for p in pl_res.json().get("product_lines", []):
        if p["code"] not in ["SAAS_CLOUD", "E_COMMERCE", "FIN_AI"]:
            client.delete(f"/api/v1/tenants/current/product-lines/{p['code']}", headers=ta_headers)

    pl_code = f"IOT_{uuid.uuid4().hex[:6].upper()}"
    new_pl = client.post("/api/v1/tenants/current/product-lines", json={
        "code": pl_code,
        "name": "智能物联网硬件线",
        "description": "IoT硬件固件升级与设备售后"
    }, headers=ta_headers)
    assert new_pl.status_code == 200, new_pl.text

    # 5.4 团队坐席席位管理
    staff_res = client.get("/api/v1/tenants/current/staff", headers=ta_headers)
    assert staff_res.status_code == 200
    for s in staff_res.json().get("staff", []):
        if s.get("username", "").startswith("agent_iot_") or s.get("username", "").startswith("agent_"):
            client.delete(f"/api/v1/tenants/current/staff/{s.get('user_id', s.get('username'))}", headers=ta_headers)

    staff_user = f"agent_{uuid.uuid4().hex[:6]}"
    new_staff = client.post("/api/v1/tenants/current/staff", json={
        "username": staff_user,
        "name": "硬件客服张工",
        "role": "service_agent",
        "product_code": pl_code,
        "password": "pass_agent_01"
    }, headers=ta_headers)
    assert new_staff.status_code == 200, new_staff.text

    # ----------------------------------------------------
    # Step 6: 平台超管登录，查看商业账单、弹性配额与生命周期
    # ----------------------------------------------------
    pa_login = client.post("/api/v1/auth/login", json={"username": "platform_admin", "password": "admin123"})
    assert pa_login.status_code == 200
    pa_headers = {"Authorization": f"Bearer {pa_login.json()['token']}"}

    # 6.1 查看 tenant_default 的商业账务台账
    billing_res = client.get("/api/v1/tenants/tenant_default/billing", headers=pa_headers)
    assert billing_res.status_code == 200
    b_data = billing_res.json()
    assert b_data["tenant_code"] == "tenant_default"
    assert "days_left" in b_data
    assert "total_paid_amount" in b_data

    # 6.2 动态微调非标弹性配额
    elastic_res = client.put("/api/v1/tenants/tenant_default/elastic-quota", json={
        "tenant_code": "tenant_default",
        "max_product_lines": 12,
        "max_kbs": 60,
        "max_seats": 55,
        "max_km_seats": 12,
        "max_docs_per_kb": 25000,
        "monthly_query_quota": 200000,
        "monthly_token_quota": 120000000
    }, headers=pa_headers)
    assert elastic_res.status_code == 200
    assert elastic_res.json()["current_quotas"]["max_product_lines"] == 12

    # 6.3 租户生命周期管控
    status_res = client.put("/api/v1/tenants/tenant_default/status", json={
        "status": "ACTIVE",
        "reason": "正常续约考核通过"
    }, headers=pa_headers)
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "ACTIVE"
