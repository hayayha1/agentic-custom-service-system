import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select, update
from app.db.session import async_session_maker
from app.models.bad_case import BadCase, BadCaseCluster, ROOT_CAUSE_DICT
from app.services.badcase_service import badcase_service

async def repair_data():
    async with async_session_maker() as db:
        res = await db.execute(select(BadCaseCluster))
        clusters = res.scalars().all()
        print(f"Total clusters to check: {len(clusters)}")
        repaired_count = 0
        for c in clusters:
            c_cases_stmt = select(BadCase).where(BadCase.cluster_id == c.id)
            c_cases = (await db.execute(c_cases_stmt)).scalars().all()
            if c_cases:
                code, name, desc_info, dist, action, reason = badcase_service.determine_cluster_root_cause(
                    c_cases,
                    target_knowledge_title=c.target_knowledge_title
                )
                print(f"Cluster '{c.cluster_name[:20]}' -> RC: {code} ({name}), Action: {action}")
                c.root_cause_code = code
                c.root_cause_name = name
                c.root_cause_description = desc_info
                c.root_cause_distribution = dist
                c.recommended_action = action
                c.recommended_reason = reason
                repaired_count += 1
            else:
                # Fallback if no cases
                if c.root_cause_code in ROOT_CAUSE_DICT:
                    expected = ROOT_CAUSE_DICT[c.root_cause_code]["action"]
                    if c.recommended_action != expected:
                        c.recommended_action = expected
                        c.recommended_reason = f"【簇整体根因：{ROOT_CAUSE_DICT[c.root_cause_code]['name']}】系统推荐执行【{ROOT_CAUSE_DICT[c.root_cause_code]['action_label']}】。"
                        repaired_count += 1
        await db.commit()
        print(f"Repaired and aligned {repaired_count} clusters successfully!")

if __name__ == "__main__":
    asyncio.run(repair_data())
