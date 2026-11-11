import os
import sys
import shutil
import asyncio
import sqlite3
import json

sys.path.insert(0, os.path.abspath('.'))

from app.services.chunking.splitter import DocumentChunker
from app.services.model_service import model_service

KB_ID = "b34fb60a-392c-4bb2-9e10-57539b37fed2"
MD_DIR = "data/md"

async def reindex():
    print("Backing up database...")
    shutil.copyfile("knowledge_base.db", "knowledge_base.db.bak")

    conn = sqlite3.connect("knowledge_base.db")
    c = conn.cursor()

    # Find existing docs for this KB
    c.execute("SELECT id FROM documents WHERE kb_id = ?", (KB_ID,))
    old_doc_ids = [r[0] for r in c.fetchall()]

    print(f"Deleting {len(old_doc_ids)} existing docs and chunks for KB {KB_ID}...")
    c.execute("DELETE FROM document_chunks WHERE kb_id = ?", (KB_ID,))
    c.execute("DELETE FROM document_versions WHERE doc_id IN ({})".format(
        ",".join("?" * len(old_doc_ids)) if old_doc_ids else "''"
    ), old_doc_ids)
    c.execute("DELETE FROM documents WHERE kb_id = ?", (KB_ID,))
    conn.commit()

    md_files = sorted([f for f in os.listdir(MD_DIR) if f.endswith(".md")])
    print(f"Found {len(md_files)} markdown files in {MD_DIR}: {md_files}")

    total_chunks = 0
    for fname in md_files:
        fpath = os.path.join(MD_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        import uuid
        doc_id = str(uuid.uuid4())
        doc_info = {"id": doc_id, "name": fname, "priority": 1}

        # Create Document record
        c.execute("""
            INSERT INTO documents (id, kb_id, name, doc_type, file_size, priority, version, status, created_by, updated_by, created_at, updated_at, content)
            VALUES (?, ?, ?, 'MD', ?, 1, 1, 'ACTIVE', 'admin', 'admin', datetime('now'), datetime('now'), ?)
        """, (doc_id, KB_ID, fname, len(content.encode('utf-8')), content))

        # Create initial DocumentVersion
        c.execute("""
            INSERT INTO document_versions (id, doc_id, version, content, metadata_snapshot, created_by, created_at)
            VALUES (?, ?, 1, ?, ?, 'admin', datetime('now'))
        """, (str(uuid.uuid4()), doc_id, content, json.dumps({"name": fname, "doc_type": "MD"})))

        raw_chunks = DocumentChunker.chunk_markdown(content, doc_info)
        print(f"File {fname}: parsed into {len(raw_chunks)} chunks. Generating embeddings...")

        for idx, rc in enumerate(raw_chunks):
            emb = await model_service.get_embedding(rc.content)
            chunk_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO document_chunks (id, kb_id, doc_id, chunk_index, content, embedding, heading_path, priority, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, datetime('now'))
            """, (
                chunk_id,
                KB_ID,
                doc_id,
                rc.chunk_index,
                rc.content,
                json.dumps(emb) if emb else None,
                rc.heading_path,
                json.dumps(rc.metadata, ensure_ascii=False)
            ))
            total_chunks += 1

        conn.commit()
        print(f"File {fname} saved successfully.")

    c.execute("""
        UPDATE knowledge_bases
        SET doc_count = ?, chunk_count = ?, updated_at = datetime('now')
        WHERE id = ?
    """, (len(md_files), total_chunks, KB_ID))
    conn.commit()
    conn.close()

    print(f"\nAll done! Total documents: {len(md_files)}, Total chunks: {total_chunks}")

if __name__ == "__main__":
    asyncio.run(reindex())
