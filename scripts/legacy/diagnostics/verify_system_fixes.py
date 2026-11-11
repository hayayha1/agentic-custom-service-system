import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8001"

async def test_all():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("====== 1. 验证用户登录与角色鉴权 ======")
        # 1.1 admin 登录
        res_admin = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert res_admin.status_code == 200, f"Admin login failed: {res_admin.text}"
        admin_data = res_admin.json()
        print("Admin 登录成功:", admin_data["role"], admin_data["display_name"])

        # 1.2 tech_agent 登录
        res_tech = await client.post("/api/v1/auth/login", json={"username": "tech", "password": "tech123"})
        assert res_tech.status_code == 200, f"Tech login failed: {res_tech.text}"
        tech_data = res_tech.json()
        print("Tech 登录成功:", tech_data["role"], tech_data["display_name"], "负责产品:", tech_data["product_code"])

        # 1.3 user 登录
        res_user = await client.post("/api/v1/auth/login", json={"username": "user", "password": "user123"})
        assert res_user.status_code == 200, f"User login failed: {res_user.text}"
        user_data = res_user.json()
        print("User 登录成功:", user_data["role"], user_data["display_name"])

        print("\n====== 2. 验证知识库列表与数据权限隔离（图一修复） ======")
        # 2.1 admin 查询知识库列表（可查全部）
        res_admin_kbs = await client.get("/api/v1/kbs", headers={"X-User-Role": "admin", "X-User-Id": "admin_master"})
        assert res_admin_kbs.status_code == 200, f"Admin get kbs failed: {res_admin_kbs.text}"
        admin_kbs = res_admin_kbs.json()
        print(f"Admin 查到知识库数量: {len(admin_kbs)}，名称示例: {[k['name'] for k in admin_kbs]}")

        # 2.2 tech_agent 查询知识库（仅所属产品，且必须返回真实 name，杜绝 '知识库 · 39746cba'）
        res_tech_kbs = await client.get("/api/v1/kbs", headers={
            "X-User-Role": "tech_agent", 
            "X-User-Id": "agent_1028",
            "X-User-Product": "SAAS_CLOUD"
        })
        assert res_tech_kbs.status_code == 200, f"Tech get kbs failed: {res_tech_kbs.text}"
        tech_kbs = res_tech_kbs.json()
        print(f"Tech 查到知识库数量: {len(tech_kbs)}")
        for k in tech_kbs:
            assert k["product_code"] == "SAAS_CLOUD", f"越权发现非SAAS产品: {k['product_code']}"
            assert not k["name"].startswith("知识库 · "), f"图一bug复现: 知识库名称异常: {k['name']}"
            print(f"  - 真实知识库名称: {k['name']}, ID: {k['id']}, 产品: {k['product_code']}")

        target_kb_id = tech_kbs[0]["id"] if tech_kbs else admin_kbs[0]["id"]

        print("\n====== 3. 验证知识文档审核流（客服提交 PENDING_REVIEW -> 超管审核通过 ACTIVE） ======")
        # 3.1 技术客服提交文档
        doc_payload = {
            "kb_id": target_kb_id,
            "name": "自动化测试审核文档.md",
            "doc_type": "MD",
            "content": "# 测试审核标题\n这是技术客服专员提交的待审核业务规则内容。",
            "priority": 3,
            "created_by": "agent_1028"
        }
        res_create = await client.post("/api/v1/documents", json=doc_payload, headers={
            "X-User-Role": "tech_agent",
            "X-User-Id": "agent_1028",
            "X-User-Product": "SAAS_CLOUD"
        })
        assert res_create.status_code == 200, f"Create doc failed: {res_create.text}"
        created_doc = res_create.json()
        assert created_doc["status"] == "PENDING_REVIEW", f"客服提交状态应为 PENDING_REVIEW，实际为: {created_doc['status']}"
        print(f"技术客服提交文档成功，文档ID: {created_doc['id']}, 当前审核状态: {created_doc['status']}")

        # 3.2 验证待审核期间不应生成检索切片
        res_chunks_before = await client.get(f"/api/v1/chunks?doc_id={created_doc['id']}")
        assert res_chunks_before.status_code == 200
        before_count = res_chunks_before.json().get("total", 0)
        assert before_count == 0, f"待审核期间不应有切片，实际切片数: {before_count}"
        print("已验证：待审核状态下切片未入库，不影响生产检索！")

        # 3.3 超级管理员审核通过
        res_approve = await client.post(f"/api/v1/documents/{created_doc['id']}/approve", headers={
            "X-User-Role": "admin",
            "X-User-Id": "admin_master"
        })
        assert res_approve.status_code == 200, f"Approve failed: {res_approve.text}"
        approve_data = res_approve.json()
        assert approve_data["status"] == "ACTIVE"
        print(f"超管审核通过！返回: {approve_data['message']}, 生成切片数: {approve_data['chunk_count']}")

        # 3.4 验证审核通过后切片生成并入库
        res_chunks_after = await client.get(f"/api/v1/chunks?doc_id={created_doc['id']}")
        after_count = res_chunks_after.json().get("total", 0)
        assert after_count > 0, f"审核通过后应生成切片，实际: {after_count}"
        print(f"已验证：审核通过后切片成功入库，生成切片数: {after_count}")

        print("\n====== 4. 验证会话隔离、人工客服分配与挂断/二次转人工 ======")
        # 4.1 普通用户进入/登录创建新会话（force_new=True）
        res_sess = await client.post("/api/v1/chat/sessions", json={
            "customer_id": "test_user_999",
            "customer_name": "测试客户999",
            "product_code": "SAAS_CLOUD",
            "force_new": True
        })
        assert res_sess.status_code == 200
        user_sess = res_sess.json()
        print(f"普通用户成功开启新会话: {user_sess['id']}, 状态: {user_sess['status']}")

        # 4.2 用户发起转人工客服（自动路由产品对应客服）
        res_transfer = await client.post("/api/v1/chat/transfer-human", json={
            "session_id": user_sess["id"],
            "customer_id": "test_user_999"
        })
        assert res_transfer.status_code == 200
        transfer_data = res_transfer.json()
        assert transfer_data["status"] == "HUMAN_CONNECTED"
        assert transfer_data["agent"] == "agent_1028", f"SAAS_CLOUD 应分配给 agent_1028，实际: {transfer_data['agent']}"
        print(f"成功转接专属人工客服: {transfer_data['agent']}，会话状态: {transfer_data['status']}")

        # 4.3 验证技术客服只能看到分配给自己的会话
        res_agent_sessions = await client.get("/api/v1/chat/sessions", headers={
            "X-User-Role": "tech_agent",
            "X-User-Id": "agent_1028",
            "X-User-Product": "SAAS_CLOUD"
        })
        assert res_agent_sessions.status_code == 200
        agent_sessions = res_agent_sessions.json()
        my_session_ids = [s["id"] for s in agent_sessions]
        assert user_sess["id"] in my_session_ids, "agent_1028 应能看到分配给自己的客户会话"
        print(f"技术客服 agent_1028 成功感知到新分配的客户会话 (待接待会话数: {len(agent_sessions)})")

        # 4.4 验证其他技术客服看不到此会话
        res_other_sessions = await client.get("/api/v1/chat/sessions", headers={
            "X-User-Role": "tech_agent",
            "X-User-Id": "agent_1029",
            "X-User-Product": "E_COMMERCE"
        })
        assert res_other_sessions.status_code == 200
        other_ids = [s["id"] for s in res_other_sessions.json()]
        assert user_sess["id"] not in other_ids, "agent_1029 不应看到未分配给自己的 SAAS 客户"
        print("已验证：技术客服之间数据严格隔离！")

        # 4.5 用户主动挂断人工客服
        res_hangup = await client.post(f"/api/v1/chat/hangup?session_id={user_sess['id']}")
        assert res_hangup.status_code == 200
        hangup_data = res_hangup.json()
        assert hangup_data["status"] == "AI_SERVICE"
        print("用户主动挂断成功，已切回 AI 服务")

        # 4.6 挂断后用户再次提问，验证回答中常驻转人工按钮（支持二次转人工）
        res_ask = await client.post("/api/v1/chat", json={
            "product_code": "SAAS_CLOUD",
            "customer_id": "test_user_999",
            "session_id": user_sess["id"],
            "query": "你们的SaaS服务怎么收费？"
        }, headers={"X-User-Role": "user", "X-User-Id": "test_user_999"})
        assert res_ask.status_code == 200
        ask_data = res_ask.json()
        actions = [a["action"] for a in ask_data.get("action_buttons", [])]
        assert "TRANSFER_TO_HUMAN" in actions, "挂断后新提问中必须常驻 TRANSFER_TO_HUMAN 按钮"
        print("已验证：挂断后再次提问常驻转人工选项，用户可顺利二次进入人工！")

        # 4.7 验证第二次转人工
        res_transfer_again = await client.post("/api/v1/chat/transfer-human", json={
            "session_id": user_sess["id"],
            "customer_id": "test_user_999"
        })
        assert res_transfer_again.status_code == 200
        assert res_transfer_again.json()["status"] == "HUMAN_CONNECTED"
        print("已验证：成功完成二次转人工流程！")

        # 4.8 清理测试数据
        await client.delete(f"/api/v1/documents/{created_doc['id']}", headers={"X-User-Role": "admin"})
        print("\nAll verification checks passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_all())
