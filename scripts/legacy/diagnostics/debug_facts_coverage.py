import json
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('knowledge_base.db')
c = conn.cursor()
c.execute("""
    SELECT d.name as doc_name, c.heading_path, c.content 
    FROM document_chunks c
    JOIN documents d ON c.doc_id = d.id
    WHERE c.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
""")
chunks = [
    {"doc_name": row[0], "heading_path": row[1] or "", "content": row[2] or ""}
    for row in c.fetchall()
]

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for item in dataset:
    qid = item['id']
    target_doc = item['source_doc']
    target_sec = item['source_section']
    facts = item['key_facts']
    
    # find corresponding chunk
    gt_chunks = [c for c in chunks if c['doc_name'] == target_doc and (target_sec in c['heading_path'] or any(p in c['heading_path'] for p in target_sec.split() if len(p) > 2))]
    if not gt_chunks:
        print(f"GT not found for {qid}")
        continue
    gt = gt_chunks[0]
    
    print(f"\n--- {qid} ---")
    print(f"Target: {target_doc} | {target_sec}")
    for fact in facts:
        # direct in
        direct = fact in gt['content']
        # sub tokens
        tokens = [t for t in re.split(r'[,，。；;、\s]+', fact) if t]
        tok_match = all(t in gt['content'] for t in tokens)
        print(f"  Fact: '{fact}' -> direct: {direct}, tokens: {tok_match}")
