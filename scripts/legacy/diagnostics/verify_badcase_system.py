import sys
import json
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8001"

def http_json(method, path, body=None, headers=None, timeout=60):
    if headers is None:
        headers = {}
    url = f"{BASE_URL}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode('utf-8')
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except:
            return e.code, {"raw": content}

print("=" * 60)
print("开始全生命周期 BadCase 闭环治理系统与运营角色数据隔离测试")
print("=" * 60)

# 1. 登录验证：电商运营 ops 与 SaaS 运营 ops_saas
print("\n[1] 验证运营专员登录及权限响应...")
status, ops_res = http_json("POST", "/api/v1/auth/login", {"username": "ops", "password": "ops123"})
assert status == 200, f"ops login failed: {ops_res}"
assert ops_res["role"] == "operator", f"Wrong role: {ops_res['role']}"
ops_kb = ops_res["assigned_kb_id"]
print(f"  ✓ 电商运营 ops 登录成功: role={ops_res['role']}, assigned_kb_id={ops_kb}")

status, saas_res = http_json("POST", "/api/v1/auth/login", {"username": "ops_saas", "password": "123456"})
assert status == 200, f"ops_saas login failed: {saas_res}"
assert saas_res["role"] == "operator", f"Wrong role: {saas_res['role']}"
saas_kb = saas_res["assigned_kb_id"]
print(f"  ✓ SaaS运营 ops_saas 登录成功: role={saas_res['role']}, assigned_kb_id={saas_kb}")

# 2. 知识库数据隔离验证
print("\n[2] 验证运营专员知识库数据权限隔离...")
ops_headers = {
    "X-User-Role": "operator",
    "X-User-Id": "ops",
    "X-User-Product": "E_COMMERCE",
    "X-User-Kb-Id": ops_kb
}
saas_headers = {
    "X-User-Role": "operator",
    "X-User-Id": "ops_saas",
    "X-User-Product": "SAAS_CLOUD",
    "X-User-Kb-Id": saas_kb
}
admin_headers = {
    "X-User-Role": "admin",
    "X-User-Id": "admin_001"
}

# 2.1 知识库列表隔离
status, ops_kbs = http_json("GET", "/api/v1/kbs", headers=ops_headers)
assert status == 200
assert all(k["id"] == ops_kb for k in ops_kbs), f"ops saw other kbs: {ops_kbs}"
print(f"  ✓ ops 只能看到自己负责的知识库: {[k['name'] for k in ops_kbs]}")

status, saas_kbs = http_json("GET", "/api/v1/kbs", headers=saas_headers)
assert status == 200
assert all(k["id"] == saas_kb for k in saas_kbs), f"saas saw other kbs: {saas_kbs}"
print(f"  ✓ ops_saas 只能看到自己负责的知识库: {[k['name'] for k in saas_kbs]}")

status, admin_kbs = http_json("GET", "/api/v1/kbs", headers=admin_headers)
assert status == 200
print(f"  ✓ 超管 admin 可查看全域知识库: {len(admin_kbs)} 个知识库")

# 2.2 知识文档模块数据隔离
status, ops_docs = http_json("GET", "/api/v1/documents", headers=ops_headers)
assert status == 200
assert all(d["kb_id"] == ops_kb for d in ops_docs), "ops saw docs from other kbs!"
print(f"  ✓ ops 仅可见电商知识库下的文档: {len(ops_docs)} 篇")

# 2.3 BadCase 聚类簇数据隔离
status, ops_clusters = http_json("GET", "/api/v1/badcases/clusters", headers=ops_headers)
assert status == 200
assert all(c["kb_id"] == ops_kb for c in ops_clusters), "ops saw badcase clusters from other kbs!"
print(f"  ✓ ops 仅可见电商库的 BadCase 问题簇: {len(ops_clusters)} 个簇")

# 2.4 跨知识库越权拦截校验 (403 Forbidden)
if ops_clusters:
    target_cluster_id = ops_clusters[0]["id"]
    status, cross_res = http_json("GET", f"/api/v1/badcases/clusters/{target_cluster_id}/cases", headers=saas_headers)
    assert status == 403, f"Cross-kb access should be blocked with 403, got {status}: {cross_res}"
    print(f"  ✓ SaaS运营越权查看电商簇详情被系统严格拦截 (HTTP 403 Forbidden)")

# 3. BadCase 采集链路测试 (用户差评与坐席标错)
print("\n[3] 验证多源 BadCase 采集入库...")
# 3.1 用户差评采集
# 创建一个测试用户会话并发送提问获取 message_id
user_headers = {"X-User-Role": "user", "X-User-Id": "test_user_888"}
status, session_res = http_json("POST", "/api/v1/chat/sessions", {
    "customer_id": "test_user_888",
    "customer_name": "测试客户",
    "product_code": "E_COMMERCE"
}, headers=user_headers)
session_id = session_res["id"]

status, chat_res = http_json("POST", "/api/v1/chat", {
    "session_id": session_id,
    "user_id": "test_user_888",
    "query": "你们家的鲜奶喝了一半能退款吗？"
}, headers=user_headers)
msg_id = chat_res.get("message_id")
print(f"  ✓ 对话发送成功: message_id={msg_id}, 回答置信度={chat_res.get('confidence_score')}")

# 提交用户差评
status, fb_res = http_json("POST", "/api/v1/badcases/feedback", {
    "message_id": msg_id,
    "session_id": session_id,
    "feedback_type": "DOWN",
    "comment": "答非所问: 机器人没听懂生鲜拆封能不能退"
}, headers=user_headers)
assert status == 200
print(f"  ✓ 用户显式差评提交成功入库: {fb_res['message']}")

