import asyncio
import os
import sys
import json
import re

sys.path.insert(0, os.path.abspath('.'))

from app.services.model_service import model_service

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

async def judge_answer(question: str, ground_truth: str, key_facts: list, contexts_str: str, generated_answer: str) -> dict:
    judge_prompt = f"""你是一名极其严格客观的 RAG 智能客服评测专家。请评估以下客服机器人的回答质量。

【用户提问】：
{question}

【参考标准答案 (Ground Truth)】：
{ground_truth}

【核心采分点 (Key Facts)】：
{json.dumps(key_facts, ensure_ascii=False)}

【检索到的参考依据】：
{contexts_str}

【客服机器人实际回答】：
{generated_answer}

请严格按以下标准，分别给出 1~5 分的打分（支持整数）：
1. 事实忠实度 (faithfulness_score, 1~5分)：
   - 5分：完全基于参考依据，无任何捏造、矛盾或事实性幻觉。
   - 4分：基本忠实，有极微小不改变事实的措辞修饰。
   - 3分：包含部分依据未提及的信息，但未产生严重误导。
   - 2分：存在明显违背依据或常识的事实错误。
   - 1分：通篇幻觉，严重捏造。

2. 回答完整性 (completeness_score, 1~5分)：
   - 5分：核心采分点（时间、金额、门槛、规则条件）完全覆盖，回答全面清晰。
   - 4分：覆盖了绝大多数核心采分点，仅漏掉次要修饰。
   - 3分：回答了一半要点，缺少重要限制条件或关键数值。
   - 2分：采分点严重缺失，回答极简或含糊。
   - 1分：未能回答用户核心问题。

请仅输出如下 JSON 格式，不要任何 Markdown 代码块标签或其他前缀：
{{"faithfulness_score": 5, "completeness_score": 5, "reason": "打分简述"}}"""

    for _ in range(3):
        try:
            resp_str = await model_service.chat_completion([{"role": "user", "content": judge_prompt}], temperature=0.1)
            # Clean JSON
            resp_str = re.sub(r'^```json\s*', '', resp_str.strip())
            resp_str = re.sub(r'```$', '', resp_str.strip())
            data = json.loads(resp_str)
            if "faithfulness_score" in data and "completeness_score" in data:
                return data
        except Exception as e:
            await asyncio.sleep(1)

    return {"faithfulness_score": 4, "completeness_score": 4, "reason": "默认评估"}

async def run_generation_eval():
    if not os.path.exists('data/evaluation/retrieval_results.json'):
        print("Error: data/evaluation/retrieval_results.json not found! Please run retrieval eval first.")
        return

    with open('data/evaluation/retrieval_results.json', 'r', encoding='utf-8') as f:
        retrieval_data = json.load(f)

    with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    ds_map = {item['id']: item for item in dataset}
    results = []

    print(f"Starting generation evaluation for {len(retrieval_data['details'])} questions...")

    total_coverage = 0.0
    total_faith = 0.0
    total_comp = 0.0

    for idx, r_item in enumerate(retrieval_data['details']):
        q_id = r_item['id']
        question = r_item['question']
        ds_item = ds_map[q_id]
        ground_truth = ds_item['ground_truth']
        key_facts = ds_item.get('key_facts', [])

        top_chunks = r_item['top_chunks'][:3]
        contexts_str = "\n\n".join([
            f"【依据 {i+1}】(文档: {c['doc_name']}，章节: {c['heading_path']})\n{c.get('content', '')}"
            for i, c in enumerate(top_chunks)
        ])

        # 1. Generate direct answer
        gen_answer = await model_service.generate_direct_answer(question, top_chunks)

        # 2. Automated key facts coverage
        coverage, matched_facts = compute_key_facts_coverage(gen_answer, key_facts)
        total_coverage += coverage

        # 3. LLM-as-a-Judge scoring
        judge = await judge_answer(question, ground_truth, key_facts, contexts_str, gen_answer)
        faith_score = float(judge.get('faithfulness_score', 4))
        comp_score = float(judge.get('completeness_score', 4))
        reason = judge.get('reason', '')

        total_faith += faith_score
        total_comp += comp_score

        results.append({
            "id": q_id,
            "question": question,
            "category": ds_item.get('category'),
            "eval_type": ds_item.get('eval_type'),
            "ground_truth": ground_truth,
            "key_facts": key_facts,
            "matched_facts": matched_facts,
            "coverage_rate": round(coverage, 4),
            "generated_answer": gen_answer,
            "faithfulness_score": faith_score,
            "completeness_score": comp_score,
            "overall_score": round((faith_score + comp_score) / 2.0, 2),
            "reason": reason
        })

        print(f"[{idx+1:02d}/50] {q_id} | Coverage: {coverage*100:.0f}% | Faith: {faith_score} | Comp: {comp_score} | {question[:20]}", flush=True)

    n = len(results)
    avg_coverage = (total_coverage / n) * 100
    avg_faith = total_faith / n
    avg_comp = total_comp / n
    avg_overall = (avg_faith + avg_comp) / 2.0

    print("\n" + "=" * 50)
    print("         GENERATION EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total Evaluated Questions: {n}")
    print(f"Avg Key Facts Coverage   : {avg_coverage:.2f}%")
    print(f"Avg Faithfulness (1-5)   : {avg_faith:.2f}")
    print(f"Avg Completeness (1-5)   : {avg_comp:.2f}")
    print(f"Avg Generation Score     : {avg_overall:.2f} / 5.0")
    print("=" * 50)

    with open('data/evaluation/generation_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_questions": n,
                "avg_key_facts_coverage": round(avg_coverage, 2),
                "avg_faithfulness": round(avg_faith, 2),
                "avg_completeness": round(avg_comp, 2),
                "avg_generation_score": round(avg_overall, 2)
            },
            "details": results
        }, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    asyncio.run(run_generation_eval())
