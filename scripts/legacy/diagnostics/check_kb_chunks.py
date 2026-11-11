import sqlite3

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()

c.execute("SELECT id, name, doc_type, status FROM documents WHERE kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'")
docs = c.fetchall()
print(f"Docs in KB b34fb60a-392c-4bb2-9e10-57539b37fed2: {len(docs)}")
for d in docs:
    c.execute("SELECT count(*) FROM document_chunks WHERE doc_id = ?", (d[0],))
    cnt = c.fetchone()[0]
    print(f"Doc {d[0]} | {d[1]} | {d[2]} | {d[3]} | Chunks: {cnt}")

c.execute("SELECT count(*) FROM document_chunks WHERE kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'")
total_chunks = c.fetchone()[0]
print(f"Total chunks in KB: {total_chunks}")
