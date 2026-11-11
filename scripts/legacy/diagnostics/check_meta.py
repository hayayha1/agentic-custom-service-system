import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, c.heading_path, c.metadata
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE c.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
    LIMIT 10
""")
for r in c.fetchall():
    meta = json.loads(r[2]) if r[2] else {}
    print(f"Doc: {r[0]} | Meta doc_name: {meta.get('doc_name')} | Path: {r[1]}")
