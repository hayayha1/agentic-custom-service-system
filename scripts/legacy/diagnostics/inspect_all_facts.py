import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

for x in dataset:
    print(f"{x['id']} | {x['source_doc']} | {x['source_section']} | {x['key_facts']}")
