import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/evaluation/rag_cache/cache_all_retrievals.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

from eval_strategies_summary import check_hard_match, check_soft_match, composite_ids

for item in dataset:
    qid = item['id']
    target_doc = item['source_doc']
    target_sec = item['source_section']
    key_facts = item['key_facts']
    is_comp = qid in composite_ids or "复合" in item.get("eval_type", "")
    
    chunks = item['retrieved_chunks']
    h_ranks = [r+1 for r, c in enumerate(chunks[:5]) if check_hard_match(c, target_doc, target_sec)]
    s_ranks = [r+1 for r, c in enumerate(chunks[:5]) if check_soft_match(c, key_facts, is_comp)]
    
    h_top3 = any(r <= 3 for r in h_ranks)
    s_top3 = any(r <= 3 for r in s_ranks)
    
    # If different or both missed
    if not h_top3 or not s_top3 or (h_top3 != s_top3):
        print(f"[{qid}] HardTop3: {h_top3} (ranks {h_ranks}), SoftTop3: {s_top3} (ranks {s_ranks})")
        print(f"       Q: {item['question']}")
        print(f"       Target: {target_doc} -> {target_sec}")
        print(f"       Top 1: {chunks[0]['doc_name']} -> {chunks[0]['heading_path'][:40]}")
        print(f"       Top 2: {chunks[1]['doc_name']} -> {chunks[1]['heading_path'][:40]}")
        print(f"       Top 3: {chunks[2]['doc_name']} -> {chunks[2]['heading_path'][:40]}")
        print("-" * 50)
