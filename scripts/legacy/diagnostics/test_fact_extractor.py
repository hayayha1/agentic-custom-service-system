import json
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

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

from test_match_logic import check_hard_match

def extract_fact_requirements(fact):
    """
    Extract core requirements (keywords, numbers, thresholds) from a key fact string.
    """
    fact = fact.strip()
    
    # Pre-defined mapping for calculation/scenario-derived facts:
    scenario_rules = {
        "200元对应赔付20元": ["10%", "赔付"],
        "实际赔付5元": ["5元", "最低"],
        "实际赔偿100元": ["100元", "封顶"],
        "最多抵扣30元": ["30%", "抵扣"],
        "消耗3000积分": ["100积分", "1元"],
        "返还差额200元": ["差额", "实付"],
        "5楼不收取搬运费": ["6层", "免费"],
        "退还500元本金": ["全额", "退款"],
        "三倍赔偿1500元": ["三倍", "赔偿"],
        "共计到手2000元": ["假一赔四"]
    }
    
    if fact in scenario_rules:
        return [scenario_rules[fact]]

    # General extraction
    # Numbers/percentages/units
    nums = re.findall(r'\d+(?:个|个自然)?(?:%|元|天|小时|日|分钟|期|折)?', fact)
    
    # Chinese keywords (length >= 2)
    # Filter out stopwords
    stopwords = {"根据", "按照", "可以", "应当", "必须", "属于", "进行", "以及", "或者", "如果", "发生", "之后"}
    words = [w for w in re.findall(r'[\u4e00-\u9fa5]{2,}', fact) if w not in stopwords]
    
    reqs = []
    if nums:
        reqs.append(nums)
    if words:
        reqs.append(words)
        
    return reqs

def check_fact_in_text(fact, text):
    if fact in text:
        return True
        
    reqs = extract_fact_requirements(fact)
    if not reqs:
        return False
        
    # All requirement groups must be satisfied
    # For a list of tokens, if it's numbers: all numbers must appear in text (or normalized equivalent)
    # For a list of words: at least the most critical words must appear
    for group in reqs:
        if isinstance(group, list):
            # If all are numbers or rules
            matched_count = sum(1 for tok in group if tok in text or tok.replace("个自然日", "日").replace("个工作日", "工作日") in text)
            if matched_count < len(group) * 0.7:  # At least 70% of tokens in group
                return False
        elif isinstance(group, str):
            if group not in text:
                return False
                
    return True

print("Evaluating all GT chunks coverage with refined fact checker:")
covered_count = 0
for item in dataset:
    qid = item['id']
    target_doc = item['source_doc']
    target_sec = item['source_section']
    facts = item['key_facts']
    
    gt_chunks = [c for c in chunks if check_hard_match(c, target_doc, target_sec)]
    if not gt_chunks:
        print(f"Missing GT chunk for {qid}")
        continue
    gt = gt_chunks[0]
    
    all_facts_ok = True
    unmatched_facts = []
    for f in facts:
        if not check_fact_in_text(f, gt['content']):
            all_facts_ok = False
            unmatched_facts.append(f)
            
    if all_facts_ok:
        covered_count += 1
    else:
        print(f"Unmatched in {qid} ({target_sec}):")
        for uf in unmatched_facts:
            print(f"   fact: {uf}")

print(f"\nTotal: {covered_count}/{len(dataset)} covered by GT chunk.")
