import json
import sqlite3

def main():
    with open('data/evaluation/test_dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total evaluation questions: {len(data)}")
    source_docs = set(d['source_doc'] for d in data)
    print("Source docs in evaluation dataset:")
    for sd in sorted(source_docs):
        print(f"  - {sd}")

    print("\nSample evaluation items:")
    for i in range(5):
        d = data[i]
        print(f"[{d['id']}] Q: {d['question']}")
        print(f"  Category: {d.get('category')} | Type: {d.get('eval_type')}")
        print(f"  Source: {d['source_doc']} -> {d['source_section']}")
        print(f"  Key facts: {d['key_facts']}")
        print(f"  Ground truth: {d['ground_truth'][:60]}...")
        print()

    # Also inspect database documents and chunks in KB b34fb60a-392c-4bb2-9e10-57539b37fed2
    conn = sqlite3.connect('knowledge_base.db')
    c = conn.cursor()
    c.execute("""
        SELECT d.id, d.name, d.status, count(c.id)
        FROM documents d
        LEFT JOIN document_chunks c ON d.id = c.doc_id
        WHERE d.kb_id = 'b34fb60a-392c-4bb2-9e10-57539b37fed2'
        GROUP BY d.id
    """)
    print("Documents in target KB (b34fb60a-392c-4bb2-9e10-57539b37fed2):")
    for row in c.fetchall():
        print(f"  Doc ID: {row[0]}, Name: {row[1]}, Status: {row[2]}, Chunks: {row[3]}")

if __name__ == '__main__':
    main()
