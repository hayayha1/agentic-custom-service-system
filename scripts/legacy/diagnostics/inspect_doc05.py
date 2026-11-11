import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT c.heading_path, c.content 
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE d.name LIKE '%05%'
""")
rows = c.fetchall()
for h, cnt in rows:
    if "3." in h or "安装" in h or "搬运" in h:
        print("HEADING:", h)
        print("CONTENT:\n", cnt[:200])
        print("-" * 30)
