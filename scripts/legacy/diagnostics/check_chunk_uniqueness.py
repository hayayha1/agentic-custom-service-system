import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, c.heading_path, count(*)
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE c.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
    GROUP BY d.name, c.heading_path
""")
duplicates = [r for r in c.fetchall() if r[2] > 1]
print("Duplicate (doc_name, heading_path) counts:", len(duplicates))
if duplicates:
    for d in duplicates[:5]:
        print(d)
