import sqlite3
import difflib

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("SELECT name, content FROM documents WHERE kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'")
for name, content in c.fetchall():
    print("Doc name in DB:", name, "len:", len(content) if content else 0)
