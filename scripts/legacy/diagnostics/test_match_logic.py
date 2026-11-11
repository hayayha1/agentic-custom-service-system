import re

def check_hard_match(chunk, target_doc, target_sec):
    chunk_doc = chunk.get("doc_name", "").strip()
    target_doc = target_doc.strip()
    
    # 1. doc match
    doc_match = (chunk_doc == target_doc or 
                 chunk_doc.split('.')[0] == target_doc.split('.')[0])
    if not doc_match:
        return False
        
    # 2. section match
    heading_path = chunk.get("heading_path", "").strip()
    target_sec = target_sec.strip()
    
    if target_sec in heading_path:
        return True
        
    parts = [p.strip() for p in heading_path.split(" > ") if p.strip()]
    if parts and parts[-1] == target_sec:
        return True
        
    # 章节编号匹配（如 2.3 或 1.1）
    m = re.match(r'^(\d+(\.\d+)*\.?)', target_sec)
    if m:
        sec_num = m.group(1).rstrip('.')
        pattern = r'(^|[ >#])' + re.escape(sec_num) + r'([ .#>]|$)'
        if re.search(pattern, heading_path):
            # 同时也检查部分文字重合
            sec_text = re.sub(r'^[\d.\s]+', '', target_sec)
            if any(sec_text[:4] in p for p in parts) or sec_text in heading_path:
                return True
                
    return False

def check_soft_match(chunk, key_facts):
    content = chunk.get("content", "").strip()
    if not key_facts or not content:
        return False
        
    covered_facts = []
    for fact in key_facts:
        fact = fact.strip()
        # 1. 严格子串匹配
        if fact in content:
            covered_facts.append(fact)
            continue
            
        # 2. 提取核心词（去除标点和常见停用词）
        # 例如 "赔偿比例10%" -> ["赔偿", "10%"] 或 ["10%"]
        core_tokens = [tok for tok in re.split(r'[,，。；;、\s]+', fact) if tok]
        if core_tokens and all(t in content for t in core_tokens):
            covered_facts.append(fact)
            continue
            
        # 3. 判定词与数值拆解匹配
        # 比如 "最高不超过100元封顶" -> "100元" and "封顶"
        nums = re.findall(r'\d+[%元天小时次日分门槛]*', fact)
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,}', fact)
        if nums and all(n in content for n in nums) and any(k in content for k in keywords):
            covered_facts.append(fact)
            continue

    # 当所有 key_facts 均被覆盖时，判定为软命中
    return len(covered_facts) == len(key_facts)

print("Match logic test script created.")
