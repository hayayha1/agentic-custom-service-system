"""Native function-calling contracts. Identity is injected by the server only."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


OrderID = Annotated[str, Field(pattern=r"^ORD[-_][A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*$", max_length=80)]


class OrderQuery(ToolArguments):
    order_id: OrderID | None = Field(default=None, description="用户提供或已验证的订单号，未提供时查询本人列表")


class OrderRequired(ToolArguments):
    order_id: OrderID = Field(description="当前客户名下的目标订单编号")


class RefundArguments(OrderRequired):
    refund_reason: str = Field(min_length=2, max_length=500, description="用户明确提供的退款原因")
    refund_amount: float | None = Field(default=None, gt=0, le=10000000, allow_inf_nan=False,
                                      description="用户要求的退款金额，未提供则以订单金额为准")


class AddressArguments(OrderRequired):
    new_address: str = Field(min_length=5, max_length=300, description="用户提供的新收货地址")
    contact_phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$", description="收件人手机号")


class CancelArguments(OrderRequired):
    cancel_reason: str | None = Field(default=None, min_length=1, max_length=300, description="取消原因")


class InvoiceArguments(OrderRequired):
    invoice_title: str = Field(min_length=2, max_length=200, description="用户提供的发票抬头，禁止臆造")
    tax_id: str | None = Field(default=None, pattern=r"^[0-9A-Z]{15,20}$", description="纳税人识别号")
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
                             description="电子发票接收邮箱")


class KnowledgeArguments(ToolArguments):
    query: str = Field(min_length=1, max_length=2000, description="需要检索的政策或产品问题")


ARGUMENT_MODELS = {
    "query_orders": OrderQuery,
    "query_logistics": OrderQuery,
    "query_refund_status": OrderQuery,
    "apply_refund": RefundArguments,
    "update_shipping_address": AddressArguments,
    "cancel_unpaid_order": CancelArguments,
    "apply_invoice": InvoiceArguments,
    "expedite_shipping": OrderRequired,
    "knowledge_retriever": KnowledgeArguments,
}


class RequestIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)
    tenant_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    role: str

    def can_act(self):
        return (self.role in {"user", "end_user"} and self.customer_id == self.user_id) or self.role in {
            "tenant_admin", "admin", "service_agent", "tech_agent"}


class Observation(BaseModel):
    status: Literal["success", "validation_error", "denied", "approval_required", "unavailable", "failed", "uncertain"]
    tool_name: str
    message: str
    data: dict = Field(default_factory=dict)
    card_data: dict | None = None
    retryable: bool = False

    @property
    def success(self):
        return self.status == "success"


def function_schema(name, description, model):
    return {"type": "function", "function": {"name": name, "description": description,
                                               "parameters": model.model_json_schema()}}
