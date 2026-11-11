import asyncio
import os
import sys

# Windows 终端编码保护
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.abspath('.'))

from app.db.session import async_session_maker
from app.services.retrieval.engine import retrieval_engine
from app.services.model_service import model_service
from app.models.knowledge_base import KnowledgeBase
from sqlalchemy import select

async def search(query: str, top_k: int = 3, kb_id: str = None):
    async with async_session_maker() as db:
        # 未指定 kb_id 时自动获取首个生效的知识库
        if not kb_id:
            res = await db.execute(select(KnowledgeBase).where(KnowledgeBase.status == "ACTIVE"))
            kb = res.scalars().first()
            if not kb:
                print("[错误] 未找到任何启用的知识库！")
                return
            kb_id = kb.id
            kb_name = kb.name
        else:
            kb = await db.get(KnowledgeBase, kb_id)
            kb_name = kb.name if kb else kb_id

        print("=" * 60)
        print(f"[检索测试] Top-{top_k} 文本块召回")
        print(f"[目标知识库] {kb_name} (ID: {kb_id})")
        print(f"[用户原始提问] {query}")
        
        # 1. 轻量改写（指代补全与术语标准化）
        rewritten = await model_service.rewrite_query(query, "电商平台")
        print(f"[语义改写结果] {rewritten}")
        print("-" * 60)

        # 自动检索测试集标注（若属于 50 道评测集中的问题）
        import json
        dataset_path = os.path.join("data", "evaluation", "test_dataset.json")
        matched_case = None
        if os.path.exists(dataset_path):
            try:
                with open(dataset_path, "r", encoding="utf-8") as f:
                    test_ds = json.load(f)
                q_clean = query.strip().lower()
                matched_case = next((item for item in test_ds if item["question"].strip().lower() == q_clean or item["question"] in query or query in item["question"]), None)
            except Exception:
                pass

        if matched_case:
            print(f"[测试集基准用例] {matched_case['id']} ({matched_case.get('category')} / {matched_case.get('eval_type')})")
            print(f"  🎯 标注目标 source_doc    : {matched_case['source_doc']}")
            print(f"  🎯 标注目标 source_section: {matched_case['source_section']}")
            print(f"  🔑 核心采分点 key_facts   : {matched_case.get('key_facts')}")
            print("-" * 60)

        # 2. 仅调用混合检索器与 Reranker (不调用大模型生成答案)
        chunks, top_score = await retrieval_engine.retrieve_and_rerank(
            db=db,
            kb_id=kb_id,
            raw_query=query,
            rewritten_query=rewritten,
            bm25_top_k=15,
            vector_top_k=15,
            rerank_top_k=top_k
        )

        def extract_source_section(heading_path: str) -> str:
            if not heading_path:
                return "正文"
            parts = [p.strip() for p in heading_path.split(" > ") if p.strip()]
            return parts[-1] if parts else heading_path

        # 如果匹配到测试用例，计算命中排名
        hit_rank = None
        if matched_case:
            tgt_doc = matched_case["source_doc"]
            tgt_sec = matched_case["source_section"]
            for idx, c in enumerate(chunks):
                c_doc = c["doc_name"]
                c_sec = extract_source_section(c.get("heading_path") or "")
                c_path = c.get("heading_path") or ""
                if (c_doc == tgt_doc or c_doc.startswith(tgt_doc.split(".")[0])) and (tgt_sec in c_path or c_sec in tgt_sec or tgt_sec[:4] in c_path):
                    hit_rank = idx + 1
                    break

            if hit_rank and hit_rank <= 3:
                print(f"🎉【HitRate@3 命中判定】: 成功在第 {hit_rank} 位命中！(Hit@3 ✅)")
            elif hit_rank and hit_rank <= top_k:
                print(f"🔔【HitRate@{top_k} 命中判定】: 在第 {hit_rank} 位命中 (超出Top-3)")
            else:
                print(f"⚠️【HitRate 命中判定】: 未在当前 Top-{top_k} 候选中命中目标章节")
            print("-" * 60)

        print(f"[Rerank 最高置信度得分] {top_score:.4f}")
        print(f"[实际返回候选块数量] {len(chunks)}\n")

        for idx, c in enumerate(chunks):
            sec = extract_source_section(c.get("heading_path") or "")
            is_matched_chunk = False
            if matched_case and hit_rank == idx + 1:
                is_matched_chunk = True

            hit_tag = "  <-- 【🎯 命中用例标注目标】" if is_matched_chunk else ""
            print(f">>> 【Top {idx + 1}】 得分: {c['score']:.4f}{hit_tag}")
            print(f"    source_doc    : {c['doc_name']}")
            print(f"    source_section: {sec}")
            print(f"    heading_path  : {c['heading_path']}")
            print(f"    文档优先级    : {c['priority']}")
            content = c.get('content', '').strip()
            preview = content if len(content) <= 300 else content[:300] + "..."
            print(f"    文本内容:\n{preview}")
            print("-" * 60)

def main():
    if len(sys.argv) > 1:
        q = sys.argv[1]
        k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        asyncio.run(search(q, k))
    else:
        print("提示：可在命令行直接运行：python scripts/legacy/diagnostics/test_search.py \"你的问题\" 3")
        print("也可以直接在下方交互式输入（输入 exit 或 q 退出）：")
        while True:
            try:
                user_input = input("\n请输入测试问句 > ").strip()
                if not user_input or user_input.lower() in ["exit", "q", "quit"]:
                    print("已退出测试。")
                    break
                k_input = input("请输入返回 Top-K 数量 (默认 3): ").strip()
                k = int(k_input) if k_input.isdigit() else 3
                asyncio.run(search(user_input, k))
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == '__main__':
    main()
