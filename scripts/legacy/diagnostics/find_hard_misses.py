import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/evaluation/rag_cache/cache_all_retrievals.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

from eval_strategies_summary import check_hard_match

print("Questions where Hard Match is NOT in Top-3:")
for item in dataset:
    qid = item['id']
    target_doc = item['source_doc']
    target_sec = item['source_section']
    chunks = item['retrieved_chunks']
    h_ranks = [r+1 for r, c in enumerate(chunks[:5]) if check_hard_match(c, target_doc, target_sec)]
    if not any(r <= 3 for r in h_ranks):
        print(f"[{qid}] Hit ranks: {h_ranks}")
        print(f"       Q: {item['question']}")
        print(f"       Target: {target_doc} -> {target_sec}")
        for r_idx, c in enumerate(chunks[:5]):
            print(f"       Rank {r_idx+1}: {c['doc_name']} | {c['heading_path'][:40]} | Score: {c['score']}")
        print("-" * 50)
