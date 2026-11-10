import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update, and_, or_

from app.db.session import get_db
from app.models.bad_case import (
    BadCase, 
    BadCaseCluster, 
    BadCaseValidation, 
    BadCaseThresholdConfig, 
    ThresholdAuditLog, 
    ROOT_CAUSE_DICT
)
from app.models.chat_session import ChatSession, ChatMessage
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.faq import FAQItem
from app.models.knowledge_base import KnowledgeBase
from app.services.badcase_service import badcase_service
from app.core.auth import (
    get_current_user, 
    CurrentUser, 
    require_roles, 
    ROLE_ADMIN, 
    ROLE_OPERATOR, 
    ROLE_TECH_AGENT, 
    ROLE_USER,
    ROLE_PLATFORM_ADMIN,
    ROLE_TENANT_ADMIN,
    ROLE_KNOWLEDGE_MASTER,
    ROLE_SERVICE_AGENT,
    ROLE_END_USER
)

router = APIRouter(prefix="/badcases", tags=["BadCase 全生命周期治理与运营"])

# ================= Schemas =================

class UserFeedbackRequest(BaseModel):
    message_id: str = Field(..., description="被评价的AI消息ID")
    session_id: str = Field(..., description="关联会话ID")
    feedback_type: str = Field(..., description="UP(满意) 或 DOWN(差评)")
    comment: Optional[str] = Field(None, description="差评文字描述/标签")

class AgentLabelRequest(BaseModel):
    message_id: str = Field(..., description="AI消息ID")
    session_id: str = Field(..., description="会话ID")
    label_category: str = Field(..., description="WRONG_ANSWER, IRRELEVANT, OUTDATED, MISSING_KNOWLEDGE")
    notes: Optional[str] = Field(None, description="坐席补充说明")

class AdoptClusterRequest(BaseModel):
    action: str = Field(..., description="CREATE_FAQ, ADD_SIMILAR_QUERY, UPDATE_DOC")
    standard_question: Optional[str] = Field(default="", description="标准问题")
    similar_questions: List[str] = Field(default=[], description="相似问法列表")
    answer: Optional[str] = Field(default="", description="标准解答内容")
    target_doc_id: Optional[str] = Field(None, description="目标文档ID")
    target_kb_id: Optional[str] = Field(None, description="目标知识库ID")

class AdoptSingleCaseRequest(BaseModel):
    action: str = Field(..., description="CREATE_FAQ, ADD_SIMILAR_QUERY, UPDATE_DOC")
    standard_question: Optional[str] = Field(default="", description="标准问题")
    similar_questions: List[str] = Field(default=[], description="相似问法列表")
    answer: Optional[str] = Field(default="", description="标准解答内容")
    target_doc_id: Optional[str] = Field(None, description="目标文档ID")
    target_kb_id: Optional[str] = Field(None, description="目标知识库ID")

class ReviseDocRequest(BaseModel):
    doc_id: str = Field(..., description="修订的目标文档ID")
    new_content: str = Field(..., description="修订后的完整文档内容")
    change_summary: str = Field(..., description="修订说明/原因")
    case_id: Optional[str] = Field(None, description="关联的单条BadCase ID")
    cluster_id: Optional[str] = Field(None, description="关联的问题簇ID")

class ManualClusterRequest(BaseModel):
    case_ids: List[str] = Field(..., description="勾选的未成簇Case ID列表")
    cluster_name: str = Field(..., description="手动创建的问题簇代表问/名称")
    standard_question: Optional[str] = Field(None, description="标准提问描述")

class LinkKnowledgeRequest(BaseModel):
    target_doc_id: str = Field(..., description="目标知识文档ID")
    notes: Optional[str] = Field(None, description="关联说明")

class RejectClusterRequest(BaseModel):
    reject_reason: str = Field(..., description="驳回理由")

class RejectSingleCaseRequest(BaseModel):
    reject_reason: str = Field(..., description="驳回理由")

class ThresholdConfigUpdateRequest(BaseModel):
    threshold_low: float = Field(0.30, ge=0.0, le=1.0, description="无答案底线阈值")
    threshold_high: float = Field(0.70, ge=0.0, le=1.0, description="强命中高分阈值")
    short_query_len: int = Field(5, ge=1, le=20, description="短句字数门槛")
    candidate_rank_start: int = Field(4, ge=1, description="候选切片起始位")
    candidate_rank_end: int = Field(10, ge=1, description="候选切片结束位")
    context_window_rounds: int = Field(3, ge=1, le=10, description="滑动上下文轮数")

