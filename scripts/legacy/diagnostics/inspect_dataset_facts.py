import json

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total cases: {len(data)}")
for i, d in enumerate(data):
    print(f"[{i+1:02d}] {d['id']} | Doc: {d['source_doc']} | Sec: {d['source_section']}")
    print(f"     Question : {d['question']}")
    print(f"     Key Facts: {d.get('key_facts')}")
