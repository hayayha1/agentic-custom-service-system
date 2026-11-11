import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("SELECT id, name, product_code, status FROM knowledge_bases")
kbs = c.fetchall()
print("Knowledge Bases:")
for kb in kbs:
    print(kb)

c.execute("SELECT id, kb_id, name, doc_type, status, file_size FROM documents")
docs = c.fetchall()
print(f"\nDocuments ({len(docs)}):")
for d in docs:
    print(d)

