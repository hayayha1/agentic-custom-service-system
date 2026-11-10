import pytest
import pytest_asyncio
import io
from httpx import AsyncClient, ASGITransport
from app.main import app, seed_demo_data
from app.db.session import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    await init_db()
    await seed_demo_data()

@pytest.mark.asyncio
async def test_health_and_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_rbac_permissions_isolation():
    """测试三种角色（普通用户、技术客服、超级管理员）的严格权限区分"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. 普通用户 (user) 权限测试
        user_headers = {"X-User-Role": "user", "X-User-Id": "user_001"}
        
        # 1.1 普通用户越权访问知识库管理 -> 必须 403
        res = await ac.get("/api/v1/kbs", headers=user_headers)
        assert res.status_code == 403

        # 1.2 普通用户越权访问知识片段管理 -> 必须 403
        res = await ac.get("/api/v1/documents", headers=user_headers)
        assert res.status_code == 403

        # 1.3 普通用户查询会话列表 -> 只能看到本人的行级数据
        res = await ac.get("/api/v1/chat/sessions", headers=user_headers)
        assert res.status_code == 200
        user_sessions = res.json()
        assert all(s["customer_id"] == "user_001" for s in user_sessions)

        # 1.4 普通用户越权关闭人工座席 -> 必须 403
        res = await ac.post("/api/v1/chat/finish-human?session_id=any", headers=user_headers)
        assert res.status_code == 403

        # 2. 技术客服 (tech_agent) 权限测试
        agent_headers = {"X-User-Role": "tech_agent", "X-User-Id": "agent_1028"}

        # 2.1 技术客服越权修改知识库配置 -> 必须 403
        res = await ac.get("/api/v1/kbs", headers=agent_headers)
        assert res.status_code == 403

        # 2.2 技术客服访问知识片段管理与切片 -> 允许 200
        res = await ac.get("/api/v1/documents", headers=agent_headers)
        assert res.status_code == 200

        res = await ac.get("/api/v1/chunks", headers=agent_headers)
        assert res.status_code == 200

        # 2.3 技术客服查看全局进线客户会话 -> 允许 200 (看到所有会话)
        res = await ac.get("/api/v1/chat/sessions", headers=agent_headers)
        assert res.status_code == 200

        # 3. 超级管理员 (admin) 权限测试
        admin_headers = {"X-User-Role": "admin", "X-User-Id": "admin_01"}

        # 3.1 超管访问知识库 -> 允许 200
        res = await ac.get("/api/v1/kbs", headers=admin_headers)
        assert res.status_code == 200

        # 3.2 超管访问文档与切片 -> 允许 200
        res = await ac.get("/api/v1/documents", headers=admin_headers)
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_knowledge_base_lifecycle():
    transport = ASGITransport(app=app)
    admin_headers = {"X-User-Role": "admin"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        kb_payload = {
            "product_code": "TEST_PROD",
            "name": "测试专用知识库",
            "description": "自动化测试知识库",
            "config": {
                "bm25_top_k": 10,
                "vector_top_k": 10,
                "rerank_top_k": 2,
                "threshold_direct": 0.80,
                "threshold_clarify": 0.50
            }
        }
        res = await ac.post("/api/v1/kbs", json=kb_payload, headers=admin_headers)
        assert res.status_code == 200
        kb_data = res.json()
        kb_id = kb_data["id"]

        res = await ac.get(f"/api/v1/kbs/{kb_id}", headers=admin_headers)
        assert res.status_code == 200

        # 知识库状态切换 (启用/停用) 与更新人测试
        res = await ac.put(f"/api/v1/kbs/{kb_id}", json={
            "description": "更新后的描述",
            "status": "INACTIVE",
            "updated_by": "tech_lead",
            "config": {"threshold_direct": 0.85}
        }, headers=admin_headers)
        assert res.status_code == 200
        updated_kb = res.json()
        assert updated_kb["status"] == "INACTIVE"
        assert updated_kb["updated_by"] == "tech_lead"

        res = await ac.delete(f"/api/v1/kbs/{kb_id}", headers=admin_headers)
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_document_and_version_rollback():
    transport = ASGITransport(app=app)
    admin_headers = {"X-User-Role": "admin"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/kbs", headers=admin_headers)
        kbs = res.json()
        target_kb = kbs[0]
        kb_id = target_kb["id"]

        doc_payload = {
            "kb_id": kb_id,
            "name": "自动化测试手册.md",
            "doc_type": "MD",
            "priority": 3,
            "content": "# 测试章节一\n这是测试的第一段正文内容。\n## 测试子章节\n这是测试子章节的内容。"
        }
        res = await ac.post("/api/v1/documents", json=doc_payload, headers=admin_headers)
        assert res.status_code == 200
        doc_data = res.json()
        doc_id = doc_data["id"]
        assert doc_data["content"] == doc_payload["content"]
        assert doc_data["priority"] == 3

        # 测试按优先级查询
        res = await ac.get(f"/api/v1/documents?priority=3", headers=admin_headers)
        assert res.status_code == 200
        docs_with_p3 = res.json()
        assert any(d["id"] == doc_id for d in docs_with_p3)

        # 编辑文档正文并验证更新人
        res = await ac.put(f"/api/v1/documents/{doc_id}", json={
            "content": "# 测试章节一 (修改版)\n这是版本二的修改内容。",
            "updated_by": "agent_1028"
        }, headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["version"] == 2
        assert res.json()["updated_by"] == "agent_1028"
        assert res.json()["content"] == "# 测试章节一 (修改版)\n这是版本二的修改内容。"

        # 检查历史版本快照
        res = await ac.get(f"/api/v1/documents/{doc_id}/versions", headers=admin_headers)
        assert res.status_code == 200
        versions = res.json()
        assert len(versions) >= 1
        # 确认保存的旧版本是第一版的内容
        v1_snapshot = next(v for v in versions if v["version"] == 1)
        assert v1_snapshot["content"] == doc_payload["content"]

        # 回滚到指定版本 1 并记录回滚人
        res = await ac.post(f"/api/v1/documents/{doc_id}/rollback?target_version=1&updated_by=admin_audit", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["version"] == 3
        assert res.json()["content"] == doc_payload["content"]
        assert res.json()["updated_by"] == "admin_audit"

        res = await ac.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_faq_batch_import_and_chunks():
    transport = ASGITransport(app=app)
    agent_headers = {"X-User-Role": "tech_agent"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 通过超管获取 kb_id
        admin_res = await ac.get("/api/v1/kbs", headers={"X-User-Role": "admin"})
        kb_id = admin_res.json()[0]["id"]

        batch_payload = {
            "kb_id": kb_id,
            "document_name": "API自动化批量FAQ",
            "items": [
                {
                    "standard_question": "怎么开通企业专属账号？",
                    "similar_questions": ["企业账号注册流程", "如何申请企业认证"],
                    "answer": "请前往【企业认证中心】上传营业执照彩色扫描件，平台将在 2 个小时内完成审核。",
                    "priority": 5
                }
            ]
        }
        # 技术客服进行批量导入 FAQ
        res = await ac.post("/api/v1/documents/faq/batch", json=batch_payload, headers=agent_headers)
        assert res.status_code == 200

        # 技术客服检索切片
        res = await ac.get(f"/api/v1/chunks?kb_id={kb_id}&keyword=企业认证中心", headers=agent_headers)
        assert res.status_code == 200
        assert res.json()["total"] >= 1

@pytest.mark.asyncio
async def test_chat_sessions_and_human_escalation():
    transport = ASGITransport(app=app)
    admin_headers = {"X-User-Role": "admin"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/chat/sessions", headers=admin_headers)
        assert res.status_code == 200
        sessions = res.json()
        assert len(sessions) >= 1
        current_sess = sessions[0]
        sess_id = current_sess["id"]

        # 发起用户对话
        res = await ac.post("/api/v1/chat", json={
            "product_code": "SAAS_CLOUD",
            "customer_id": current_sess["customer_id"],
            "session_id": sess_id,
            "query": "怎么办理产品退款？"
        })
        assert res.status_code == 200

        # 转人工
        res = await ac.post("/api/v1/chat/transfer-human", json={
            "session_id": sess_id,
            "customer_id": current_sess["customer_id"]
        })
        assert res.status_code == 200

        # 技术客服结束人工服务
        agent_headers = {"X-User-Role": "tech_agent"}
        res = await ac.post(f"/api/v1/chat/finish-human?session_id={sess_id}", headers=agent_headers)
        assert res.status_code == 200
        assert res.json()["status"] == "AI_SERVICE"

@pytest.mark.asyncio
async def test_transaction_business_cards():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/chat", json={
            "product_code": "SAAS_CLOUD",
            "customer_id": "user_001",
            "query": "查一下我的订单物流到哪了"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["reply_type"] == "TRANSACTION"
        assert data["business_data"] is not None

@pytest.mark.asyncio
async def test_file_upload_and_chunking():
    transport = ASGITransport(app=app)
    agent_headers = {"X-User-Role": "tech_agent"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_res = await ac.get("/api/v1/kbs", headers={"X-User-Role": "admin"})
        kb_id = admin_res.json()[0]["id"]

        dummy_md = "# 业务文件直传测试\n这是通过 Multipart 上传的文档正文内容。"
        files = {"file": ("test_upload.md", io.BytesIO(dummy_md.encode("utf-8")), "text/markdown")}
        data = {"kb_id": kb_id, "priority": "4", "created_by": "tester"}

        # 技术客服上传文档
        res = await ac.post("/api/v1/documents/upload", data=data, files=files, headers=agent_headers)
        assert res.status_code == 200
        doc_info = res.json()
        assert doc_info["name"] == "test_upload.md"

@pytest.mark.asyncio
async def test_auth_login_and_agent_chat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 超管登录
        res = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200
        assert res.json()["role"] == "admin"

        # 2. 技术客服登录
        res = await ac.post("/api/v1/auth/login", json={"username": "tech", "password": "tech123"})
        assert res.status_code == 200
        assert res.json()["role"] == "tech_agent"

        # 3. 普通客户登录
        res = await ac.post("/api/v1/auth/login", json={"username": "user", "password": "user123"})
        assert res.status_code == 200
        assert res.json()["role"] == "user"

        # 4. 错误密码拦截
        res = await ac.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword"})
        assert res.status_code == 401

        # 5. 技术客服向普通客户会话发送消息
        # 5.1 客户建立会话
        cust_headers = {"X-User-Role": "user", "X-User-Id": "cust_888"}
        res = await ac.post("/api/v1/chat/sessions", json={
            "customer_id": "cust_888",
            "customer_name": "测试客户小王",
            "product_code": "SAAS_CLOUD"
        }, headers=cust_headers)
        assert res.status_code == 200
        session_id = res.json()["id"]

        # 5.2 客服发消息
        transfer = await ac.post("/api/v1/chat/transfer-human", json={
            "session_id": session_id, "customer_id": "cust_888"
        }, headers=cust_headers)
        assert transfer.status_code == 200
        agent_headers = {"X-User-Role": "tech_agent", "X-User-Id": "agent_1028"}
        res = await ac.post("/api/v1/chat", json={
            "session_id": session_id,
            "customer_id": "cust_888",
            "product_code": "SAAS_CLOUD",
            "query": "您好小王，我是技术专员，已为您处理好账号问题。"
        }, headers=agent_headers)
        assert res.status_code == 200
        assert res.json()["reply_type"] == "HUMAN_AGENT"

        # 5.3 客户拉取会话历史消息流，验证客服发的消息能够被客户拉取到
        res = await ac.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=cust_headers)
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) >= 1
        agent_msg = next((m for m in msgs if m["role"] == "human_agent" and "已为您处理好账号问题" in m["content"]), None)
        assert agent_msg is not None
        assert "已为您处理好账号问题" in agent_msg["content"]

@pytest.mark.asyncio
async def test_user_profile_rbac_and_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. 普通客户访问客户画像 -> 403 Forbidden
        user_headers = {"X-User-Role": "user", "X-User-Id": "user_001"}
        res = await ac.get("/api/v1/chat/user-profile", headers=user_headers)
        assert res.status_code == 403

        # 2. 技术客服访问客户画像 -> 200 OK 且包含完整指标
        tech_headers = {"X-User-Role": "tech_agent", "X-User-Id": "agent_1028"}
        res = await ac.get("/api/v1/chat/user-profile?customer_id=U10086", headers=tech_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == "U10086"
        assert data["name"] == "张先生"
        assert data["phone"] == "138****5678"
        assert data["channel"] == "微信小程序"
        assert data["vip_level"] == "企业VIP"
        assert data["recent_order"]["order_id"] == "ORD_20261025"
        assert data["recent_order"]["product"] == "智能语音盒"
        assert data["recent_order"]["status"] == "已发货"
        assert data["pending_issue"] == "昨日反馈设备无法连接WiFi，等待固件更新"
        assert "技术小白" in data["tags"]
        assert "急躁型" in data["tags"]

        # 3. 超管访问客户画像 -> 200 OK
        admin_headers = {"X-User-Role": "admin", "X-User-Id": "admin_master"}
        res = await ac.get("/api/v1/chat/user-profile", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["user_id"] == "U10086"

        # 4. 技术客服动态更新标签
        res = await ac.put("/api/v1/chat/user-profile?customer_id=U10086", json={
            "tags": ["技术小白", "急躁型", "已电话回访"]
        }, headers=tech_headers)
        assert res.status_code == 200
        assert "已电话回访" in res.json()["tags"]
