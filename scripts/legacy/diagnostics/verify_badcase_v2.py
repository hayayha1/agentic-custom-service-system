import asyncio
import sys
import httpx
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8001"

async def test_full_v2_system():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        print("\n================== 1. 验证 7 大标准根因字典与官方定义 ==================")
        res = await client.get("/api/v1/badcases/root-causes")
        assert res.status_code == 200, f"root-causes API failed: {res.text}"
        rc_dict = res.json()
        expected_keys = [
            "RC_INVALID_CASE", "RC_MATCH_CONFUSION", "RC_KNOWLEDGE_ERROR",
            "RC_CONTEXT_MISSING", "RC_KNOWLEDGE_MISSING", "RC_RECALL_INSUFFICIENT",
            "RC_QUERY_AMBIGUOUS"
        ]
        for k in expected_keys:
            assert k in rc_dict, f"Missing root cause key: {k}"
            print(f"  [√] 根因 {k}: {rc_dict[k]['name']} (优先级 {rc_dict[k]['priority']}) -> {rc_dict[k]['action']}")

        print("\n================== 2. 模拟角色认证与 Token 获取 ==================")
        # 登录超管
        admin_login = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert admin_login.status_code == 200, f"admin login failed: {admin_login.text}"
        admin_token = admin_login.json()["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("  [√] 超级管理员 admin 登录认证成功")

        # 登录电商运营专员 ops
        ops_login = await client.post("/api/v1/auth/login", json={"username": "ops", "password": "ops123"})
        assert ops_login.status_code == 200, f"ops login failed: {ops_login.text}"
        ops_token = ops_login.json()["token"]
        ops_headers = {"Authorization": f"Bearer {ops_token}"}
        print("  [√] 电商运营专员 ops 登录认证成功 (负责电商售后库)")

        print("\n================== 3. 验证动态三轮输入上下文与自动根因初诊 ==================")
        # 创建一个测试客户会话
        sess_res = await client.post("/api/v1/chat/sessions", json={
            "customer_id": "test_user_v2",
            "customer_name": "王女士",
            "product_code": "E_COMMERCE",
            "force_new": True
        })
        assert sess_res.status_code == 200
        sess_data = sess_res.json()
        session_id = sess_data["id"]
        print(f"  [√] 创建测试会话 session_id: {session_id}")

        # 进行 4 轮问答交互，验证逆向滑动窗口是否精确截断至近三轮用户输入
        q_list = [
            "你好，我想问一下", # User 1
            "买的衣服尺码不合适怎么办", # User 2
            "运费险怎么退", # User 3
            "那鲜奶开封了觉得不好喝还能退吗" # User 4 (触发点)
        ]
        last_msg_id = None
        for q in q_list:
            chat_resp = await client.post("/api/v1/chat", json={
                "session_id": session_id,
                "product_code": "E_COMMERCE",
                "customer_id": "test_user_v2",
                "query": q
            }, headers=admin_headers)
            assert chat_resp.status_code == 200, f"Chat failed for query '{q}': {chat_resp.text}"
            last_msg_id = chat_resp.json()["message_id"]

        print(f"  [√] 完成连续 4 轮用户提问与 AI 回答交互 (最终 message_id: {last_msg_id})")

        # 用户对最后一轮提问提交 👎 差评
        fb_resp = await client.post("/api/v1/badcases/feedback", json={
            "message_id": last_msg_id,
            "session_id": session_id,
            "feedback_type": "DOWN",
            "comment": "生鲜开封不给退，AI乱说支持7天无理由"
        }, headers=admin_headers)
        assert fb_resp.status_code == 200, f"Feedback failed: {fb_resp.text}"
        case_data = fb_resp.json()
        case_id = case_data["case_id"]
        print(f"  [√] 差评录入成功，返回 case_id: {case_id}, 根因初诊: {case_data.get('root_cause')}")

        # 查询该 BadCase 明细，检查上下文记忆长度是否正好为用户近 3 轮
        bc_list_res = await client.get("/api/v1/badcases/list?keyword=鲜奶", headers=admin_headers)
        assert bc_list_res.status_code == 200
        bc_items = bc_list_res.json()["items"]
        assert len(bc_items) > 0
        target_case = [c for c in bc_items if c["id"] == case_id][0]
        
        ctx = target_case["chat_context"]
        user_msgs_in_ctx = [m for m in ctx if m["role"] == "user"]
        print(f"  [√] 上下文记忆验证：总消息数 {len(ctx)}，其中用户提问轮数: {len(user_msgs_in_ctx)} (精确截断为近3轮)")
        assert len(user_msgs_in_ctx) == 3, f"Expected 3 user rounds, got {len(user_msgs_in_ctx)}"
        print(f"  [√] 命中知识来源检查: {len(target_case.get('recall_sources', []))} 处切片已关联")
        print(f"  [√] 客观测根因初诊结果: {target_case.get('root_cause_name')} ({target_case.get('root_cause_code')}) - {target_case.get('root_cause_reason')}")

        # 录入额外几条测试 BadCase：一条高相似度（用于聚类成簇），两条长尾孤岛（用于测试全量池与手动合并）
        extra_cases = [
            ("鲜奶打开喝了一口可以退款吗", "同类相似问"),
            ("怎么开具公司抬头的电子增值税专票", "发票长尾孤岛1"),
            ("系统登录密码忘记了怎么快速找回", "密码长尾孤岛2")
        ]
        for eq, note in extra_cases:
            sess_tmp = await client.post("/api/v1/chat/sessions", json={
                "customer_id": "test_extra",
                "customer_name": "测试客户",
                "product_code": "E_COMMERCE",
                "force_new": True
            })
            c_resp = await client.post("/api/v1/chat", json={
                "session_id": sess_tmp.json()["id"],
                "product_code": "E_COMMERCE",
                "customer_id": "test_extra",
                "query": eq
            }, headers=admin_headers)
            mid = c_resp.json()["message_id"]
            await client.post("/api/v1/badcases/feedback", json={
                "message_id": mid,
                "session_id": sess_tmp.json()["id"],
                "feedback_type": "DOWN",
                "comment": f"测试辅助用例: {note}"
            }, headers=admin_headers)

        print("\n================== 4. 全量 BadCase 池多维检索与长尾筛选 ==================")
        all_cases_res = await client.get("/api/v1/badcases/list?cluster_status=all", headers=admin_headers)
        assert all_cases_res.status_code == 200
        all_data = all_cases_res.json()
        print(f"  [√] 全量 BadCase 池总数: {all_data['total']} 笔")

        unclustered_res = await client.get("/api/v1/badcases/list?cluster_status=unclustered", headers=admin_headers)
        assert unclustered_res.status_code == 200
        print(f"  [√] 未成簇长尾孤岛 Case 数: {unclustered_res.json()['total']} 笔")

        print("\n================== 5. 增量聚类防重与簇整体根因裁定 ==================")
        # 触发增量聚类
        c_res = await client.post("/api/v1/badcases/cluster/run?mode=incremental", headers=ops_headers)
        assert c_res.status_code == 200
        cluster_run_data = c_res.json()
        print(f"  [√] 增量聚类完成: {cluster_run_data['message']}")

        # 再次触发增量聚类，验证不会重复生成相同的簇 (幂等性)
        c_res_2 = await client.post("/api/v1/badcases/cluster/run?mode=incremental", headers=ops_headers)
        assert c_res_2.status_code == 200
        assert c_res_2.json()["cluster_count"] == cluster_run_data["cluster_count"], "重复增量聚类导致簇数量不幂等！"
        print(f"  [√] 增量防重验证通过：两次聚类后簇总数保持 {cluster_run_data['cluster_count']} 不变")

        # 获取簇列表检查簇整体根因
        clusters_res = await client.get("/api/v1/badcases/clusters", headers=ops_headers)
        assert clusters_res.status_code == 200
        clusters = clusters_res.json()
        assert len(clusters) > 0
        top_cluster = clusters[0]
        print(f"  [√] 顶层问题簇: 《{top_cluster['cluster_name']}》")
        print(f"      - 频次热度: {top_cluster['case_count']} 次")
        print(f"      - 簇整体根因: {top_cluster.get('root_cause_name')} ({top_cluster.get('root_cause_code')})")
        print(f"      - 官方标准定义: {top_cluster.get('root_cause_description')}")
        print(f"      - 推荐治理动作: {top_cluster.get('recommended_action')}")

        print("\n================== 6. 手动合并建簇 (长尾 Case 治理) ==================")
        # 获取 2 条未成簇的 case 进行手动合并
        p_cases = await client.get("/api/v1/badcases/list?cluster_status=unclustered", headers=ops_headers)
        p_items = p_cases.json()["items"]
        if len(p_items) < 2:
            # 动态补录 2 条未成簇长尾 Case 验证手动合并
            for t_q in ["测试发票税号核对长尾特例问", "测试冷链极速送达超时违约金特例"]:
                sess_t = await client.post("/api/v1/chat/sessions", json={
                    "customer_id": "test_unclustered", "customer_name": "长尾客户", "product_code": "E_COMMERCE", "force_new": True
                })
                c_t = await client.post("/api/v1/chat", json={
                    "session_id": sess_t.json()["id"], "product_code": "E_COMMERCE", "customer_id": "test_unclustered", "query": t_q
                }, headers=admin_headers)
                await client.post("/api/v1/badcases/feedback", json={
                    "message_id": c_t.json()["message_id"], "session_id": sess_t.json()["id"], "feedback_type": "DOWN", "comment": "长尾特例手工合并测试"
                }, headers=admin_headers)
            p_cases = await client.get("/api/v1/badcases/list?cluster_status=unclustered", headers=ops_headers)
            p_items = p_cases.json()["items"]

        assert len(p_items) >= 2, f"Expected at least 2 unclustered cases, got {len(p_items)}"
        merge_ids = [p_items[0]["id"], p_items[1]["id"]]
        manual_res = await client.post("/api/v1/badcases/manual-cluster", json={
            "case_ids": merge_ids,
            "cluster_name": "售后发票与冷链特例合并簇",
            "standard_question": "发票开具与冷链超时服务综合问题"
        }, headers=ops_headers)
        assert manual_res.status_code == 200
        print(f"  [√] 手动合并建簇成功: {manual_res.json()['message']}")

        print("\n================== 7. 场景 C: 修订长文本知识库草稿版本流 ==================")
        # 获取或创建一个电商文档用于修订
        target_kb_id = target_case.get("kb_id") or "b34fb60a-392c-4bb2-9e10-57539b37fed2"
        kb_docs = await client.get(f"/api/v1/documents?kb_id={target_kb_id}", headers=admin_headers)
        docs_list = kb_docs.json() if kb_docs.status_code == 200 else []
        
        if not docs_list:
            create_doc_res = await client.post("/api/v1/documents", json={
                "kb_id": target_kb_id,
                "name": "电商售后服务标准规范",
                "doc_type": "MD",
                "content": "# 电商售后政策规范\n\n## 1. 通用原则\n支持7天无理由退货（特殊商品除外）。\n\n## 2. 退货运费\n购买运费险的可自动理赔。",
                "priority": 1
            }, headers=admin_headers)
            assert create_doc_res.status_code == 200
            doc_to_revise = create_doc_res.json()
        else:
            doc_to_revise = docs_list[0]

        rev_res = await client.post("/api/v1/badcases/revise-doc", json={
            "doc_id": doc_to_revise["id"],
            "new_content": (doc_to_revise.get("content") or "正文") + "\n\n### 4. 生鲜食品特殊售后细则\n鲜奶、短保及冷链生鲜拆封后不支持7天无理由退货。",
            "change_summary": "根据BadCase差评增补生鲜食品例外退换条款",
            "case_id": case_id,
            "cluster_id": top_cluster["id"]
        }, headers=ops_headers)
        assert rev_res.status_code == 200, f"Revise doc failed: {rev_res.text}"
        print(f"  [√] 修订长文本知识库成功: {rev_res.json()['message']}")

        print("\n================== 8. 规则判定阈值配置与审计日志 ==================")
        # 修改阈值
        conf_res = await client.put(f"/api/v1/badcases/configs/{target_kb_id}", json={
            "threshold_low": 0.35,
            "threshold_high": 0.75,
            "short_query_len": 6,
            "candidate_rank_start": 4,
            "candidate_rank_end": 10,
            "context_window_rounds": 3
        }, headers=admin_headers)
        assert conf_res.status_code == 200, f"Config update failed: {conf_res.text}"
        print(f"  [√] 更新知识库阈值成功: {conf_res.json()['message']}")

        # 查询变更审计日志
        logs_res = await client.get(f"/api/v1/badcases/configs/logs?kb_id={target_kb_id}", headers=admin_headers)
        assert logs_res.status_code == 200
        logs = logs_res.json()
        assert len(logs) > 0
        latest_log = logs[0]
        print(f"  [√] 审计日志记录生效: 操作人 {latest_log['operator']}, 变更时间 {latest_log['changed_at']}")

        print("\n================== 9. 效果回流自动化验证 ==================")
        val_res = await client.post(f"/api/v1/badcases/clusters/{top_cluster['id']}/validate", headers=ops_headers)
        assert val_res.status_code == 200
        val_data = val_res.json()
        print(f"  [√] 回流验证完成: {val_data['message']}")
        print(f"      - 回归样本总数: {val_data['data']['total_cases']}")
        print(f"      - 达标通过率: {val_data['data']['pass_rate'] * 100:.1f}%")

        print("\n================== 10. 全景大盘数据分析 ==================")
        dash_res = await client.get("/api/v1/badcases/analytics/dashboard", headers=admin_headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        print("  [√] 全景看板数据聚合正常:")
        print(f"      - 采集总数: {dash_data['summary']['total_cases_collected']}")
        print(f"      - 根因分布明细: {dash_data['root_cause_breakdown']}")

    print("\n🎉🎉🎉 全部 10 项 BadCase 优化方案全流程验证通过！🎉🎉🎉\n")

if __name__ == "__main__":
    asyncio.run(test_full_v2_system())
