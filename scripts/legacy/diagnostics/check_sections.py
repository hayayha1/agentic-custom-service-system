import json

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sections = set((d['source_doc'], d['source_section']) for d in data)
print(f"Total unique doc-section pairs: {len(sections)}")
for doc, sec in sorted(sections):
    print(f"  {doc} -> {sec}")
