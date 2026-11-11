import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, c.heading_path, c.content 
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE d.name LIKE '%03%'
""")
rows = c.fetchall()
for r in rows:
    print("DOC:", r[0])
    print("HEADING:", r[1])
    print("CONTENT:\n", r[2][:300])
    print("="*40)
