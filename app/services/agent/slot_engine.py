import re
from typing import Dict, Any, List, Optional, Tuple
from app.services.agent.memory import memory_hub

class SlotExtractionResult:
    def __init__(self, slots: Dict[str, Any], is_complete: bool, missing_slots: List[str], clarification_prompt: str = "", clarification_card: Optional[Dict[str, Any]] = None):
        self.slots = slots
        self.is_complete = is_complete
        self.missing_slots = missing_slots
        self.clarification_prompt = clarification_prompt
        self.clarification_card = clarification_card

class SlotEngine:
    """动态槽位抽取与主动反向追问引擎"""

    def __init__(self):
        # 常见退款原因特征词
        self.refund_reason_keywords = [
            "七天无理由", "功能不符合", "算力配额不足", "拍错了", "买重了",
            "质量问题", "不想用了", "价格太贵", "不满意", "误购", "测试"
        ]

    def extract_slots_from_text(
        self,
        query: str,
        customer_id: str,
        session_id: str,
        action_type: str = "",
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """从用户文本与上下文提取业务槽位参数"""
        extracted = {}

        # 1. 抽取订单号
        # 正则匹配 ORD-20261025-8891 或 ORD_20261025 或 ORD-AUTO-xxx
        order_match = re.search(r"(ORD[-_][A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)?)", query, re.IGNORECASE)
        if order_match:
            extracted["order_id"] = order_match.group(1).upper()
        else:
            # 代词消解：如果用户说“这个订单”、“刚才那单”、“最新这笔”，从工作记忆或最近订单补全
            if use_memory and any(w in query for w in ["这个", "这单", "刚才", "第一笔", "最新", "那单"]):
                ref_order = memory_hub.get_referenced_entity(session_id, "order_id")
                if ref_order:
                    extracted["order_id"] = ref_order
                else:
                    # 尝试从长期画像获取最近订单
                    prof = memory_hub.get_customer_profile(customer_id)
                    recent_ord = prof.get("recent_order", {})
                    if recent_ord.get("order_id"):
                        extracted["order_id"] = recent_ord.get("order_id")

        # 2. 抽取手机号
        phone_match = re.search(r"(1[3-9]\d{9})", query)
        if phone_match:
            extracted["contact_phone"] = phone_match.group(1)

        # 3. 抽取退款原因
        for rk in self.refund_reason_keywords:
            if rk in query:
                extracted["refund_reason"] = rk
                break
        if "refund_reason" not in extracted:
            reason_match = re.search(r"原因(?:是|为)?[:：\s]?([^\s，。,]+)", query)
            if reason_match:
                extracted["refund_reason"] = reason_match.group(1).strip()

        # 4. 抽取收件地址
        addr_match = re.search(r"(?:地址|寄到|送去|改到)(?:是|为)?[:：\s]?([^\s，。]+(?:省|市|区|路|道|号|大厦|园)[^\s，。]*)", query)
        if addr_match:
            extracted["new_address"] = addr_match.group(1).strip()
        elif any(kw in query for kw in ["省", "市", "区", "路", "号楼", "科技园"]) and len(query) > 8:
            # 可能是直接发来的地址文本
            clean_addr = re.sub(r"^(请帮我|麻烦|我要|改到|地址)", "", query).strip()
            if any(k in clean_addr for k in ["省", "市", "区", "路", "号"]):
                extracted["new_address"] = clean_addr

        # 5. 抽取发票抬头
        inv_match = re.search(r"(?:抬头|发票抬头)(?:是|为)?[:：\s]?([^\s，。]+(?:公司|集团|有限|工作室|个人))", query)
        if inv_match:
            extracted["invoice_title"] = inv_match.group(1).strip()

        # 6. 抽取纳税人识别号
        tax_match = re.search(r"(91[0-9A-Z]{16}|[0-9A-Z]{18})", query)
        if tax_match:
            extracted["tax_id"] = tax_match.group(1)

        # 记录识别到的实体至工作记忆
        if use_memory and "order_id" in extracted:
            memory_hub.set_referenced_entity(session_id, "order_id", extracted["order_id"])

        return extracted

    async def validate_and_build_clarification(
        self,
        action_name: str,
        current_slots: Dict[str, Any],
        customer_id: str,
        session_id: str
    ) -> SlotExtractionResult:
        """
        校验槽位是否齐全，若缺失则生成主动反向追问话术与交互式选项卡片
        """
        from app.services.agent.tools import action_tool_center
        from app.services.business_service import business_service

        tool_def = action_tool_center.get_tool(action_name)
        if not tool_def:
            return SlotExtractionResult(slots=current_slots, is_complete=True, missing_slots=[])

        required = tool_def.required_slots
        missing = [s for s in required if not current_slots.get(s)]

        if not missing:
            return SlotExtractionResult(slots=current_slots, is_complete=True, missing_slots=[])

        # 针对缺失槽位进行定制化优雅反问
        orders = await business_service.get_customer_orders(customer_id)

        # 缺失场景 1：缺失订单号 (order_id)
        if "order_id" in missing:
            options = []
            for ord in orders[:3]:
                action_text = "发起退款" if "refund" in action_name else ("修改地址" if "address" in action_name else "开具发票")
                options.append({
                    "title": f"订单 {ord['order_id']} · {ord['product_name'][:18]}",
                    "value": ord["order_id"],
                    "quick_prompt": f"帮我对订单 {ord['order_id']} {action_text}"
                })

            clarification_card = {
                "card_type": "CLARIFICATION_CARD",
                "missing_slot": "order_id",
                "title": "请选择需要办理业务的目标订单",
                "summary": "为您检测到您名下有以下订单，请直接点击选择：",
                "options": options
            }
            clarification_prompt = (
                f"请问您需要办理哪笔订单？"
                f"系统已为您检索到您账号绑定的订单列表，您可以直接点击下方卡片选择对应订单快速继续办理。"
            )
            return SlotExtractionResult(
                slots=current_slots,
                is_complete=False,
                missing_slots=missing,
                clarification_prompt=clarification_prompt,
                clarification_card=clarification_card
            )

        # 缺失场景 2：缺失退款原因 (refund_reason)
        if "refund_reason" in missing:
            ord_id = current_slots.get("order_id", "")
            reason_options = [
                {"title": "📦 七天无理由退货/退款", "value": "七天无理由退款", "quick_prompt": f"订单 {ord_id} 退款原因：七天无理由退款"},
                {"title": "⚙️ 算力/规格与预期不符", "value": "规格与预期不符", "quick_prompt": f"订单 {ord_id} 退款原因：规格与预期不符"},
                {"title": "💸 买错/重复下单需重购", "value": "买错需重购", "quick_prompt": f"订单 {ord_id} 退款原因：买错需重购"}
            ]
            clarification_card = {
                "card_type": "CLARIFICATION_CARD",
                "missing_slot": "refund_reason",
                "title": "请补充退款原因说明",
                "summary": "请选择或输入您的退货退款主要原因：",
                "options": reason_options
            }
            clarification_prompt = (
                f"已定位到您的订单（{ord_id}）。根据售后规范，请问您的退款主要原因是什么？"
                f"您可以直接点击下方常见原因快速提交。"
            )
            return SlotExtractionResult(
                slots=current_slots,
                is_complete=False,
                missing_slots=missing,
                clarification_prompt=clarification_prompt,
                clarification_card=clarification_card
            )

        # 缺失场景 3：缺失收件地址 (new_address)
        if "new_address" in missing:
            ord_id = current_slots.get("order_id", "")
            pref_addr = memory_hub.get_preferred_address(customer_id)
            addr_options = [
                {"title": f"📍 使用历史常用地址：{pref_addr}", "value": pref_addr, "quick_prompt": f"地址改到 {pref_addr}"}
            ]
            clarification_card = {
                "card_type": "CLARIFICATION_CARD",
                "missing_slot": "new_address",
                "title": "请提供变更后的新收货地址",
                "summary": "请提供新地址及联系方式：",
                "options": addr_options
            }
            clarification_prompt = (
                f"好的，请问订单 {ord_id} 需要将收货地址变更为哪里？"
                f"您可以直接输入新地址（包含省市区与门牌号），或者点击下方已为您预填的历史地址快速确认。"
            )
            return SlotExtractionResult(
                slots=current_slots,
                is_complete=False,
                missing_slots=missing,
                clarification_prompt=clarification_prompt,
                clarification_card=clarification_card
            )

        # 默认缺失兜底
        return SlotExtractionResult(
            slots=current_slots,
            is_complete=False,
            missing_slots=missing,
            clarification_prompt=f"为了帮您顺利办理该业务，还请补充以下信息：{', '.join(missing)}。"
        )

slot_engine = SlotEngine()
