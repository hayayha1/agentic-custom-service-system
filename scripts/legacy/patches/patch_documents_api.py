with open('app/api/v1/documents.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """    content = doc.content
    if not content:
        v_stmt = select(DocumentVersion).where(DocumentVersion.doc_id == doc.id).order_by(DocumentVersion.version.desc()).limit(1)
        v = (await db.execute(v_stmt)).scalars().first()
        if v and v.content:
            content = v.content
        elif doc.doc_type == "FAQ":
            f_stmt = select(FAQItem).where(FAQItem.doc_id == doc.id).limit(1)
            f = (await db.execute(f_stmt)).scalars().first()
            if f:
                content = f"【标准问题】: {f.standard_question}\\n【解答】: {f.answer}"

    stmt_chunks = select(DocumentChunk).where(DocumentChunk.doc_id == doc_id).order_by(DocumentChunk.chunk_index.asc())
    c_res = await db.execute(stmt_chunks)
    chunks = c_res.scalars().all()

    doc_resp = DocumentResponse.model_validate(doc)
    doc_resp.content = content or ""

    return {
        "doc": doc_resp,
        "content": content or "",
        "chunk_count": len(chunks),"""

new_block = """    content = doc.content
    faq_data = None
    if doc.doc_type == "FAQ":
        f_stmt = select(FAQItem).where(FAQItem.doc_id == doc.id).limit(1)
        f = (await db.execute(f_stmt)).scalars().first()
        if f:
            faq_data = {
                "standard_question": f.standard_question,
                "similar_questions": f.similar_questions or [],
                "answer": f.answer
            }
            if not content:
                content = f"【标准问题】: {f.standard_question}\\n【相似问法】: {'；'.join(f.similar_questions or [])}\\n【标准解答】: {f.answer}"

    if not content:
        v_stmt = select(DocumentVersion).where(DocumentVersion.doc_id == doc.id).order_by(DocumentVersion.version.desc()).limit(1)
        v = (await db.execute(v_stmt)).scalars().first()
        if v and v.content:
            content = v.content

    stmt_chunks = select(DocumentChunk).where(DocumentChunk.doc_id == doc_id).order_by(DocumentChunk.chunk_index.asc())
    c_res = await db.execute(stmt_chunks)
    chunks = c_res.scalars().all()

    doc_resp = DocumentResponse.model_validate(doc)
    doc_resp.content = content or ""

    return {
        "doc": doc_resp,
        "content": content or "",
        "faq": faq_data,
        "chunk_count": len(chunks),"""

text_norm = text.replace('\r\n', '\n')
old_norm = old_block.replace('\r\n', '\n')
new_norm = new_block.replace('\r\n', '\n')

assert old_norm in text_norm, "old_norm not found in documents.py"
text_norm = text_norm.replace(old_norm, new_norm, 1)

with open('app/api/v1/documents.py', 'w', encoding='utf-8') as f:
    f.write(text_norm)

print("Successfully updated app/api/v1/documents.py!")
