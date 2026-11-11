import os

with open('app/api/v1/badcases.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update list_clusters sync logic
old_block_1 = """    # 动态为历史遗留簇补齐根因字典元数据与标准描述
    need_commit = False
    for c in clusters:
        if not c.root_cause_code:
            c_cases_stmt = select(BadCase).where(BadCase.cluster_id == c.id)
            c_cases = (await db.execute(c_cases_stmt)).scalars().all()
            if c_cases:
                code, name, desc_info, dist, action, reason = badcase_service.determine_cluster_root_cause(c_cases)
                c.root_cause_code = code
                c.root_cause_name = name
                c.root_cause_description = desc_info
                c.root_cause_distribution = dist
                if not c.recommended_action:
                    c.recommended_action = action
                    c.recommended_reason = reason
            else:
                c.root_cause_code = "RC_KNOWLEDGE_MISSING"
                c.root_cause_name = ROOT_CAUSE_DICT["RC_KNOWLEDGE_MISSING"]["name"]
                c.root_cause_description = ROOT_CAUSE_DICT["RC_KNOWLEDGE_MISSING"]["description"]
            need_commit = True
    if need_commit:
        await db.commit()"""

new_block_1 = """    # 动态为历史遗留簇补齐根因字典元数据与标准描述，并强制保持 根因 - 治理动作 - 诊断依据 强一致性
    need_commit = False
    for c in clusters:
        c_cases_stmt = select(BadCase).where(BadCase.cluster_id == c.id)
        c_cases = (await db.execute(c_cases_stmt)).scalars().all()
        if c_cases:
            code, name, desc_info, dist, action, reason = badcase_service.determine_cluster_root_cause(
                c_cases,
                target_knowledge_title=c.target_knowledge_title
            )
            if c.root_cause_code != code or c.root_cause_name != name or c.root_cause_distribution != dist:
                c.root_cause_code = code
                c.root_cause_name = name
                c.root_cause_description = desc_info
                c.root_cause_distribution = dist
                need_commit = True

            # 强一致性校验与自动纠偏：若推荐动作与根因定义脱节，或依据与根因矛盾，立即纠偏
            expected_action = ROOT_CAUSE_DICT.get(c.root_cause_code, {}).get("action", action)
            if c.recommended_action != expected_action or not c.recommended_reason or (c.root_cause_code == "RC_KNOWLEDGE_MISSING" and "场景 A" in (c.recommended_reason or "")):
                c.recommended_action = expected_action
                c.recommended_reason = reason
                need_commit = True
        elif not c.root_cause_code:
            c.root_cause_code = "RC_KNOWLEDGE_MISSING"
            c.root_cause_name = ROOT_CAUSE_DICT["RC_KNOWLEDGE_MISSING"]["name"]
            c.root_cause_description = ROOT_CAUSE_DICT["RC_KNOWLEDGE_MISSING"]["description"]
            c.recommended_action = "CREATE_FAQ"
            c.recommended_reason = "【场景 B: 知识缺失】知识库完全缺失该问题解答，建议一键采纳新建独立 FAQ。"
            need_commit = True
    if need_commit:
        await db.commit()"""

# 2. Update adopt_cluster logic to support target_kb_id and proper ADD_SIMILAR_QUERY
old_block_2 = """    kb = await db.get(KnowledgeBase, cluster.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="归属知识库不存在")

    created_doc_id = None

    if payload.action == "CREATE_FAQ":
        doc = Document(
            kb_id=cluster.kb_id,
            name=f"FAQ_{payload.standard_question[:16]}.faq",
            doc_type="FAQ",
            file_size=len(payload.answer.encode("utf-8")),
            priority=2,
            version=1,
            status="PENDING_REVIEW",
            created_by=current_user.username or "operator",
            updated_by=current_user.username or "operator"
        )
        db.add(doc)
        await db.flush()

        faq_item = FAQItem(
            doc_id=doc.id,
            kb_id=cluster.kb_id,
            standard_question=payload.standard_question,
            similar_questions=payload.similar_questions or cluster.sample_queries or [],
            answer=payload.answer,
            priority=2
        )
        db.add(faq_item)

        initial_version = DocumentVersion(
            doc_id=doc.id,
            version=1,
            content=f"【标准问题】: {payload.standard_question}\\n【相似问】: {'；'.join(payload.similar_questions)}\\n【解答】: {payload.answer}",
            metadata_snapshot={"name": doc.name, "doc_type": "FAQ", "status": "PENDING_REVIEW"},
            created_by=doc.created_by
        )
        db.add(initial_version)
        created_doc_id = doc.id

    elif payload.action == "ADD_SIMILAR_QUERY":
        target_doc = await db.get(Document, payload.target_doc_id) if payload.target_doc_id else None
        if target_doc:
            target_doc.status = "PENDING_REVIEW"
            f_stmt = select(FAQItem).where(FAQItem.doc_id == target_doc.id).limit(1)
            f_res = await db.execute(f_stmt)
            faq_row = f_res.scalars().first()
            if faq_row:
                curr_sim = faq_row.similar_questions or []
                for sq in payload.similar_questions:
                    if sq not in curr_sim:
                        curr_sim.append(sq)
                faq_row.similar_questions = curr_sim
            created_doc_id = target_doc.id"""

new_block_2 = """    target_kb_id = payload.target_kb_id or cluster.kb_id
    if current_user.role == ROLE_OPERATOR and target_kb_id != current_user.assigned_kb_id:
        raise HTTPException(status_code=403, detail="无权操作非本组负责的知识库")

    kb = await db.get(KnowledgeBase, target_kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="目标知识库不存在")

    created_doc_id = None

    if payload.action == "CREATE_FAQ":
        full_content = f"【标准问题】: {payload.standard_question}\\n【相似问】: {'；'.join(payload.similar_questions or cluster.sample_queries or [])}\\n【解答】: {payload.answer or ''}"
        doc = Document(
            kb_id=target_kb_id,
            name=f"FAQ_{payload.standard_question[:16]}.faq",
            doc_type="FAQ",
            content=full_content,
            file_size=len((payload.answer or "").encode("utf-8")),
            priority=2,
            version=1,
            status="PENDING_REVIEW",
            created_by=current_user.username or "operator",
            updated_by=current_user.username or "operator"
        )
        db.add(doc)
        await db.flush()

        faq_item = FAQItem(
            doc_id=doc.id,
            kb_id=target_kb_id,
            standard_question=payload.standard_question,
            similar_questions=payload.similar_questions or cluster.sample_queries or [],
            answer=payload.answer or "",
            priority=2
        )
        db.add(faq_item)

        initial_version = DocumentVersion(
            doc_id=doc.id,
            version=1,
            content=full_content,
            metadata_snapshot={"name": doc.name, "doc_type": "FAQ", "status": "PENDING_REVIEW"},
            created_by=doc.created_by
        )
        db.add(initial_version)
        created_doc_id = doc.id

    elif payload.action == "ADD_SIMILAR_QUERY":
        target_doc = await db.get(Document, payload.target_doc_id) if payload.target_doc_id else None
        if not target_doc:
            raise HTTPException(status_code=400, detail="未指定目标知识文档")
        
        target_doc.status = "PENDING_REVIEW"
        target_doc.updated_by = current_user.username or "operator"
        
        f_stmt = select(FAQItem).where(FAQItem.doc_id == target_doc.id).limit(1)
        f_res = await db.execute(f_stmt)
        faq_row = f_res.scalars().first()
        if faq_row:
            curr_sim = list(faq_row.similar_questions or [])
            for sq in (payload.similar_questions or cluster.sample_queries or []):
                sq_clean = sq.strip()
                if sq_clean and sq_clean not in curr_sim:
                    curr_sim.append(sq_clean)
            faq_row.similar_questions = curr_sim
            target_doc.content = f"【标准问题】: {faq_row.standard_question}\\n【相似问】: {'；'.join(curr_sim)}\\n【解答】: {faq_row.answer}"
        created_doc_id = target_doc.id"""

# Normalize \r\n to \n for matching
content_norm = content.replace('\r\n', '\n')
old_block_1_norm = old_block_1.replace('\r\n', '\n')
old_block_2_norm = old_block_2.replace('\r\n', '\n')
new_block_1_norm = new_block_1.replace('\r\n', '\n')
new_block_2_norm = new_block_2.replace('\r\n', '\n')

assert old_block_1_norm in content_norm, "old_block_1_norm not found!"
content_norm = content_norm.replace(old_block_1_norm, new_block_1_norm, 1)

assert old_block_2_norm in content_norm, "old_block_2_norm not found!"
content_norm = content_norm.replace(old_block_2_norm, new_block_2_norm, 1)

with open('app/api/v1/badcases.py', 'w', encoding='utf-8') as f:
    f.write(content_norm)

print("Successfully patched app/api/v1/badcases.py!")