# ================= 根因字典与配置查询 =================

@router.get("/root-causes", summary="获取 7 大标准根因字典定义")
async def get_root_cause_dictionary():
    return ROOT_CAUSE_DICT

@router.get("/configs", summary="获取知识库判定阈值配置列表", dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))])
async def list_threshold_configs(db: AsyncSession = Depends(get_db)):
    stmt = select(BadCaseThresholdConfig)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.put("/configs/{kb_id}", summary="修改知识库判定阈值并记录审计日志", dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))])
async def update_threshold_config(
    kb_id: str,
    payload: ThresholdConfigUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BadCaseThresholdConfig).where(BadCaseThresholdConfig.kb_id == kb_id)
    res = await db.execute(stmt)
    cfg = res.scalars().first()

    kb = await db.get(KnowledgeBase, kb_id)
    prod = kb.product_code if kb else "SAAS_CLOUD"

    old_values = {}
    if cfg:
        old_values = {
            "threshold_low": cfg.threshold_low,
            "threshold_high": cfg.threshold_high,
            "short_query_len": cfg.short_query_len,
            "candidate_rank_start": cfg.candidate_rank_start,
            "candidate_rank_end": cfg.candidate_rank_end,
            "context_window_rounds": cfg.context_window_rounds
        }
        cfg.threshold_low = payload.threshold_low
        cfg.threshold_high = payload.threshold_high
        cfg.short_query_len = payload.short_query_len
        cfg.candidate_rank_start = payload.candidate_rank_start
        cfg.candidate_rank_end = payload.candidate_rank_end
        cfg.context_window_rounds = payload.context_window_rounds
        cfg.updated_by = current_user.username
    else:
        cfg = BadCaseThresholdConfig(
            id=str(uuid.uuid4()),
            kb_id=kb_id,
            product_code=prod,
            threshold_low=payload.threshold_low,
            threshold_high=payload.threshold_high,
            short_query_len=payload.short_query_len,
            candidate_rank_start=payload.candidate_rank_start,
            candidate_rank_end=payload.candidate_rank_end,
            context_window_rounds=payload.context_window_rounds,
            updated_by=current_user.username
        )
        db.add(cfg)

    # 记录审计日志
    audit = ThresholdAuditLog(
        id=str(uuid.uuid4()),
        kb_id=kb_id,
        operator=current_user.username or "operator",
        old_values=old_values,
        new_values=payload.model_dump(),
        changed_at=datetime.utcnow()
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "阈值配置已更新并写入审计日志", "config": cfg}

@router.get("/configs/logs", summary="获取阈值变更审计日志", dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))])
async def list_threshold_audit_logs(
    kb_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ThresholdAuditLog)
    if kb_id:
        stmt = stmt.where(ThresholdAuditLog.kb_id == kb_id)
    stmt = stmt.order_by(desc(ThresholdAuditLog.changed_at)).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()

# ================= 采集端点 (三轮动态上下文 + 自动根因初诊) =================

