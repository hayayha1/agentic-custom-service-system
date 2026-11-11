import sqlite3

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("SELECT id, name, doc_type, content, status FROM documents WHERE name LIKE '%生鲜%'")
rows = c.fetchall()
print("Documents found:", len(rows))
for r in rows:
    print(r[0], r[1], r[2], "Content len:", len(r[3] or ""))
    print("Content preview:", (r[3] or "")[:200])

c.execute("SELECT doc_id, standard_question, answer FROM faq_items WHERE doc_id IN (SELECT id FROM documents WHERE name LIKE '%生鲜%')")
faqs = c.fetchall()
print("FAQ items:", faqs)
