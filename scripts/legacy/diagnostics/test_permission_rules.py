import asyncio
import sys
import httpx

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://127.0.0.1:8001"

async def test_permissions():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        print("\n================== 1. 验证前端 HTML hasMenuPermission 权限定义 =================")
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            html = f.read()

        assert "if (currentRole.value === 'operator') {" in html
        assert "return menuKey === 'chunks' || menuKey === 'badcases';" in html
        assert "if (currentRole.value === 'tech_agent') {" in html
        assert "return menuKey === 'chat' || menuKey === 'chunks';" in html
        print("  [√] 运营权限规约: 严格限定为 chunks (知识文档管理) 与 badcases (badcase池)")
        print("  [√] 客服权限规约: 严格限定为 chat (对话) 与 chunks (知识文档管理)")

        print("\n================== 2. 模拟真实登录获取各角色凭证 =================")
        # 1) 登录超管 admin
        admin_login = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert admin_login.status_code == 200, f"admin login failed: {admin_login.text}"
        admin_token = admin_login.json()["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}", "X-User-Role": "admin"}
        print("  [√] 超级管理员 admin 登录成功")

        # 2) 登录运营 ops
        ops_login = await client.post("/api/v1/auth/login", json={"username": "ops", "password": "ops123"})
        assert ops_login.status_code == 200, f"ops login failed: {ops_login.text}"
        ops_token = ops_login.json()["token"]
        ops_headers = {"Authorization": f"Bearer {ops_token}", "X-User-Role": "operator"}
        print("  [√] 知识运营专员 ops 登录成功")

        # 3) 登录客服 agent
        agent_login = await client.post("/api/v1/auth/login", json={"username": "agent", "password": "agent123"})
        assert agent_login.status_code == 200, f"agent login failed: {agent_login.text}"
        agent_token = agent_login.json()["token"]
        agent_headers = {"Authorization": f"Bearer {agent_token}", "X-User-Role": "tech_agent"}
        print("  [√] 客服坐席 agent 登录成功")

        print("\n================== 3. 验证运营 (operator) 越权拦截与合法访问 =================")
        # 运营有权访问: 知识文档管理 (chunks / documents), badcase池
        res_docs = await client.get("/api/v1/documents", headers=ops_headers)
        print(f"  -> 运营访问知识文档列表: HTTP {res_docs.status_code} (期望 200)")
        assert res_docs.status_code == 200

        res_badcases = await client.get("/api/v1/badcases/list", headers=ops_headers)
        print(f"  -> 运营访问BadCase池: HTTP {res_badcases.status_code} (期望 200)")
        assert res_badcases.status_code == 200

        # 运营无权访问: 运营数据报表 (/api/v1/analytics/overview), 知识库全域管理 (/api/v1/knowledge-bases)
        res_analytics = await client.get("/api/v1/analytics/overview", headers=ops_headers)
        print(f"  -> 运营访问运营数据报表接口: HTTP {res_analytics.status_code} (期望 403 越权拦截)")
        assert res_analytics.status_code == 403

        res_kb = await client.post("/api/v1/kbs", json={"name": "非法建库", "product_code": "E_COMMERCE"}, headers=ops_headers)
        print(f"  -> 运营尝试新建知识库: HTTP {res_kb.status_code} (期望 403 越权拦截)")
        assert res_kb.status_code == 403

        print("\n================== 4. 验证客服 (tech_agent) 越权拦截与合法访问 =================")
        # 客服有权访问: 对话 (/api/v1/chat/sessions), 知识文档管理 (chunks / documents)
        res_chat = await client.get("/api/v1/chat/sessions", headers=agent_headers)
        print(f"  -> 客服访问客服会话列表: HTTP {res_chat.status_code} (期望 200)")
        assert res_chat.status_code == 200

        res_agent_docs = await client.get("/api/v1/documents", headers=agent_headers)
        print(f"  -> 客服访问知识文档列表: HTTP {res_agent_docs.status_code} (期望 200)")
        assert res_agent_docs.status_code == 200

        # 客服无权访问: BadCase池, 运营报表, 知识库创建管理
        res_agent_bc = await client.get("/api/v1/badcases/list", headers=agent_headers)
        print(f"  -> 客服访问BadCase池接口: HTTP {res_agent_bc.status_code} (期望 403 越权拦截)")
        assert res_agent_bc.status_code == 403

        res_agent_analytics = await client.get("/api/v1/analytics/overview", headers=agent_headers)
        print(f"  -> 客服访问运营数据报表接口: HTTP {res_agent_analytics.status_code} (期望 403 越权拦截)")
        assert res_agent_analytics.status_code == 403

        res_agent_kb = await client.post("/api/v1/kbs", json={"name": "客服非法建库", "product_code": "SAAS_CLOUD"}, headers=agent_headers)
        print(f"  -> 客服尝试新建知识库: HTTP {res_agent_kb.status_code} (期望 403 越权拦截)")
        assert res_agent_kb.status_code == 403

        print("\n================== 5. 验证超管 (admin) 拥有全域权限 =================")
        res_admin_chat = await client.get("/api/v1/chat/sessions", headers=admin_headers)
        res_admin_docs = await client.get("/api/v1/documents", headers=admin_headers)
        res_admin_bc = await client.get("/api/v1/badcases/list", headers=admin_headers)
        res_admin_an = await client.get("/api/v1/analytics/overview", headers=admin_headers)
        assert all(r.status_code == 200 for r in [res_admin_chat, res_admin_docs, res_admin_bc, res_admin_an])
        print("  [√] 超管对会话、文档、BadCase、报表所有端点均具备 200 正常访问权限")

        print("\n========================================================")
        print("🎉 角色权限调整与端点隔离 100% 验证通过！")
        print("========================================================")

if __name__ == "__main__":
    asyncio.run(test_permissions())
