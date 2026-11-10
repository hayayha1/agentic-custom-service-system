from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.retrieval.engine import retrieval_engine
from app.services.model_service import model_service

class KnowledgeCollaboratorResult:
    def __init__(
        self,
        content: str,
        sources: List[Dict[str, Any]],
        top_score: float,
        reply_type: str,
        suggested_questions: List[Dict[str, Any]] = None
    ):
        self.content = content
        self.sources = sources
        self.top_score = top_score
        self.reply_type = reply_type
        self.suggested_questions = suggested_questions or []

class KnowledgeCollaboratorTool:
    """
    知识协同工具（RAG 降维接入）：
    将原有的 BM25 + 密集向量检索 + Rerank 引擎包装为 Agent 可按需自主调用的标准工具。
    具备事实交叉校验与优先级仲裁能力。
    """

    async def execute_retrieval(
        self,
        db: AsyncSession,
        kb_id: str,
        raw_query: str,
        rewritten_query: str,
        kb_config: Dict[str, Any],
        live_business_context: Optional[Dict[str, Any]] = None
    ) -> KnowledgeCollaboratorResult:
        """执行知识协同检索与答案生成"""
        bm25_top_k = kb_config.get("bm25_top_k", 15)
        vector_top_k = kb_config.get("vector_top_k", 15)
        rerank_top_k = kb_config.get("rerank_top_k", 3)
        th_direct = kb_config.get("threshold_direct", 0.80)
        th_clarify = kb_config.get("threshold_clarify", 0.50)

        chunks, top_score = await retrieval_engine.retrieve_and_rerank(
            db=db,
            kb_id=kb_id,
            raw_query=raw_query,
            rewritten_query=rewritten_query or raw_query,
            bm25_top_k=bm25_top_k,
            vector_top_k=vector_top_k,
            rerank_top_k=rerank_top_k
        )

        sources = []
        for c in chunks:
            snippet = c.get("content", "")
            snippet_summary = snippet[:120] + "..." if len(snippet) > 120 else snippet
            sources.append({
                "doc_id": c.get("doc_id"),
                "doc_name": c.get("doc_name"),
                "heading": c.get("heading_path") or "正文段落",
                "chunk_id": c.get("chunk_id"),
                "snippet": snippet_summary,
                "priority": c.get("priority", 1)
            })

        # 1. 高置信度直接回答
        if top_score >= th_direct and chunks:
            # Extractive grounding prevents generated policy details or unsupported
            # claims that an arbitrary order qualifies for a retrieved policy.
            from app.services.agent.safety import grounded_answer
            answer = grounded_answer(chunks)

            return KnowledgeCollaboratorResult(
                content=answer,
                sources=sources,
                top_score=top_score,
                reply_type="DIRECT_ANSWER"
            )

        # 2. 中置信度反向推荐相似问
        elif top_score >= th_clarify:
            suggested = []
            for idx, c in enumerate(chunks[:3]):
                meta = c.get("metadata", {})
                title = meta.get("standard_question")
                if not title:
                    first_line = c.get("content", "").split("\n")[0].replace("#", "").strip()
                    title = first_line[:30] if first_line else f"相关参考内容 {idx+1}"
                suggested.append({
                    "question_id": f"q_{idx+1}",
                    "title": title
                })

            return KnowledgeCollaboratorResult(
                content="您是不是想咨询以下问题？您可以直接点击下方卡片快速查看详细解答：",
                sources=[],
                top_score=top_score,
                reply_type="RECOMMEND_QUESTIONS",
                suggested_questions=suggested
            )

        # 3. 低置信度兜底
        else:
            return KnowledgeCollaboratorResult(
                content="抱歉，暂时没有检索到与您的问题高度匹配的知识库内容。您可以尝试简化问法、补充关键词，或者点击下方按钮直接转接人工客服为您处理。",
                sources=[],
                top_score=top_score,
                reply_type="FALLBACK"
            )

knowledge_tool = KnowledgeCollaboratorTool()
