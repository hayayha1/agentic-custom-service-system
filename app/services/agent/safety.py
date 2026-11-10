"""Deterministic input boundaries, conservative grounding and recursive PII masking."""
import re

from app.core.config import settings


def input_violation(query):
    if not query.strip() or len(query) > 10000:
        return "输入为空或超过允许长度"
    if any(word in query for word in settings.SENSITIVE_WORDS):
        return "包含不合规内容"
    if re.search(r"忽略.{0,12}(之前|所有|系统).{0,8}(指令|规则|提示)|"
                 r"(泄露|输出|显示).{0,8}(系统提示|API.?KEY|密钥)|"
                 r"ignore.{0,20}(previous|system|all).{0,12}(instructions|rules)|"
                 r"(绕过|跳过).{0,8}(审批|确认|权限)|越狱|jailbreak", query, re.I):
        return "检测到提示词注入或绕过权限指令"
    return None


def redact(value):
    if isinstance(value, dict):
        return {k: ("[已隐藏]" if re.search(r"password|secret|api_key|authorization", k, re.I)
                    else redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if not isinstance(value, str):
        return value
    value = re.sub(r"(?<!\d)(\d{6})\d{8}(\d{3}[\dXx])(?!\d)", r"\1********\2", value)
    value = re.sub(r"(?<!\d)(1[3-9]\d)\d{4}(\d{4})(?!\d)", r"\1****\2", value)
    value = re.sub(r"(?<![A-Za-z0-9])(\d{4})\d{8,15}(\d{4})(?!\d)", r"\1********\2", value)
    value = re.sub(r"\b([\w.+-])[^\s@]*@([\w.-]+\.[a-zA-Z]{2,})\b", r"\1***@\2", value)
    return value


def confirmation_answer(query):
    """Only unambiguous, entire utterances authorize a frozen operation."""
    text = re.sub(r"[\s，,。.!！?？✅❌]", "", query).lower()
    if text in {"取消", "不要了", "算了", "放弃", "暂不", "不需要", "no", "不确认", "暂不取消",
                "取消办理退款", "取消退款", "取消修改地址", "取消修改", "不同意", "不要确认"}:
        return False
    if text in {"确认", "确定", "同意", "是的", "yes", "ok", "确认办理", "好的确认办理",
                "确认办理退款", "确认申请退款", "确认修改地址", "确认取消订单", "确认修改"}:
        return True
    return None


def grounded_answer(chunks):
    """Extractive output is a hard factual boundary, not an LLM self-assessment."""
    return "\n\n".join(c.get("content", "") for c in chunks[:3])[:5000]
