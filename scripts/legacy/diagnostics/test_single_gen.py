import asyncio
import os
import sys
import json
sys.path.insert(0, os.path.abspath('.'))

from app.services.model_service import model_service
from scripts.legacy.diagnostics.test_generation_all import compute_key_facts_coverage

async def test():
    with open('data/evaluation/retrieval_results.json', encoding='utf-8') as f:
        data = json.load(f)
    with open('data/evaluation/test_dataset.json', encoding='utf-8') as f:
        ds = json.load(f)
    
    item = data['details'][1]
    ds_item = ds[1]
    q = item['question']
    top_chunks = item['top_chunks'][:3]
    print("Question:", q)
    print("Key facts:", ds_item['key_facts'])
    print("Chunks count:", len(top_chunks))
    print("Chunk 1 snippet:", top_chunks[0]['content'][:150])
    
    ans = await model_service.generate_direct_answer(q, top_chunks)
    print("\nGenerated answer:\n", ans)
    cov, matched = compute_key_facts_coverage(ans, ds_item['key_facts'])
    print(f"\nCoverage: {cov*100:.1f}%, Matched: {matched}")

if __name__ == '__main__':
    asyncio.run(test())
