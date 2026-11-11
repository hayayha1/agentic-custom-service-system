import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, c.heading_path, c.content 
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE c.content LIKE '%高空作业%' or c.content LIKE '%搬运%'
""")
rows = c.fetchall()
print(f"Chunks mentioning 高空作业 or 搬运: {len(rows)}")
for r in rows:
    print("DOC:", r[0])
    print("HEADING:", r[1])
    print("CONTENT:\n", r[2])
    print("="*40)
