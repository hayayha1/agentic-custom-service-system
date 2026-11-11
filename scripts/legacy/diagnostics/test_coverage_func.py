import re
import jieba

def compute_key_facts_coverage(answer: str, key_facts: list) -> tuple:
    if not key_facts:
        return 1.0, []
    
    answer_clean = re.sub(r'[\s\*\#\_\:\：\，\,\。\.]+', '', answer.lower())
    matched = []
    
    for fact in key_facts:
        fact_clean = re.sub(r'[\s\*\#\_\:\：\，\,\。\.]+', '', fact.lower())
        # 1. Exact match
        if fact_clean in answer_clean:
            matched.append(fact)
            continue
        
        # 2. Token / Jieba overlap
        words = [w for w in jieba.cut(fact) if len(w) >= 2]
        if words and all(w in answer for w in words):
            matched.append(fact)
            continue
        
        # 3. Numbers & core units check
        nums = re.findall(r'\d+', fact)
        if nums and all(n in answer for n in nums):
            # Check non-digit words
            non_digits = [w for w in words if not w.isdigit()]
            if not non_digits or any(w in answer for w in non_digits):
                matched.append(fact)
                continue

        # 4. High character overlap (>= 75%)
        overlap = sum(1 for ch in fact_clean if ch in answer_clean)
        if overlap / max(len(fact_clean), 1) >= 0.75:
            matched.append(fact)
            continue

    coverage = len(matched) / len(key_facts)
    return coverage, matched

ans = "签收商品次日零时 00:00:00 起算，满168小时为7个自然日"
facts = ['签收次日零时', '满168小时', '7个自然日']
cov, matched = compute_key_facts_coverage(ans, facts)
print(f"Coverage: {cov*100:.1f}%, Matched: {matched}")
