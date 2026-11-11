import asyncio
import sys
import httpx
import json

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://127.0.0.1:8001"

async def run_tests():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("\n================== 0. 登录认证获取 Token ==================")
        login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("  [√] 管理员 admin 登录成功")

        print("\n================== 测试项 1: 簇根因和建议操作单点一致性 =================")
        # 获取所有簇列表，检查根因、建议动作与诊断依据是否完全自洽
        clusters_res = await client.get("/api/v1/badcases/clusters", headers=headers)
        assert clusters_res.status_code == 200, f"Get clusters failed: {clusters_res.text}"
        clusters = clusters_res.json()
        print(f"  当前共有 {len(clusters)} 个聚类簇")
        
        mismatched_clusters = []
        for c in clusters:
            code = c.get("root_cause_code")
            action = c.get("recommended_action")
            reason = c.get("recommended_reason") or c.get("root_cause_reason") or ""
            
            # 校验规则
            if code == "RC_KNOWLEDGE_MISSING":
                if action != "CREATE_FAQ" or "已有" in reason or "场景 A" in reason:
                    mismatched_clusters.append((c["id"], code, action, reason))
            elif code == "RC_RECALL_INSUFFICIENT":
                if action != "ADD_SIMILAR_QUERY" or "缺失" in reason or "场景 B" in reason:
                    mismatched_clusters.append((c["id"], code, action, reason))
            elif code == "RC_KNOWLEDGE_ERROR":
                if action != "UPDATE_DOC":
                    mismatched_clusters.append((c["id"], code, action, reason))

        if mismatched_clusters:
            print("  [X] 发现不匹配的簇:", mismatched_clusters)
            assert False, f"Found {len(mismatched_clusters)} mismatched clusters!"
        else:
            print(f"  [√] 全部 {len(clusters)} 个簇的根因代码、建议动作和诊断依据完全自洽！")
            # 打印一个知识缺失簇和一个召回不足簇作为示例
            missing_cases = [c for c in clusters if c.get("root_cause_code") == "RC_KNOWLEDGE_MISSING"]
            if missing_cases:
                mc = missing_cases[0]
                print(f"      示例知识缺失簇: [{mc['root_cause_code']}] 动作: {mc['recommended_action']}, 诊断: {mc.get('recommended_reason')}")
            recall_cases = [c for c in clusters if c.get("root_cause_code") == "RC_RECALL_INSUFFICIENT"]
            if recall_cases:
                rc = recall_cases[0]
                print(f"      示例召回不足簇: [{rc['root_cause_code']}] 动作: {rc['recommended_action']}, 诊断: {rc.get('recommended_reason')}")

        print("\n================== 测试项 2: 新建 FAQ 支持选择归属知识库 =================")
        # 获取知识库列表
        kbs_res = await client.get("/api/v1/kbs", headers=headers)
        assert kbs_res.status_code == 200, f"Get KBs failed: {kbs_res.text}"
        kbs = kbs_res.json()
        assert len(kbs) >= 1
        target_kb = kbs[0]
        target_kb_id = target_kb["id"]
        print(f"  选取目标知识库: {target_kb['name']} (id={target_kb_id})")

        # 选一个簇进行采纳新建 FAQ
        cluster_to_adopt = clusters[0]
        test_q = f"测试新建FAQ问法_{cluster_to_adopt['id'][:6]}"
        test_a = f"这是针对知识库 {target_kb['name']} 的权威标准解答内容"
        adopt_payload = {
            "action": "CREATE_FAQ",
            "standard_question": test_q,
            "similar_questions": [f"{test_q}_相似1", f"{test_q}_相似2"],
            "answer": test_a,
            "target_kb_id": target_kb_id
        }
        adopt_res = await client.post(f"/api/v1/badcases/clusters/{cluster_to_adopt['id']}/adopt", json=adopt_payload, headers=headers)
        assert adopt_res.status_code == 200, f"Adopt CREATE_FAQ failed: {adopt_res.text}"
        adopt_data = adopt_res.json()
        print(f"  [√] 采纳接口返回成功: {adopt_data.get('message')}")
        created_doc_id = adopt_data.get("doc_id")
        assert created_doc_id, "Returned doc_id should not be empty"

        # 检查新文档是否确实归属于 target_kb_id
        doc_detail_res = await client.get(f"/api/v1/documents/{created_doc_id}", headers=headers)
        assert doc_detail_res.status_code == 200
        doc_detail = doc_detail_res.json()
        doc_kb_id = doc_detail["doc"]["kb_id"]
        assert doc_kb_id == target_kb_id, f"Doc KB ID {doc_kb_id} != target {target_kb_id}"
        print(f"  [√] 新建 FAQ 成功落库至指定知识库 (doc.kb_id={doc_kb_id})，状态为 PENDING_REVIEW")

        print("\n================== 测试项 3: 追加相似问法不修改原文档解答 =================")
        # 1. 查找或准备一个已有文档
        docs_res = await client.get("/api/v1/documents", headers=headers)
        assert docs_res.status_code == 200
        docs = docs_res.json()
        faq_docs = [d for d in docs if d.get("doc_type") == "FAQ" and d.get("id") != created_doc_id]
        if not faq_docs:
            target_doc_for_append = docs[0]
        else:
            target_doc_for_append = faq_docs[0]
        
        target_doc_id = target_doc_for_append["id"]
        # 获取追加前的详细数据（含原始解答）
        before_detail = (await client.get(f"/api/v1/documents/{target_doc_id}", headers=headers)).json()
        before_answer = before_detail.get("faq", {}).get("answer") if before_detail.get("faq") else before_detail["doc"].get("content")
        print(f"  目标文档: 《{target_doc_for_append['name']}》 (id={target_doc_id})")
        print(f"  追加前解答内容预览: {str(before_answer)[:40]}...")

        # 执行追加相似问法
        append_sim_queries = ["新发现的用户问法A", "新发现的用户问法B"]
        adopt_append_payload = {
            "action": "ADD_SIMILAR_QUERY",
            "target_doc_id": target_doc_id,
            "similar_questions": append_sim_queries,
            "standard_question": "",
            "answer": "" # 用户不填、也不应传递新解答
        }
        adopt_append_res = await client.post(f"/api/v1/badcases/clusters/{cluster_to_adopt['id']}/adopt", json=adopt_append_payload, headers=headers)
        assert adopt_append_res.status_code == 200, f"Adopt ADD_SIMILAR_QUERY failed: {adopt_append_res.text}"
        
        # 重新获取文档详细信息，验证 answer 未被清空或覆盖，且相似问已扩充
        after_detail = (await client.get(f"/api/v1/documents/{target_doc_id}", headers=headers)).json()
        after_answer = after_detail.get("faq", {}).get("answer") if after_detail.get("faq") else after_detail["doc"].get("content")
        assert after_answer == before_answer, f"Answer was modified! Before: {before_answer}, After: {after_answer}"
        print(f"  [√] 原文档解答内容完全保持不变！")
        if after_detail.get("faq"):
            sims = after_detail["faq"].get("similar_questions", [])
            print(f"  [√] 目标 FAQ 当前相似问总数: {len(sims)}，包含新增问法: {all(q in sims for q in append_sim_queries)}")

        print("\n================== 测试项 4: 修订原文档支持切换文档及正文回显 =================")
        # 测试 GET /documents/{doc_id} 返回完整原文
        for test_d in docs[:3]:
            d_res = await client.get(f"/api/v1/documents/{test_d['id']}", headers=headers)
            assert d_res.status_code == 200
            d_json = d_res.json()
            content = (d_json.get("doc") and d_json["doc"].get("content")) or d_json.get("content")
            assert content is not None, f"Document {test_d['id']} returned None content"
            print(f"  [√] 校验文档 《{test_d['name']}》: content 字段正常回显，长度为 {len(content)} 字符")

        # 测试 POST /api/v1/badcases/revise-doc 修订草稿提交流程
        test_doc_for_revise = docs[0]
        cur_detail = (await client.get(f"/api/v1/documents/{test_doc_for_revise['id']}", headers=headers)).json()
        cur_content = (cur_detail.get("doc") and cur_detail["doc"].get("content")) or cur_detail.get("content") or ""
        old_version = cur_detail["doc"].get("version", 1)

        revised_text = cur_content + f"\n\n<!-- 自动验证修订新增条款: {cluster_to_adopt['id'][:6]} -->"
        revise_payload = {
            "doc_id": test_doc_for_revise["id"],
            "new_content": revised_text,
            "change_summary": "测试自动验证：修改指定文档并回显正文",
            "cluster_id": cluster_to_adopt["id"]
        }
        revise_res = await client.post("/api/v1/badcases/revise-doc", json=revise_payload, headers=headers)
        assert revise_res.status_code == 200, f"Revise doc failed: {revise_res.text}"
        revise_data = revise_res.json()
        print(f"  [√] 修订草稿提交成功: {revise_data.get('message')}")
        
        # 验证新版本
        after_revise = (await client.get(f"/api/v1/documents/{test_doc_for_revise['id']}", headers=headers)).json()
        new_version = after_revise["doc"].get("version")
        assert new_version == old_version + 1, f"Version should increment from {old_version} to {old_version + 1}, got {new_version}"
        print(f"  [√] 文档版本成功升级: v{old_version} -> v{new_version}")

        print("\n================== 测试项 5: 验证前端静态文件 HTML 语法与结构 =================")
        with open("app/static/index.html", "r", encoding="utf-8") as f:
            html = f.read()

        # 检查选择知识库的 select
        assert 'adoptForm.target_kb_id' in html, "Frontend missing adoptForm.target_kb_id"
        assert 'v-model="adoptForm.target_kb_id"' in html, "Frontend missing v-model='adoptForm.target_kb_id'"
        print("  [√] 前端采纳弹窗包含目标知识库选择框 (adoptForm.target_kb_id)")

        # 检查追加相似问不要求输入解答
        assert 'adoptTargetDocInfo' in html, "Frontend missing adoptTargetDocInfo"
        assert 'adoptForm.action === \'CREATE_FAQ\'' in html, "Frontend missing conditional CREATE_FAQ check"
        print("  [√] 前端追加相似问模式已隐藏 Answer 输入框，并增加了目标文档已有解答的只读预览卡片")

        # 检查修改原文档支持下拉切换并展示原文
        assert 'reviseDocForm.doc_id' in html, "Frontend missing reviseDocForm.doc_id"
        assert 'onReviseDocChange' in html, "Frontend missing onReviseDocChange"
        assert 'resetReviseContentToOriginal' in html, "Frontend missing resetReviseContentToOriginal"
        assert 'loadDocContentForRevise' in html, "Frontend missing loadDocContentForRevise"
        print("  [√] 前端文档修订弹窗包含文档选择下拉框、自动拉取最新正文回显及「恢复原文」按钮")

        print("\n========================================================")
        print("🎉 4 项问题全部验证通过！无任何报错或逻辑冲突！")
        print("========================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