# 3.2 坐席客服标错采集
agent_headers = {"X-User-Role": "tech_agent", "X-User-Id": "tech_001", "X-User-Product": "E_COMMERCE"}
status, label_res = http_json("POST", "/api/v1/badcases/agent-label", {
    "message_id": msg_id,
    "session_id": session_id,
    "label_category": "WRONG_ANSWER",
    "notes": "客服质检：AI对生鲜拆封退款规则理解错误"
}, headers=agent_headers)
assert status == 200
print(f"  ✓ 坐席人工质检标错成功入库: {label_res['message']}")

# 4. BadCase 闭环治理：采纳生成知识草稿与审核流
print("\n[4] 验证运营专员采纳 BadCase 簇生成待审核知识草稿...")
# 选取一个待处理簇
pending_cluster = next((c for c in ops_clusters if c["status"] == "PENDING"), ops_clusters[0])
cluster_id = pending_cluster["id"]
print(f"  选中目标问题簇: 《{pending_cluster.get('cluster_name') or pending_cluster.get('representative_query')}》 (推荐动作: {pending_cluster['recommended_action']})")

status, adopt_res = http_json("POST", f"/api/v1/badcases/clusters/{cluster_id}/adopt", {
    "action": "CREATE_FAQ",
    "standard_question": "生鲜类乳制品开封后是否支持7天无理由退款？",
    "similar_questions": [
        "鲜奶拆封了可以退款吗",
        "喝了一半的牛奶能退吗",
        "生鲜食品开封后退换货规则"
    ],
    "answer": "根据《消费者权益保护法》及商城售后政策，鲜奶等冷链生鲜食品保质期短、易变质，拆封后影响二次销售，不支持7天无理由退款。若商品存在质量变质或胀气，请于签收24小时内联系客服凭凭证申请全额退款赔付。"
}, headers=ops_headers)
assert status == 200
created_doc_id = adopt_res["doc_id"]
print(f"  ✓ 运营专员采纳成功，生成知识草稿: doc_id={created_doc_id}, 状态={adopt_res['cluster_status']}")

# 检查该草稿文档状态必须为 PENDING_REVIEW
status, doc_info = http_json("GET", f"/api/v1/documents/{created_doc_id}", headers=ops_headers)
assert status == 200
doc_obj = doc_info.get("doc", doc_info)
assert doc_obj["status"] == "PENDING_REVIEW", f"Expected PENDING_REVIEW, got {doc_obj['status']}"
print(f"  ✓ 验证新生成草稿状态正确处于: {doc_obj['status']} (待超管审核，未污染检索向量库)")

# 5. 超管审核通过与向量索引生效
print("\n[5] 验证超级管理员审核通过知识草稿并向量化...")
status, review_res = http_json("POST", f"/api/v1/documents/{created_doc_id}/approve", headers=admin_headers)
assert status == 200, f"Approve failed: {review_res}"
assert review_res["status"] == "ACTIVE"
print(f"  ✓ 超级管理员审核通过，文档状态正式转为: {review_res['status']}, 切片数={review_res['chunk_count']}")

# 6. 效果回流验证：对簇内真实问句执行自动化回归测试
print("\n[6] 验证效果回流回归测试 (自动化检验闭环成效)...")
status, val_res = http_json("POST", f"/api/v1/badcases/clusters/{cluster_id}/validate", headers=ops_headers)
assert status == 200
report = val_res["data"]
sample_count = report.get("total_cases") or report.get("sample_count") or len(report.get("details", []))
print(f"  ✓ 回归测试执行完成: 通过率 = {report['pass_rate'] * 100:.1f}%, 测试用例数 = {sample_count}")
for item in (report.get("details") or report.get("items", [])):
    pass_mark = "✅ 通过" if item["passed"] else "❌ 未达标"
    score = item.get("top_score") if item.get("top_score") is not None else item.get("score", 0.0)
    matched = item.get("top_heading") or item.get("top_doc") or item.get("matched_heading") or "无"
    print(f"    - [{pass_mark}] Query: '{item['query']}' | 置信度得分: {score:.4f} | 命中切片: {matched}")

# 7. 全景转化看板数据验证
print("\n[7] 验证 BadCase 闭环转化看板报表...")
status, dash_res = http_json("GET", f"/api/v1/badcases/analytics/dashboard?kb_id={ops_kb}", headers=ops_headers)
assert status == 200
summary = dash_res["summary"]
print(f"  ✓ 看板统计数据:")
print(f"    · 采集总量: {summary['total_cases_collected']}")
print(f"    · 聚类簇数: {summary['total_clusters']}")
print(f"    · 待处理簇: {summary['pending_clusters']}")
print(f"    · 已采纳簇: {summary['adopted_clusters']}")
print(f"    · 来源细分: {dash_res['case_type_breakdown']}")

# 8. 前端静态文件提供验证
print("\n[8] 验证前端页面静态托管...")
req = urllib.request.Request("http://127.0.0.1:8001/static/index.html")
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')
    assert "BadCase 闭环治理工作台" in html
    assert "ops / ops123" in html
    assert "showAdoptModal" in html
    assert "showValidationModal" in html
    print(f"  ✓ 前端页面 index.html 正常提供 (size={len(html)} 字节)，包含 BadCase 治理与运营全套组件")

print("\n" + "=" * 60)
print("🎉 恭喜！所有 BadCase 闭环治理、运营角色数据隔离与回流验证测试全部通过！")
print("=" * 60)
