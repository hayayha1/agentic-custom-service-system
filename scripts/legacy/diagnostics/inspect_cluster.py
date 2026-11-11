import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT id, cluster_name, case_count, root_cause_code, root_cause_name, recommended_action, recommended_reason, target_knowledge_id, target_knowledge_title 
    FROM bad_case_clusters 
    WHERE id = 'fe0c481e-66d7-47fb-852c-ca5e3d9d097d'
""")
row = c.fetchone()
print('Cluster:', row)

c.execute("""
    SELECT id, user_query, root_cause_code, root_cause_name, recommended_action 
    FROM bad_cases 
    WHERE cluster_id = 'fe0c481e-66d7-47fb-852c-ca5e3d9d097d'
""")
cases = c.fetchall()
print(f'Cases ({len(cases)}):')
for cs in cases:
    print('  ', cs)
