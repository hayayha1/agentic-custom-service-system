import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from app.services.chunking.splitter import DocumentChunker

for fname in sorted(os.listdir('data/md')):
    if not fname.endswith('.md'):
        continue
    with open(os.path.join('data/md', fname), 'r', encoding='utf-8') as f:
        content = f.read()
    chunks = DocumentChunker.chunk_markdown(content, {'id': fname, 'name': fname, 'priority': 1})
    print(f"File: {fname} -> {len(chunks)} chunks")
    for c in chunks[:3]:
        print(f"   [idx {c.chunk_index}] Path: {c.heading_path}")
