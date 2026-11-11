import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.abspath('.'))

from app.db.session import async_session_maker
from app.services.retrieval.engine import retrieval_engine
from app.services.model_service import model_service

async def test():
    async with async_session_maker() as db:
        kb_id = "b34fb60a-392c-4bb2-9e10-57539b37fed2"
        q = "生鲜水果支持7天退货吗？"
        rewritten = await model_service.rewrite_query(q, "电商平台")
        print("Query:", q)
        print("Rewritten:", rewritten)
        
        chunks, top_score = await retrieval_engine.retrieve_and_rerank(
            db=db,
            kb_id=kb_id,
            raw_query=q,
            rewritten_query=rewritten,
            bm25_top_k=15,
            vector_top_k=15,
            rerank_top_k=5
        )
        print(f"\nTop score: {top_score}")
        for i, c in enumerate(chunks):
            print(f"Rank {i+1}: Doc={c['doc_name']} | Score={c['score']:.4f}")
            print(f"        Heading: {c['heading_path']}")
            print(f"        Content snippet: {c['content'][:100]}...")

if __name__ == '__main__':
    asyncio.run(test())
