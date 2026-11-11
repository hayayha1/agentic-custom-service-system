import sqlite3

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, count(c.id), sum(case when c.embedding is not null then 1 else 0 end)
    FROM documents d
    LEFT JOIN document_chunks c ON d.id = c.doc_id
    WHERE d.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
    GROUP BY d.id
""")
for r in c.fetchall():
    print(r)
