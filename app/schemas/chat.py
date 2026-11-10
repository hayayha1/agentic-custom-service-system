from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SourceCitation(BaseModel):
    doc_id: str
    doc_name: str
    heading: Optional[str] = None
    chunk_id: str
    snippet: Optional[str] = None
    priority: int = 1

class SuggestedQuestion(BaseModel):
    question_id: str
    title: str

class ActionButton(BaseModel):
    action: str = Field(..., description="动作标识: TRANSFER_TO_HUMAN, VIEW_ORDER 等")
    label: str = Field(..., description="按钮文字描述")
    payload: Optional[Dict[str, Any]] = None

class ChatMessageRequest(BaseModel):
    approval_id: Optional[str] = Field(None, max_length=64, description="确认卡片标识，阻止历史卡片误授权其他操作")
    product_code: str = Field(default="SAAS_CLOUD", description="业务产品编码")
    kb_id: Optional[str] = Field(None, description="可选指定知识库ID")
    customer_id: str = Field(default="user_001", description="多客户会话隔离ID")
    session_id: Optional[str] = Field(None, description="可选会话ID")
    query: str = Field(..., min_length=1, max_length=1000, description="客户原始问句")

class ChatResponse(BaseModel):
    agent_trace_id: Optional[str] = Field(None, description="Agent 执行审计轨迹编号")
    message_id: Optional[str] = Field(None, description="助手消息记录ID")
    session_id: str = Field(..., description="当前会话ID")
    reply_type: str = Field(
        ..., 
        description="决策类型: DIRECT_ANSWER | RECOMMEND_QUESTIONS | FALLBACK | BLOCKED | TRANSACTION | HUMAN_AGENT"
    )
    confidence_score: float = Field(..., description="最终置信度得分")
    content: str = Field(..., description="机器人回复主体内容")
    raw_query: str = Field(..., description="客户原始输入")
    rewritten_query: Optional[str] = Field(None, description="标准化改写后的检索问句")
    sources: List[SourceCitation] = Field(default_factory=list, description="来源溯源列表")
    suggested_questions: List[SuggestedQuestion] = Field(default_factory=list, description="中置信度下的相似推荐问题")
    business_data: Optional[Dict[str, Any]] = Field(None, description="业务卡片数据(订单/物流/退款单)")
    action_buttons: List[ActionButton] = Field(
        default_factory=lambda: [ActionButton(action="TRANSFER_TO_HUMAN", label="转接人工客服")],
        description="交互操作按钮"
    )

class ChatSessionCreate(BaseModel):
    customer_id: str
    customer_name: str
    product_code: str = "SAAS_CLOUD"
    force_new: bool = False

class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    customer_name: str
    product_code: str
    status: str
    assigned_agent: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: datetime
    created_at: datetime
    qa_score: Optional[int] = None
    qa_feedback: Optional[str] = None
    qa_tags: Optional[List[str]] = None
    qa_inspector: Optional[str] = None

class QAReviewRequest(BaseModel):
    score: int = Field(..., ge=1, le=5, description="质检评分: 1-5分")
    feedback: Optional[str] = Field(None, description="质检合规评语")
    tags: List[str] = Field(default_factory=list, description="质检问题标签")
    push_to_badcase: bool = Field(default=False, description="是否推送至BadCase待办池")
    badcase_notes: Optional[str] = Field(None, description="BadCase详细描述")

class ReassignSessionRequest(BaseModel):
    target_agent: str = Field(..., description="目标客服工号，如 agent_1028, agent_1029")
    reason: Optional[str] = Field(None, description="改派调度理由")

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    role: str
    content: str
    reply_type: Optional[str] = None
    confidence_score: float
    raw_query: Optional[str] = None
    rewritten_query: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    suggested_questions: List[Dict[str, Any]] = []
    business_data: Optional[Dict[str, Any]] = None
    created_at: datetime

class TransferHumanRequest(BaseModel):
    session_id: str
    customer_id: str
    reason: Optional[str] = "用户主动请求转接人工客服"
