import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import async_session_maker
from app.services.retrieval.engine import retrieval_engine
from app.services.model_service import model_service

KB_ID = "b34fb60a-392c-4bb2-9e10-57539b37fed2"

async def collect_all_retrievals():
    with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    print(f"Loaded {len(dataset)} evaluation questions.")
    
    all_records = []
    async with async_session_maker() as db:
        for idx, item in enumerate(dataset):
            q_id = item['id']
            query = item['question']
            
            # Query rewrite
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
            
            record = {
                "id": q_id,
                "category": item.get("category", ""),
                "eval_type": item.get("eval_type", ""),
                "question": query,
                "rewritten_query": rewritten,
                "ground_truth": item.get("ground_truth", ""),
                "source_doc": item["source_doc"],
                "source_section": item["source_section"],
                "key_facts": item["key_facts"],
                "top_score": top_score,
                "retrieved_chunks": [
                    {
                        "rank": r_idx + 1,
                        "doc_name": c["doc_name"],
                        "heading_path": c.get("heading_path", ""),
                        "score": round(float(c.get("score", 0.0)), 4),
                        "content": c["content"],
                        "doc_id": c.get("doc_id", ""),
                        "chunk_id": c.get("id", "")
                    }
                    for r_idx, c in enumerate(chunks)
                ]
            }
            all_records.append(record)
            print(f"[{idx+1:02d}/50] {q_id}: Retrieved {len(chunks)} chunks, Top1: {chunks[0]['doc_name']} -> {chunks[0]['heading_path'][:40]} (Score: {top_score:.4f})")

    with open('data/evaluation/rag_cache/cache_all_retrievals.json', 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print("Done caching all retrievals.")

if __name__ == '__main__':
    asyncio.run(collect_all_retrievals())
