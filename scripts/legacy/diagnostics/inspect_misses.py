import json

data = json.load(open('data/evaluation/retrieval_results.json', encoding='utf-8'))
for item in data['details']:
    if not item['hit_rank'] or item['hit_rank'] > 3:
        print(f"[{item['id']}] Q: {item['question']}")
        print(f"  Target: {item['target_doc']} -> {item['target_section']} | Hit Rank: {item['hit_rank']}")
        for idx, c in enumerate(item['top_chunks']):
            print(f"    Rank {idx+1}: {c['doc_name']} -> {c['heading_path']} ({c['score']})")
        print()
