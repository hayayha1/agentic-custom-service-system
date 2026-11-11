import asyncio
import os
import sys
import json
import re

sys.path.insert(0, os.path.abspath('.'))

from app.db.session import async_session_maker
from app.services.retrieval.engine import retrieval_engine
from app.services.model_service import model_service

KB_ID = "b34fb60a-392c-4bb2-9e10-57539b37fed2"

def is_chunk_match(chunk, target_doc, target_section):
    # 1. Document match
    chunk_doc = chunk.get("doc_name", "")
    if chunk_doc != target_doc and not chunk_doc.startswith(target_doc.split('.')[0]):
        return False
    
    # 2. Section match
    heading_path = chunk.get("heading_path", "")
    content = chunk.get("content", "")

    # Direct substring in heading path
    if target_section in heading_path:
        return True

    # Extract section number like "2.3", "1.1", "2."
    m = re.match(r'^(\d+(\.\d+)*\.?)', target_section.strip())
    sec_num = m.group(1).rstrip('.') if m else ""

    # Extract core section words
    sec_text = target_section[len(sec_num):].strip() if sec_num else target_section
    # Remove leading dots or spaces
    sec_text = re.sub(r'^[.\s]+', '', sec_text)

    # If section number exists, check if heading path contains this section number
    if sec_num:
        # e.g. "2.3" in heading_path or content
        pattern = r'(^|[ >#])' + re.escape(sec_num) + r'([ .#>]|$)'
        if re.search(pattern, heading_path):
            return True
        if re.search(pattern, content[:150]):
            return True

    if sec_text and len(sec_text) >= 3:
        if sec_text in heading_path:
            return True
        # Check first line of content
        first_line = content.split('\n')[0]
        if sec_text in first_line:
            return True

    return False

async def run_retrieval_eval():
    with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"Loaded {len(dataset)} evaluation questions.")
    
    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []
    results = []

    async with async_session_maker() as db:
        for idx, item in enumerate(dataset):
            q_id = item['id']
            query = item['question']
            target_doc = item['source_doc']
            target_sec = item['source_section']

            rewritten = await model_service.rewrite_query(query, "电商平台")
            chunks, top_score = await retrieval_engine.retrieve_and_rerank(
                db=db,
                kb_id=KB_ID,
                raw_query=query,
                rewritten_query=rewritten,
                bm25_top_k=15,
                vector_top_k=15,
                rerank_top_k=5
            )

            hit_rank = None
            for r_idx, c in enumerate(chunks):
                if is_chunk_match(c, target_doc, target_sec):
                    hit_rank = r_idx + 1
                    break

            if hit_rank == 1:
                hits_at_1 += 1
            if hit_rank and hit_rank <= 3:
                hits_at_3 += 1
            if hit_rank and hit_rank <= 5:
                hits_at_5 += 1

            rr = 1.0 / hit_rank if hit_rank else 0.0
            reciprocal_ranks.append(rr)

            results.append({
                "id": q_id,
                "question": query,
                "target_doc": target_doc,
                "target_section": target_sec,
                "hit_rank": hit_rank,
                "top_score": top_score,
                "top_chunks": [
                    {
                        "doc_name": c["doc_name"],
                        "heading_path": c["heading_path"],
                        "score": c["score"]
                    }
                    for c in chunks
                ]
            })

            status = f"HIT@{hit_rank}" if hit_rank else "MISS"
            print(f"[{idx+1:02d}/50] {q_id} | {status} | Target: {target_doc} -> {target_sec}")
            if not hit_rank or hit_rank > 3:
                print(f"     Top 1: {chunks[0]['doc_name']} -> {chunks[0]['heading_path']} ({chunks[0]['score']})")

    n = len(dataset)
    hit_rate_1 = (hits_at_1 / n) * 100
    hit_rate_3 = (hits_at_3 / n) * 100
    hit_rate_5 = (hits_at_5 / n) * 100
    mrr = sum(reciprocal_ranks) / n

    print("\n" + "=" * 50)
    print("         RETRIEVAL EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total Questions : {n}")
    print(f"HitRate@1       : {hit_rate_1:.2f}% ({hits_at_1}/{n})")
    print(f"HitRate@3       : {hit_rate_3:.2f}% ({hits_at_3}/{n})")
    print(f"HitRate@5       : {hit_rate_5:.2f}% ({hits_at_5}/{n})")
    print(f"MRR             : {mrr:.4f}")
    print("=" * 50)

    with open('data/evaluation/retrieval_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "metrics": {
                "hit_rate_at_1": hit_rate_1,
                "hit_rate_at_3": hit_rate_3,
                "hit_rate_at_5": hit_rate_5,
                "mrr": mrr
            },
            "details": results
        }, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    asyncio.run(run_retrieval_eval())
