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
chunks = c.fetchall()

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

all_targets = [(x['id'], x['source_doc'], x['source_section']) for x in dataset]

not_matched = []
for qid, doc, sec in all_targets:
    direct = [c for c in chunks if c[0] == doc and sec in (c[1] or '')]
    if not direct:
        m = re.match(r'^(\d+(\.\d+)*\.?)', sec.strip())
        sec_num = m.group(1).rstrip('.') if m else ""
        sec_text = sec[len(sec_num):].strip() if sec_num else sec
        sec_text = re.sub(r'^[.\s]+', '', sec_text)
        
        matches = [c for c in chunks if c[0] == doc and (
            (sec_num and re.search(r'(^|[ >#])' + re.escape(sec_num) + r'([ .#>]|$)', c[1] or '')) or
            (sec_text and sec_text in (c[1] or ''))
        )]
        if not matches:
            not_matched.append((qid, doc, sec))
        else:
            print(f"[RELAXED MATCH] {qid}: {sec} -> matched {matches[0][1]}")

print(f"\nTotal tested: {len(all_targets)}")
print(f"Not matched in entire DB: {len(not_matched)}")
for qid, doc, sec in not_matched:
    print(f"  {qid}: {doc} -> {sec}")
