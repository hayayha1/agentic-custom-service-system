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

from test_match_logic import check_hard_match, check_soft_match

hard_matches_on_ground_truth = 0
soft_matches_on_ground_truth = 0

for item in dataset:
    qid = item['id']
    target_doc = item['source_doc']
    target_sec = item['source_section']
    key_facts = item['key_facts']

    # Find the target chunk(s) in DB
    gt_chunks = [
        c for c in chunks 
        if check_hard_match(c, target_doc, target_sec)
    ]
    
    if gt_chunks:
        hard_matches_on_ground_truth += 1
        # Check if the gt chunk also covers key facts
        soft_ok = any(check_soft_match(c, key_facts) for c in gt_chunks)
        if soft_ok:
            soft_matches_on_ground_truth += 1
        else:
            print(f"[SOFT NOT COVERED ON GT CHUNK] {qid}:")
            print(f"  Facts: {key_facts}")
            print(f"  GT Chunk Heading: {gt_chunks[0]['heading_path']}")
            print(f"  GT Chunk Content Preview: {gt_chunks[0]['content'][:150]}...")
    else:
        print(f"[HARD MATCH MISSING ON GT] {qid}: {target_doc} -> {target_sec}")

print(f"\nTotal questions: {len(dataset)}")
print(f"Hard match found on DB chunks: {hard_matches_on_ground_truth}/{len(dataset)}")
print(f"Soft match satisfied on GT chunks: {soft_matches_on_ground_truth}/{len(dataset)}")