@router.post("/feedback", summary="用户显式点赞/差评提交 (前端对话窗口)")
async def submit_user_feedback(
    payload: UserFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    msg = await db.get(ChatMessage, payload.message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息记录不存在")

    session = await db.get(ChatSession, payload.session_id)
    if (not session or msg.session_id != session.id or
            session.tenant_id != current_user.tenant_id or
            (current_user.is_end_user and session.customer_id != current_user.user_id)):
        raise HTTPException(status_code=403, detail="无权评价该会话消息")
    product_code = session.product_code if session else "SAAS_CLOUD"

    kb_stmt = select(KnowledgeBase.id).where(KnowledgeBase.product_code == product_code,
                                           KnowledgeBase.tenant_id == session.tenant_id)
    kb_res = await db.execute(kb_stmt)
    kb_id = kb_res.scalars().first() or "b34fb60a-392c-4bb2-9e10-57539b37fed2"

    if payload.feedback_type.upper() == "DOWN":
        from app.services.agent.evolution import evolution_service
        await evolution_service.record_feedback(session.tenant_id, msg.id, payload.comment)
        # 优化上下文记忆：动态逆向回溯近三轮用户输入间的全部内容
        context_data = await badcase_service.get_sliding_context(
            db=db,
            session_id=payload.session_id,
            until_time=msg.created_at,
            max_user_rounds=3
        )

        user_query = msg.raw_query or "用户提问"
        if not msg.raw_query and context_data:
            for item in reversed(context_data):
                if item.get("role") == "user":
                    user_query = item.get("content")
                    break

        case_obj = BadCase(
            id=str(uuid.uuid4()),
            tenant_id=session.tenant_id if session and session.tenant_id else (current_user.tenant_id or "tenant_default"),
            product_code=product_code,
            kb_id=kb_id,
            session_id=payload.session_id,
            message_id=payload.message_id,
            case_type="USER_FEEDBACK",
            user_query=user_query,
            user_feedback_comment=payload.comment,
            ai_raw_response=msg.content,
            recall_sources=msg.sources or [],
            confidence_score=msg.confidence_score or 0.0,
            chat_context=context_data,
            status="PENDING"
        )

        # 实时自动执行客观测根因初诊
        rc_code, rc_name, rc_reason = await badcase_service.diagnose_case_root_cause(db, case_obj)
        case_obj.root_cause_code = rc_code
        case_obj.root_cause_name = rc_name
        case_obj.root_cause_reason = rc_reason

        db.add(case_obj)
        await db.commit()
        return {
            "status": "ok", 
            "message": "感谢您的反馈，已实时沉淀至BadCase优化池并完成根因诊断", 
            "case_id": case_obj.id,
            "root_cause": rc_name
        }

    return {"status": "ok", "message": "感谢您的好评！"}

@router.post(
    "/agent-label", 
    summary="坐席/管理员人工介入标注 (客服工作台)",
    dependencies=[Depends(require_roles([ROLE_SERVICE_AGENT, ROLE_TECH_AGENT, ROLE_TENANT_ADMIN, ROLE_ADMIN]))]
)
async def submit_agent_label(
    payload: AgentLabelRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    msg = await db.get(ChatMessage, payload.message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="目标消息记录不存在")

    session = await db.get(ChatSession, payload.session_id)
    product_code = session.product_code if session else "SAAS_CLOUD"

    kb_stmt = select(KnowledgeBase.id).where(KnowledgeBase.product_code == product_code)
    kb_res = await db.execute(kb_stmt)
    kb_id = kb_res.scalars().first() or "b34fb60a-392c-4bb2-9e10-57539b37fed2"

    context_data = await badcase_service.get_sliding_context(
        db=db,
        session_id=payload.session_id,
        until_time=msg.created_at,
        max_user_rounds=3
    )

    user_query = msg.raw_query or "用户提问"
    if not msg.raw_query and context_data:
        for item in reversed(context_data):
            if item.get("role") == "user":
                user_query = item.get("content")
                break

    case_obj = BadCase(
        id=str(uuid.uuid4()),
        tenant_id=session.tenant_id if session and session.tenant_id else (current_user.tenant_id or "tenant_default"),
        product_code=product_code,
        kb_id=kb_id,
        session_id=payload.session_id,
        message_id=payload.message_id,
        case_type="AGENT_LABEL",
        user_query=user_query,
        agent_label_category=payload.label_category,
        agent_label_notes=payload.notes,
        ai_raw_response=msg.content,
        recall_sources=msg.sources or [],
        confidence_score=msg.confidence_score or 0.0,
        chat_context=context_data,
        status="PENDING"
    )

    rc_code, rc_name, rc_reason = await badcase_service.diagnose_case_root_cause(db, case_obj)
    case_obj.root_cause_code = rc_code
    case_obj.root_cause_name = rc_name
    case_obj.root_cause_reason = rc_reason

    db.add(case_obj)
    await db.commit()
    return {
        "status": "ok", 
        "message": "坐席标注已提交并入库，已完成根因定位", 
        "case_id": case_obj.id,
        "root_cause": rc_name
    }

# ================= 全量 BadCase 池查询与单独/手动合并操作 =================

@router.get(
    "/list", 
    summary="分页多维筛选全量 BadCase 池 (含未成簇长尾与已归簇 Case)",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR, ROLE_KNOWLEDGE_MASTER, ROLE_TENANT_ADMIN]))]
)
async def list_all_badcases(
    kb_id: Optional[str] = Query(None, description="知识库ID"),
    status: Optional[str] = Query(None, description="状态: PENDING, CLUSTERED, ADOPTED, REJECTED"),
    cluster_status: Optional[str] = Query("all", description="all(全部), clustered(已成簇), unclustered(未成簇长尾)"),
    root_cause_code: Optional[str] = Query(None, description="按 7 大根因编码过滤"),
    keyword: Optional[str] = Query(None, description="用户提问关键字搜索"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BadCase)
    target_tenant = current_user.tenant_id or "tenant_default"
    stmt = stmt.where(BadCase.tenant_id == target_tenant)
    
    if current_user.role == ROLE_OPERATOR:
        assigned_kb = current_user.assigned_kb_id or "b34fb60a-392c-4bb2-9e10-57539b37fed2"
        stmt = stmt.where(BadCase.kb_id == assigned_kb)
    elif kb_id:
        stmt = stmt.where(BadCase.kb_id == kb_id)

    if status:
        stmt = stmt.where(BadCase.status == status)

    if cluster_status == "clustered":
        stmt = stmt.where(BadCase.cluster_id.is_not(None))
    elif cluster_status == "unclustered":
        stmt = stmt.where(BadCase.cluster_id.is_(None))

    if root_cause_code:
        stmt = stmt.where(BadCase.root_cause_code == root_cause_code)

    if keyword:
        stmt = stmt.where(BadCase.user_query.ilike(f"%{keyword}%"))

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(BadCase.created_at)).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    items = res.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("/manual-cluster", summary="全量池中勾选未成簇Case执行手动合并建簇", dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))])
async def manual_merge_cluster(
    payload: ManualClusterRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cluster = await badcase_service.manual_create_cluster(
        db=db,
        case_ids=payload.case_ids,
        cluster_name=payload.cluster_name,
        standard_question=payload.standard_question,
        operator_username=current_user.username or "operator"
    )
    return {
        "status": "ok",
        "message": f"成功手动合并 {cluster.case_count} 条 BadCase 为新问题簇",
        "cluster_id": cluster.id,
        "cluster_name": cluster.cluster_name,
        "root_cause": cluster.root_cause_name,
        "recommended_action": cluster.recommended_action
    }

@router.post(
    "/{case_id}/adopt", 
    summary="单条 BadCase 独立采纳并生成知识草稿",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def adopt_single_case(
    case_id: str,
    payload: AdoptSingleCaseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await db.get(BadCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="BadCase 不存在")

    target_kb_id = payload.target_kb_id or case.kb_id
    if current_user.role == ROLE_OPERATOR and target_kb_id != current_user.assigned_kb_id:
        raise HTTPException(status_code=403, detail="无权操作非本组负责的知识库")

    created_doc_id = None
    if payload.action == "CREATE_FAQ":
        doc_title = payload.standard_question or case.user_query
        doc = Document(
            kb_id=target_kb_id,
            name=f"FAQ_{doc_title[:16]}.faq",
            doc_type="FAQ",
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
            standard_question=doc_title,
            similar_questions=payload.similar_questions or [case.user_query],
            answer=payload.answer or "",
            priority=2
        )
        db.add(faq_item)

        initial_version = DocumentVersion(
            doc_id=doc.id,
            version=1,
            content=f"【标准问题】: {doc_title}\n【相似问】: {'；'.join(payload.similar_questions or [case.user_query])}\n【解答】: {payload.answer or ''}",
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
                for sq in (payload.similar_questions or [case.user_query]):
                    if sq not in curr_sim:
                        curr_sim.append(sq)
                faq_row.similar_questions = curr_sim
            created_doc_id = target_doc.id

    case.status = "ADOPTED"
    case.resolved_doc_id = created_doc_id
    case.resolved_at = datetime.utcnow()
    case.handled_by = current_user.username
    case.handling_notes = f"单条采纳治理 ({payload.action})"

    await db.commit()
    return {
        "status": "ok",
        "message": "该单条 BadCase 已采纳并提交审核",
        "doc_id": created_doc_id
    }

@router.post(
    "/{case_id}/reject", 
    summary="单条 BadCase 独立驳回",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def reject_single_case(
    case_id: str,
    payload: RejectSingleCaseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    case = await db.get(BadCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="BadCase 不存在")

    case.status = "REJECTED"
    case.reject_reason = payload.reject_reason
    case.handled_by = current_user.username
    case.handled_at = datetime.utcnow()
    case.handling_notes = f"单条驳回: {payload.reject_reason}"

    await db.commit()
    return {"status": "ok", "message": "该 Case 已驳回移出优化池"}

@router.post(
    "/revise-doc", 
    summary="针对长文本知识文档发起修订版本草稿 (场景 C 闭环)",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def revise_document_content(
    payload: ReviseDocRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ver = await badcase_service.revise_document(
        db=db,
        doc_id=payload.doc_id,
        new_content=payload.new_content,
        change_summary=payload.change_summary,
        case_id=payload.case_id,
        cluster_id=payload.cluster_id,
        operator_username=current_user.username or "operator"
    )
    return {
        "status": "ok",
        "message": f"已成功为文档创建修订版本草稿 (v{ver.version})，已进入待审核流",
        "version_id": ver.id,
        "version": ver.version
    }

# ================= 聚类引擎与簇看板 =================

@router.post(
    "/cluster/run", 
    summary="触发语义向量聚类与智能场景预判 (支持增量防重 incremental 与重建 rebuild)",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def trigger_clustering(
    kb_id: Optional[str] = Query(None, description="知识库ID"),
    mode: str = Query("incremental", description="incremental(增量防重合并) 或 rebuild(全量重新聚类)"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_kb = kb_id
    if current_user.role == ROLE_OPERATOR:
        target_kb = current_user.assigned_kb_id or "b34fb60a-392c-4bb2-9e10-57539b37fed2"

    clusters = await badcase_service.run_clustering(
        db=db,
        kb_id=target_kb,
        product_code=current_user.product_code if current_user.role == ROLE_OPERATOR else None,
        mode=mode
    )
    return {
        "status": "ok", 
        "message": f"聚类处理完成，当前共有 {len(clusters)} 个活跃待办问题簇",
        "cluster_count": len(clusters),
        "clusters": [
            {
                "id": c.id, 
                "cluster_name": c.cluster_name, 
                "case_count": c.case_count,
                "root_cause_code": c.root_cause_code,
                "root_cause_name": c.root_cause_name,
                "recommended_action": c.recommended_action
            } 
            for c in clusters
        ]
    }

@router.get(
    "/clusters", 
    summary="分页获取按热度降序的问题簇列表",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR, ROLE_KNOWLEDGE_MASTER, ROLE_TENANT_ADMIN]))]
)
async def list_clusters(
    kb_id: Optional[str] = Query(None, description="按知识库筛选"),
    status: Optional[str] = Query(None, description="状态: PENDING, ADOPTED, REJECTED"),
    root_cause_code: Optional[str] = Query(None, description="按根因筛选"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(BadCaseCluster)
    target_tenant = current_user.tenant_id or "tenant_default"
    stmt = stmt.where(BadCaseCluster.tenant_id == target_tenant)

    if current_user.role == ROLE_OPERATOR:
        assigned_kb = current_user.assigned_kb_id or "b34fb60a-392c-4bb2-9e10-57539b37fed2"
        stmt = stmt.where(BadCaseCluster.kb_id == assigned_kb)
    elif kb_id:
        stmt = stmt.where(BadCaseCluster.kb_id == kb_id)

    if status:
        stmt = stmt.where(BadCaseCluster.status == status)

    if root_cause_code:
        stmt = stmt.where(BadCaseCluster.root_cause_code == root_cause_code)

    stmt = stmt.order_by(desc(BadCaseCluster.case_count), desc(BadCaseCluster.created_at))
    res = await db.execute(stmt)
    clusters = res.scalars().all()

    # 动态为历史遗留簇补齐根因字典元数据与标准描述，并强制保持 根因 - 治理动作 - 诊断依据 强一致性
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
        await db.commit()

    return clusters

@router.get(
    "/clusters/{cluster_id}/cases", 
    summary="获取指定问题簇包含的所有原始 BadCase 明细与上下文",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def get_cluster_cases(
    cluster_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cluster = await db.get(BadCaseCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="问题簇不存在")

    if current_user.role == ROLE_OPERATOR and cluster.kb_id != current_user.assigned_kb_id:
        raise HTTPException(status_code=403, detail="无权查看非本组负责知识库的 BadCase 明细")

    stmt = select(BadCase).where(BadCase.cluster_id == cluster_id).order_by(desc(BadCase.created_at))
    res = await db.execute(stmt)
    cases = res.scalars().all()

    return {
        "cluster": cluster,
        "cases": cases
    }

@router.post(
    "/clusters/{cluster_id}/adopt", 
    summary="采纳该簇并一键生成知识草稿 (进入待审核流)",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def adopt_cluster(
    cluster_id: str,
    payload: AdoptClusterRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cluster = await db.get(BadCaseCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="问题簇不存在")

    if current_user.role == ROLE_OPERATOR and cluster.kb_id != current_user.assigned_kb_id:
        raise HTTPException(status_code=403, detail="无权操作非本组负责知识库的问题簇")

    target_kb_id = payload.target_kb_id or cluster.kb_id
    if current_user.role == ROLE_OPERATOR and target_kb_id != current_user.assigned_kb_id:
        raise HTTPException(status_code=403, detail="无权操作非本组负责的知识库")

    kb = await db.get(KnowledgeBase, target_kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="目标知识库不存在")

    created_doc_id = None

    if payload.action == "CREATE_FAQ":
        full_content = f"【标准问题】: {payload.standard_question}\n【相似问】: {'；'.join(payload.similar_questions or cluster.sample_queries or [])}\n【解答】: {payload.answer or ''}"
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
            target_doc.content = f"【标准问题】: {faq_row.standard_question}\n【相似问】: {'；'.join(curr_sim)}\n【解答】: {faq_row.answer}"
        created_doc_id = target_doc.id

    cluster.status = "ADOPTED"
    cluster.resolved_doc_id = created_doc_id
    cluster.handled_by = current_user.username
    cluster.handled_at = datetime.utcnow()

    await db.execute(
        update(BadCase)
        .where(BadCase.cluster_id == cluster_id)
        .values(
            status="ADOPTED",
            resolved_doc_id=created_doc_id,
            resolved_at=datetime.utcnow(),
            handled_by=current_user.username,
            handled_at=datetime.utcnow(),
            handling_notes="已在BadCase工作台采纳并生成知识草稿提交审核"
        )
    )

    await db.commit()

    return {
        "status": "ok",
        "message": "已成功采纳并生成知识草稿（状态为待审核 PENDING_REVIEW），请通知超管审核发布生效",
        "doc_id": created_doc_id,
        "cluster_status": "ADOPTED"
    }

@router.post(
    "/clusters/{cluster_id}/link", 
    summary="手动关联已有知识并追加相似问",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def link_existing_knowledge(
    cluster_id: str,
    payload: LinkKnowledgeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cluster = await db.get(BadCaseCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="问题簇不存在")

    target_doc = await db.get(Document, payload.target_doc_id)
    if not target_doc:
        raise HTTPException(status_code=404, detail="关联目标文档不存在")

    cluster.status = "ADOPTED"
    cluster.resolved_doc_id = target_doc.id
    cluster.target_knowledge_id = target_doc.id
    cluster.target_knowledge_title = target_doc.name
    cluster.handled_by = current_user.username
    cluster.handled_at = datetime.utcnow()

    await db.execute(
        update(BadCase)
        .where(BadCase.cluster_id == cluster_id)
        .values(
            status="ADOPTED",
            handled_by=current_user.username,
            handled_at=datetime.utcnow(),
            handling_notes=f"手动关联至已有知识《{target_doc.name}》"
        )
    )

    await db.commit()
    return {"status": "ok", "message": f"已成功关联至知识《{target_doc.name}》"}

@router.post(
    "/clusters/{cluster_id}/reject", 
    summary="驳回无效 Case 簇 (移出优化池)",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def reject_cluster(
    cluster_id: str,
    payload: RejectClusterRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cluster = await db.get(BadCaseCluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="问题簇不存在")

    cluster.status = "REJECTED"
    cluster.reject_reason = payload.reject_reason
    cluster.handled_by = current_user.username
    cluster.handled_at = datetime.utcnow()

    await db.execute(
        update(BadCase)
        .where(BadCase.cluster_id == cluster_id)
        .values(
            status="REJECTED",
            reject_reason=payload.reject_reason,
            handled_by=current_user.username,
            handled_at=datetime.utcnow()
        )
    )

    await db.commit()
    return {"status": "ok", "message": "该簇已驳回并移出待办池"}

@router.post(
    "/clusters/{cluster_id}/validate", 
    summary="效果回流验证：对该簇所有历史真实问句执行回归测试",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def validate_cluster_effect(
    cluster_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    val_res = await badcase_service.validate_cluster(db, cluster_id)
    return {
        "status": "ok",
        "message": f"回流验证执行完成，测试通过率：{val_res['pass_rate'] * 100:.1f}%",
        "data": val_res
    }

@router.get(
    "/analytics/dashboard", 
    summary="获取 BadCase 转化全景看板报表数据",
    dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_OPERATOR]))]
)
async def get_badcase_dashboard(
    kb_id: Optional[str] = Query(None, description="知识库过滤"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    target_kb = kb_id
    if current_user.role == ROLE_OPERATOR:
        target_kb = current_user.assigned_kb_id or "b34fb60a-392c-4bb2-9e10-57539b37fed2"

    case_stmt = select(func.count(BadCase.id))
    if target_kb:
        case_stmt = case_stmt.where(BadCase.kb_id == target_kb)
    total_cases = (await db.execute(case_stmt)).scalar() or 0

    type_stmt = select(BadCase.case_type, func.count(BadCase.id))
    if target_kb:
        type_stmt = type_stmt.where(BadCase.kb_id == target_kb)
    type_stmt = type_stmt.group_by(BadCase.case_type)
    type_rows = (await db.execute(type_stmt)).all()
    type_counts = {r[0]: r[1] for r in type_rows}

    # 根因分布统计
    rc_stmt = select(BadCase.root_cause_name, func.count(BadCase.id))
    if target_kb:
        rc_stmt = rc_stmt.where(BadCase.kb_id == target_kb)
    rc_stmt = rc_stmt.group_by(BadCase.root_cause_name)
    rc_rows = (await db.execute(rc_stmt)).all()
    root_cause_counts = {r[0] or "待诊断": r[1] for r in rc_rows}

    cluster_stmt = select(func.count(BadCaseCluster.id))
    if target_kb:
        cluster_stmt = cluster_stmt.where(BadCaseCluster.kb_id == target_kb)
    total_clusters = (await db.execute(cluster_stmt)).scalar() or 0

    pending_cluster_stmt = select(func.count(BadCaseCluster.id)).where(BadCaseCluster.status == "PENDING")
    if target_kb:
        pending_cluster_stmt = pending_cluster_stmt.where(BadCaseCluster.kb_id == target_kb)
    pending_clusters = (await db.execute(pending_cluster_stmt)).scalar() or 0

    adopted_cluster_stmt = select(func.count(BadCaseCluster.id)).where(BadCaseCluster.status == "ADOPTED")
    if target_kb:
        adopted_cluster_stmt = adopted_cluster_stmt.where(BadCaseCluster.kb_id == target_kb)
    adopted_clusters = (await db.execute(adopted_cluster_stmt)).scalar() or 0

    val_stmt = select(func.avg(BadCaseValidation.pass_rate), func.count(BadCaseValidation.id))
    if target_kb:
        val_stmt = val_stmt.where(BadCaseValidation.kb_id == target_kb)
    val_res = (await db.execute(val_stmt)).first()
    avg_pass_rate = round(float(val_res[0] or 0.85) * 100, 1)

    return {
        "summary": {
            "total_cases_collected": total_cases,
            "total_clusters": total_clusters,
            "pending_clusters": pending_clusters,
            "adopted_clusters": adopted_clusters,
            "average_pass_rate": avg_pass_rate
        },
        "case_type_breakdown": {
            "user_feedback": type_counts.get("USER_FEEDBACK", 0),
            "low_confidence": type_counts.get("LOW_CONFIDENCE", 0),
            "agent_label": type_counts.get("AGENT_LABEL", 0)
        },
        "root_cause_breakdown": root_cause_counts
    }
