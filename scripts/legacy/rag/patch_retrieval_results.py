import sqlite3
import json

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name, c.heading_path, c.id, c.content
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE c.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
""")
chunk_lookup = {(r[0], r[1]): (r[2], r[3]) for r in c.fetchall()}

with open('data/evaluation/retrieval_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

missing = 0
for item in data['details']:
    for chunk in item['top_chunks']:
        key = (chunk['doc_name'], chunk['heading_path'])
        if key in chunk_lookup:
            chunk['chunk_id'] = chunk_lookup[key][0]
            chunk['content'] = chunk_lookup[key][1]
        else:
            missing += 1
            print("Missing chunk content for:", key)

print(f"Patched chunks. Missing: {missing}")

with open('data/evaluation/retrieval_results.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved updated data/evaluation/retrieval_results.json")
