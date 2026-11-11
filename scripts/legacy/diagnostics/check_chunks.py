import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT doc_id, chunk_index, heading_path, length(content), metadata
    FROM document_chunks
    WHERE kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
""")
rows = c.fetchall()
print(f"Total chunks in KB: {len(rows)}")
for r in rows[:15]:
    meta = json.loads(r[4]) if r[4] else {}
    print(f"Doc: {meta.get('doc_name')} | Path: {r[2]} | Len: {r[3]}")
