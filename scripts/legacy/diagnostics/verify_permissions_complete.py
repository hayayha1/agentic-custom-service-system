import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from app.main import app

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("=" * 65)
    print("🚀 启动权限体系全链路严格验证测试")
    print("=" * 65)

    # 1. 静态验证前端 index.html 的权限规则
    print("\n[Step 1] 验证前端 app/static/index.html 权限配置...")
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert "if (currentRole.value === 'operator') {" in html
    assert "return menuKey === 'chunks' || menuKey === 'badcases';" in html
    assert "if (currentRole.value === 'tech_agent') {" in html
    assert "return menuKey === 'chat' || menuKey === 'chunks';" in html
    print("  ✓ 运营权限：严格限定为 chunks (知识文档管理) 与 badcases (badcase池)")
    print("  ✓ 客服权限：严格限定为 chat (对话) 与 chunks (知识文档管理)")

    # 2. 模拟各个角色接口权限调用
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n[Step 2] 模拟多角色登录并获取令牌...")
        # 超管
        res_admin = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert res_admin.status_code == 200
        admin_headers = {"X-User-Role": "admin", "X-User-Id": "admin_master"}
        print("  ✓ 超级管理员 (admin) 登录就绪")

        # 运营
        res_ops = await client.post("/api/v1/auth/login", json={"username": "ops", "password": "ops123"})
        assert res_ops.status_code == 200
        ops_data = res_ops.json()
        ops_headers = {
            "X-User-Role": "operator", 
            "X-User-Id": "ops_001",
            "X-User-Kb-Id": ops_data.get("assigned_kb_id", "b34fb60a-392c-4bb2-9e10-57539b37fed2")
        }
        print("  ✓ 知识运营专员 (ops) 登录就绪")

        # 客服
        res_agent = await client.post("/api/v1/auth/login", json={"username": "agent", "password": "agent123"})
        assert res_agent.status_code == 200
        agent_headers = {
            "X-User-Role": "tech_agent",
            "X-User-Id": "agent_1028",
            "X-User-Product": "SAAS_CLOUD"
        }
        print("  ✓ 技术客服专员 (agent) 登录就绪")

        print("\n[Step 3] 验证【运营 (operator)】权限边界（仅可看文档管理和badcase池）...")
        # 允许项 1: 知识文档管理 (documents)
        r = await client.get("/api/v1/documents", headers=ops_headers)
        print(f"  -> 运营访问文档列表: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 允许项 2: 知识文档管理 (chunks)
        r = await client.get("/api/v1/chunks", headers=ops_headers)
        print(f"  -> 运营访问切片列表: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 允许项 3: BadCase池 (list)
        r = await client.get("/api/v1/badcases/list", headers=ops_headers)
        print(f"  -> 运营访问BadCase池: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 允许项 4: BadCase池 (clusters)
        r = await client.get("/api/v1/badcases/clusters", headers=ops_headers)
        print(f"  -> 运营访问BadCase聚类簇: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 禁止项 1: 对话会话列表 (chat sessions)
        r = await client.get("/api/v1/chat/sessions", headers=ops_headers)
        print(f"  -> 运营越权访问对话会话列表: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 2: 对话主接口 (chat interaction)
        r = await client.post("/api/v1/chat", json={"query": "测试提问", "customer_id": "test"}, headers=ops_headers)
        print(f"  -> 运营越权调用对话主接口: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 3: 运营数据报表 (analytics overview)
        r = await client.get("/api/v1/analytics/overview", headers=ops_headers)
        print(f"  -> 运营越权访问运营大盘报表: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 4: 知识库管理创建 (kbs)
        r = await client.post("/api/v1/kbs", json={"name": "非法新建库", "product_code": "SAAS_CLOUD"}, headers=ops_headers)
        print(f"  -> 运营越权新建知识库: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 5: 超管专属文档删除
        r = await client.delete("/api/v1/documents/dummy_id", headers=ops_headers)
        print(f"  -> 运营越权删除文档: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        print("\n[Step 4] 验证【客服 (tech_agent)】权限边界（仅可看对话和知识文档管理）...")
        # 允许项 1: 对话会话列表
        r = await client.get("/api/v1/chat/sessions", headers=agent_headers)
        print(f"  -> 客服访问对话会话列表: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 允许项 2: 知识文档管理 (documents)
        r = await client.get("/api/v1/documents", headers=agent_headers)
        print(f"  -> 客服访问文档列表: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 允许项 3: 知识文档管理 (chunks)
        r = await client.get("/api/v1/chunks", headers=agent_headers)
        print(f"  -> 客服访问切片列表: {r.status_code} (期望 200)")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

        # 禁止项 1: BadCase池 (list)
        r = await client.get("/api/v1/badcases/list", headers=agent_headers)
        print(f"  -> 客服越权访问BadCase池: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 2: BadCase聚类簇 (clusters)
        r = await client.get("/api/v1/badcases/clusters", headers=agent_headers)
        print(f"  -> 客服越权访问BadCase聚类簇: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 3: BadCase阈值配置 (configs)
        r = await client.get("/api/v1/badcases/configs", headers=agent_headers)
        print(f"  -> 客服越权访问BadCase阈值配置: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 4: 运营数据报表 (analytics overview)
        r = await client.get("/api/v1/analytics/overview", headers=agent_headers)
        print(f"  -> 客服越权访问运营大盘报表: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 5: 知识库管理创建 (kbs)
        r = await client.post("/api/v1/kbs", json={"name": "客服非法建库", "product_code": "SAAS_CLOUD"}, headers=agent_headers)
        print(f"  -> 客服越权新建知识库: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        # 禁止项 6: 超管专属文档删除
        r = await client.delete("/api/v1/documents/dummy_id", headers=agent_headers)
        print(f"  -> 客服越权删除文档: {r.status_code} (期望 403)")
        assert r.status_code == 403, f"Expected 403, got {r.status_code}"

        print("\n[Step 5] 验证【超级管理员 (admin)】全域权限正常...")
        r_admin_chat = await client.get("/api/v1/chat/sessions", headers=admin_headers)
        r_admin_doc = await client.get("/api/v1/documents", headers=admin_headers)
        r_admin_bc = await client.get("/api/v1/badcases/list", headers=admin_headers)
        r_admin_an = await client.get("/api/v1/analytics/overview", headers=admin_headers)
        assert all(res.status_code == 200 for res in [r_admin_chat, r_admin_doc, r_admin_bc, r_admin_an])
        print("  ✓ 超级管理员对对话、文档、BadCase、报表全域端点均可正常访问 (HTTP 200)")

    print("\n" + "=" * 65)
    print("🎯 所有权限规约与越权拦截验证 100% 全部通过！")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
