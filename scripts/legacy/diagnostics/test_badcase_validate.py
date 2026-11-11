import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.session import async_session_maker
from app.services.badcase_service import badcase_service
from app.models.bad_case import BadCaseCluster
from sqlalchemy import select

async def test_val():
    async with async_session_maker() as db:
        res = await db.execute(select(BadCaseCluster).limit(1))
        c = res.scalars().first()
        if not c:
            print("No cluster found")
            return
        print(f"Testing validation for cluster: {c.cluster_name}")
        val = await badcase_service.validate_cluster(db, c.id)
        print(f"Pass rate: {val['pass_rate'] * 100:.1f}%")
        for d in val['details']:
            print(f"  Q: {d['query']} -> passed: {d['passed']}, score: {d['top_score']}")

if __name__ == '__main__':
    asyncio.run(test_val())
