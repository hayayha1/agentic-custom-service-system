import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import async_session_maker
from app.services.badcase_service import badcase_service

async def test_cluster():
    async with async_session_maker() as db:
        clusters = await badcase_service.run_clustering(db, similarity_threshold=0.68)
        print(f"Created {len(clusters)} clusters:")
        for c in clusters:
            print("=" * 50)
            print(f"Cluster: {c.cluster_name}")
            print(f"  Count: {c.case_count}")
            print(f"  Action: {c.recommended_action}")
            print(f"  Reason: {c.recommended_reason}")
            print(f"  Sample Queries: {c.sample_queries}")
            if c.target_knowledge_title:
                print(f"  Target: {c.target_knowledge_title} ({c.target_knowledge_id})")

if __name__ == '__main__':
    asyncio.run(test_cluster())
