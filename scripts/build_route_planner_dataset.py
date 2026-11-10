"""Author and freeze a 100-case benchmark. Never imported by inference workers.

Public inputs and private labels are physically separate. Rebuilding an existing
release is refused, so evaluation cannot silently relabel failures.
"""
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.route_planner_common import DATASET, file_hash, source_hashes, write_json


A, B, C = "ORD-A001", "ORD-B002", "ORD-C003"
TITLE = "星海科技有限公司"
ADDRESS = "北京市海淀区中关村南大街1号"


def goal(identifier, tool, order=None, *, terms=None, arguments=None, shared=False, alternatives=None):
    args = dict(arguments or {})
    if order:
        args["order_id"] = order
    matcher = {"tool": tool, "arguments": args}
    if terms:
        matcher["text_any"] = terms
    return {"goal_id": identifier, "any_of": [matcher] + (alternatives or []), "allow_shared_node": shared}


def orders(identifier="order", order=A):
    return goal(identifier, "query_orders", order)


def logistics(identifier="logistics", order=A):
    # The registered order query also returns nested logistics data. A targeted
    # order-detail query is therefore an accepted alternative, not a wrong tool.
    return goal(identifier, "query_logistics", order,
                alternatives=[{"tool": "query_orders", "arguments": {"order_id": order}}])


def invoice(identifier="invoice", order=A):
    return goal(identifier, "apply_invoice", order, arguments={"invoice_title": TITLE})


def refund(identifier="refund", order=A):
    return goal(identifier, "apply_refund", order, arguments={"refund_reason": "拍错了"})


def policy(identifier="policy", terms=None):
    return goal(identifier, "knowledge_retriever", terms=terms or ["政策", "规则"], shared=True)


def base_context():
    return {"current_time": "2026-11-07T10:00:00+08:00", "timezone": "Asia/Shanghai",
            "episode": {"entities": {}, "facts": {}, "summary": ""}, "profile": {}}


def build(destination=DATASET):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("Frozen dataset already exists; create a new version instead of overwriting")
    rng = random.Random(20261107)
    records = []

    def add(group, query, goals=(), *, edges=(), independent=(), conditions=(), gaps=(),
            context=None, forbidden=(), allowed=(), expected_intent=None, notes=""):
        identifier = "rp_" + f"{rng.getrandbits(48):012x}"
        fast = group.startswith("fast_")
        public = {"case_id": identifier, "query": query, "context": context or ({} if fast else base_context())}
        label = {"case_id": identifier, "group": group,
            "scope": "target_capability" if gaps else "current_regression",
            "capability_gaps": list(gaps), "expected_route": "Fast-Path" if fast else "Deep-Path",
            "expected_intent": expected_intent, "required_goals": list(goals),
            "must_precede": list(edges), "must_be_independent": list(independent),
            "conditions": list(conditions), "forbidden_tools": list(forbidden),
            "allowed_support_tools": list(allowed), "notes": notes}
        records.append((public, label))

    for query in ["你好", "您好", "hello", "hi", "谢谢", "再见", "你好呀！", "早上好，请问在吗？", "多谢你的帮助", "辛苦了，回头见"]:
        add("fast_greeting", query, expected_intent="CHITCHAT")

    for query in [
        "你们客服上班时间是几点？", "退款规则是什么", "开票规则是什么", "退换货政策是什么？",
        "请介绍一下售后服务政策", "配送规则是什么", "账户注销规则是什么", "电子发票的申请规则是什么？",
        "你们的质保政策是什么", "促销优惠的使用规则是什么", "退款一般几天到账？", "周末客服也上班吗？",
        "发票可以开公司抬头吗？", "服务器的保修期通常是多久？", "运费一般由谁承担？",
        "会员积分有效期有多久？", "不要给我申请退款，只告诉我退款规则", "不是要开票，我只问开票规则",
        "请问七天无理由退货政策是什么", "配送服务覆盖哪些城市？",
    ]:
        add("fast_knowledge", query, expected_intent="KNOWLEDGE_QA")

    for query in ["帮我转人工", "转人工客服", "我要找真人客服", "请呼叫人工", "找客服", "直接转人工，不需要机器人处理",
                  "请帮我接一位人工客服", "接个真人来聊吧", "让人工专员接手这次咨询", "不要自动办理业务，帮我转人工"]:
        add("fast_handoff", query, expected_intent="HUMAN_ESCALATION")

    add("deep_sequential", f"先查订单 {A} 的状态，然后查询这笔订单的物流。", [orders(), logistics()], edges=[("order", "logistics")])
    add("deep_sequential", f"先查订单 {A}，校验订单是否允许退货，再申请退货，原因是拍错了，最后告知退货时效。",
        [orders(), refund(), policy(terms=["退货", "售后", "时效"])], edges=[("order", "refund")],
        conditions=[{"target_goal": "refund", "source_goal": "order", "field": "status", "operator": "in", "value": ["PAID", "COMPLETED"]}],
        gaps=["structured_conditions"], notes="状态校验可通过结构化前置条件承载，不要求编造独立校验工具。")
    add("deep_sequential", f"先查订单 {A} 的状态，再开具发票，抬头是{TITLE}，之后解释开票政策。",
        [orders(), invoice(), policy(terms=["发票", "开票"])], edges=[("order", "invoice"), ("invoice", "policy")])
    add("deep_sequential", f"先查订单 {A}，再把收货地址改为{ADDRESS}，修改后查询这笔订单物流。",
        [orders(), goal("address", "update_shipping_address", A, arguments={"new_address": ADDRESS}), logistics()],
        edges=[("order", "address"), ("address", "logistics")])
    add("deep_sequential", f"先查订单 {A} 的退款进度，再查这笔订单的详细状态。",
        [goal("refund_status", "query_refund_status", A), orders()], edges=[("refund_status", "order")])
    ctx = base_context(); ctx["orders"] = [{"order_id": A, "status": "UNPAID"}]
    add("deep_sequential", f"先查订单 {A} 的详细信息，再取消这笔未支付订单。",
        [orders(), goal("cancel", "cancel_unpaid_order", A)], edges=[("order", "cancel")], context=ctx)
    add("deep_sequential", f"先查询订单 {A} 的物流，再帮我催一下这笔订单的快递。",
        [logistics(), goal("expedite", "expedite_shipping", A)], edges=[("logistics", "expedite")])
    add("deep_sequential", f"先查订单 {A}，查完以后再查订单 {B}。",
        [orders("order_a", A), orders("order_b", B)], edges=[("order_a", "order_b")])
    add("deep_sequential", f"先查订单 {A} 的详细信息，再查退款进度，最后告诉我售后人工客服的工作时间。",
        [orders(), goal("refund_status", "query_refund_status", A), policy(terms=["客服", "工作时间", "上班"])],
        edges=[("order", "refund_status"), ("refund_status", "policy")])
    add("deep_sequential", f"先为订单 {A} 申请退款，原因是拍错了，提交后再查退款进度。",
        [refund(), goal("refund_status", "query_refund_status", A)], edges=[("refund", "refund_status")])
    add("deep_sequential", f"先查订单 {A}，再开发票，抬头是{TITLE}，最后查询这单物流。",
        [orders(), invoice(), logistics()], edges=[("order", "invoice"), ("invoice", "logistics")])
    add("deep_sequential", f"先查订单 {A}，再查订单 {B}，最后只为 {B} 开发票，抬头是{TITLE}。",
        [orders("order_a", A), orders("order_b", B), invoice("invoice_b", B)],
        edges=[("order_a", "order_b"), ("order_b", "invoice_b")])
    add("deep_sequential", f"请按先后顺序查询 {A}、{B} 这两笔订单的物流，第一笔查完再查第二笔。",
        [logistics("a", A), logistics("b", B)], edges=[("a", "b")])
    add("deep_sequential", f"先给我查退款规则，再查订单 {A}，然后申请退款，原因是拍错了。",
        [policy(terms=["退款", "退货"]), orders(), refund()], edges=[("policy", "order"), ("order", "refund")])
    add("deep_sequential", f"先核对订单 {A} 的信息，再帮我催件。", [orders(), goal("expedite", "expedite_shipping", A)], edges=[("order", "expedite")])
    add("deep_sequential", f"先查询订单 {A}，然后开票，发票抬头是{TITLE}。", [orders(), invoice()], edges=[("order", "invoice")])
    add("deep_sequential", f"先查订单 {A} 的退款进度，完成后再查订单 {B} 的物流。",
        [goal("refund_status", "query_refund_status", A), logistics("logistics_b", B)], edges=[("refund_status", "logistics_b")])
    add("deep_sequential", f"先核对订单 {B}，再为这笔订单申请退款，原因是拍错了。",
        [orders(order=B), refund(order=B)], edges=[("order", "refund")])
    add("deep_sequential", f"先查看订单 {A} 的物流，再把该订单的地址改为{ADDRESS}。",
        [logistics(), goal("address", "update_shipping_address", A, arguments={"new_address": ADDRESS})], edges=[("logistics", "address")])
    add("deep_sequential", f"先查订单 {A} 的支付状态，然后告诉我通用开票规则。",
        [orders(), policy(terms=["发票", "开票"])], edges=[("order", "policy")])

    add("deep_parallel", f"同时查订单 {A} 和 {B} 的完整物流轨迹，最后汇总。", [logistics("a", A), logistics("b", B)], independent=[("a", "b")])
    add("deep_parallel", f"订单号已确认是 {A}，请独立查询物流并申请发票，抬头是{TITLE}，两件事互不等待。",
        [logistics(), invoice()], independent=[("logistics", "invoice")])
    add("deep_parallel", f"同时查订单 {A} 的物流和订单 {B} 的退款进度。",
        [logistics(), goal("refund_b", "query_refund_status", B)], independent=[("logistics", "refund_b")])
    add("deep_parallel", f"分别查询订单 {A} 的详细状态与订单 {B} 的物流，互不依赖。",
        [orders(), logistics("b", B)], independent=[("order", "b")])
    add("deep_parallel", f"查一下订单 {A} 的物流，同时介绍通用退货政策，两项可以独立处理。",
        [logistics(), policy(terms=["退货", "退款", "售后"])], independent=[("logistics", "policy")])
    add("deep_parallel", f"同时查询 {A} 和 {B} 的退款审核进度。",
        [goal("a", "query_refund_status", A), goal("b", "query_refund_status", B)], independent=[("a", "b")])
    add("deep_parallel", f"独立查询订单 {A} 的退款进度和通用开票规则，最后一起告诉我。",
        [goal("refund_status", "query_refund_status", A), policy(terms=["开票", "发票"])], independent=[("refund_status", "policy")])
    add("deep_parallel", f"给订单 {A} 和 {B} 分别开发票，抬头均为{TITLE}，两笔独立申请。",
        [invoice("a", A), invoice("b", B)], independent=[("a", "b")])
    add("deep_parallel", f"一边查订单 {A} 的详情，一边介绍客服服务时间，分别处理后汇总。",
        [orders(), policy(terms=["客服", "服务时间", "上班"])], independent=[("order", "policy")])
    add("deep_parallel", f"帮我查 {A} 订单物流，同时查 {B} 订单发票状态，最后汇总给我。",
        [logistics("a", A), orders("invoice_status_b", B)], independent=[("a", "invoice_status_b")],
        notes="query_orders 契约返回 invoice_status，允许复用订单查询。")
    add("deep_parallel", "分别查退货政策和开票规则，这两项知识查询互不依赖，最后汇总。",
        [policy("returns", ["退货", "退款"]), policy("invoices", ["开票", "发票"])], independent=[("returns", "invoices")],
        notes="合并为一次覆盖两个主题的知识检索也可接受。")
    add("deep_parallel", f"订单 {A} 的物流、订单 {B} 的退款进度和通用退货政策，三件事分别查询后汇总。",
        [logistics(), goal("refund_b", "query_refund_status", B), policy(terms=["退货", "退款", "售后"])],
        independent=[("logistics", "refund_b"), ("logistics", "policy"), ("refund_b", "policy")])
    add("deep_parallel", f"并行查订单 {A}、{B}、{C} 的物流，最后汇总三单结果。",
        [logistics("a", A), logistics("b", B), logistics("c", C)], independent=[("a", "b"), ("a", "c"), ("b", "c")])
    add("deep_parallel", f"独立为订单 {A} 开发票，抬头是{TITLE}，并查询订单 {B} 的物流。",
        [invoice(), logistics("b", B)], independent=[("invoice", "b")])
    add("deep_parallel", f"分别查询订单 {A} 的详情、订单 {B} 的退款进度以及售后政策，三个结果一起给我。",
        [orders(), goal("refund_b", "query_refund_status", B), policy(terms=["售后", "退货", "退款"])],
        independent=[("order", "refund_b"), ("order", "policy"), ("refund_b", "policy")])

    add("deep_conditional", "先查商品 SKU-100 的库存，有库存就创建一笔订单，没有库存就登记到货提醒。",
        [goal("stock", "query_inventory", arguments={"sku": "SKU-100"}), goal("buy", "create_order", arguments={"sku": "SKU-100"}),
         goal("remind", "subscribe_stock_alert", arguments={"sku": "SKU-100"})], edges=[("stock", "buy"), ("stock", "remind")],
        conditions=[{"target_goal": "buy", "source_goal": "stock", "field": "available_quantity", "operator": "gt", "value": 0},
                    {"target_goal": "remind", "source_goal": "stock", "field": "available_quantity", "operator": "eq", "value": 0}],
        gaps=["inventory_order_alert_tools", "structured_conditions"])
    ctx = base_context(); ctx["inventory"] = {"sku": "SKU-100", "available_quantity": 5, "verified": True}
    add("deep_conditional", "如果 SKU-100 有库存就下单，没有就登记提醒；使用刚才已经核实的库存结果。",
        [goal("buy", "create_order", arguments={"sku": "SKU-100"})], forbidden=["subscribe_stock_alert"], context=ctx, gaps=["create_order_tool"])
    ctx = base_context(); ctx["inventory"] = {"sku": "SKU-100", "available_quantity": 0, "verified": True}
    add("deep_conditional", "如果 SKU-100 有库存就下单，否则登记到货提醒；库存已核实，请据此安排。",
        [goal("remind", "subscribe_stock_alert", arguments={"sku": "SKU-100"})], forbidden=["create_order"], context=ctx, gaps=["stock_alert_tool"])
    add("deep_conditional", f"先查订单 {A}，如果状态是 PAID 就申请退款，原因是拍错了，否则只说明退款规则。",
        [orders(), refund(), policy(terms=["退款", "退货"])], edges=[("order", "refund"), ("order", "policy")],
        conditions=[{"target_goal": "refund", "source_goal": "order", "field": "status", "operator": "eq", "value": "PAID"},
                    {"target_goal": "policy", "source_goal": "order", "field": "status", "operator": "ne", "value": "PAID"}], gaps=["structured_conditions"])
    add("deep_conditional", f"查订单 {A}，如果未支付就取消，如果已支付就申请退款，原因是拍错了。",
        [orders(), goal("cancel", "cancel_unpaid_order", A), refund()], edges=[("order", "cancel"), ("order", "refund")],
        conditions=[{"target_goal": "cancel", "source_goal": "order", "field": "status", "operator": "eq", "value": "UNPAID"},
                    {"target_goal": "refund", "source_goal": "order", "field": "status", "operator": "eq", "value": "PAID"}], gaps=["structured_conditions"])
    add("deep_conditional", f"先查订单 {A}，未发货就把地址改为{ADDRESS}，已发货则只告诉我改派规则。",
        [orders(), goal("address", "update_shipping_address", A, arguments={"new_address": ADDRESS}), policy(terms=["改派", "地址", "配送"])],
        edges=[("order", "address"), ("order", "policy")],
        conditions=[{"target_goal": "address", "source_goal": "order", "field": "status", "operator": "eq", "value": "UNSHIPPED"}], gaps=["structured_conditions"])
    add("deep_conditional", f"查询订单 {A} 的物流；只有物流状态是 SHIPPING 才催件，否则只返回查询结果。",
        [logistics(), goal("expedite", "expedite_shipping", A)], edges=[("logistics", "expedite")],
        conditions=[{"target_goal": "expedite", "source_goal": "logistics", "field": "status", "operator": "eq", "value": "SHIPPING"}], gaps=["structured_conditions"])
    add("deep_conditional", "先查设备 DEV-100 的保修状态，在保则创建免费维修工单，过保则生成收费维修报价。",
        [goal("warranty", "query_warranty", arguments={"device_id": "DEV-100"}), goal("repair", "create_repair_ticket"), goal("quote", "quote_repair")],
        edges=[("warranty", "repair"), ("warranty", "quote")],
        conditions=[{"target_goal": "repair", "source_goal": "warranty", "field": "in_warranty", "operator": "eq", "value": True},
                    {"target_goal": "quote", "source_goal": "warranty", "field": "in_warranty", "operator": "eq", "value": False}], gaps=["repair_warranty_tools", "structured_conditions"])
    add("deep_conditional", "先查询设备 DEV-100 的报修记录，报修次数大于三次则通知运维，否则创建普通维修工单。",
        [goal("records", "query_repair_records", arguments={"device_id": "DEV-100"}), goal("notify", "notify_operations"), goal("ticket", "create_repair_ticket")],
        edges=[("records", "notify"), ("records", "ticket")],
        conditions=[{"target_goal": "notify", "source_goal": "records", "field": "repair_count", "operator": "gt", "value": 3},
                    {"target_goal": "ticket", "source_goal": "records", "field": "repair_count", "operator": "lte", "value": 3}], gaps=["repair_operations_tools", "structured_conditions"])
    add("deep_conditional", f"先查我的可退余额，余额不少于100元就对订单 {A} 申请100元退款，原因是拍错了，否则转人工核实。",
        [goal("balance", "query_balance"), goal("refund", "apply_refund", A, arguments={"refund_reason": "拍错了", "refund_amount": 100}), goal("handoff", "transfer_to_human")],
        edges=[("balance", "refund"), ("balance", "handoff")],
        conditions=[{"target_goal": "refund", "source_goal": "balance", "field": "refundable_balance", "operator": "gte", "value": 100}], gaps=["balance_handoff_tools", "structured_conditions"])
    ctx = base_context(); ctx["orders"] = [{"order_id": A, "status": "PAID", "verified": True}]
    add("deep_conditional", f"如果订单 {A} 已支付就申请退款，未支付就取消；使用已核实状态，退款原因是拍错了。",
        [refund()], context=ctx, forbidden=["cancel_unpaid_order"], allowed=["query_orders"], notes="已知条件允许常量折叠，不强制生成无意义分支。")
    ctx = base_context(); ctx["orders"] = [{"order_id": A, "status": "CANCELLED", "verified": True}]
    add("deep_conditional", f"如果订单 {A} 还有效就申请退款，原因是拍错了；如果已经取消，就只解释取消后的退款政策。已核实状态在上下文中。",
        [policy(terms=["取消", "退款"])], context=ctx, forbidden=["apply_refund", "cancel_unpaid_order"], allowed=["query_orders"])
    add("deep_conditional", f"先查订单 {A}，状态是 PAID 才开发票，抬头是{TITLE}；未支付则取消订单。",
        [orders(), invoice(), goal("cancel", "cancel_unpaid_order", A)], edges=[("order", "invoice"), ("order", "cancel")],
        conditions=[{"target_goal": "invoice", "source_goal": "order", "field": "status", "operator": "eq", "value": "PAID"},
                    {"target_goal": "cancel", "source_goal": "order", "field": "status", "operator": "eq", "value": "UNPAID"}], gaps=["structured_conditions"])
    add("deep_conditional", f"查询订单 {A} 是否已经开票，未开票才申请，抬头是{TITLE}，已开票则只展示订单信息。",
        [orders(), invoice()], edges=[("order", "invoice")],
        conditions=[{"target_goal": "invoice", "source_goal": "order", "field": "invoice_status", "operator": "eq", "value": "NOT_APPLIED"}], gaps=["structured_conditions"])
    add("deep_conditional", f"先查订单 {A} 的退货资格，允许退货才申请退款，原因是拍错了；不允许就只解释售后政策。",
        [orders(), refund(), policy(terms=["退货", "退款", "售后"])], edges=[("order", "refund"), ("order", "policy")],
        conditions=[{"target_goal": "refund", "source_goal": "order", "field": "can_refund", "operator": "eq", "value": True},
                    {"target_goal": "policy", "source_goal": "order", "field": "can_refund", "operator": "eq", "value": False}], gaps=["structured_conditions"])

    ctx = base_context(); ctx["orders"] = [{"order_id": A, "product": "服务器", "created_at": "2026-11-06T14:00:00+08:00"}]
    add("deep_mixed", "查下我昨天买的服务器订单物流，顺便开专票，如果不想要了政策是怎样",
        [logistics(), goal("invoice", "apply_invoice", A, arguments={"invoice_type": "special"}), policy(terms=["退货", "退款", "售后"])],
        context=ctx, forbidden=["apply_refund", "cancel_unpaid_order"], allowed=["query_orders"], gaps=["invoice_type_argument"])
    add("deep_mixed", "帮我查询这个设备的报修记录，生成工单，同时通知运维，还要告诉我保修到期时间",
        [goal("records", "query_repair_records", arguments={"device_id": "DEV-100"}), goal("ticket", "create_repair_ticket"),
         goal("notify", "notify_operations"), goal("warranty", "query_warranty", arguments={"device_id": "DEV-100"})],
        edges=[("records", "ticket"), ("ticket", "notify")], independent=[("warranty", "records")],
        context={**base_context(), "episode": {"entities": {"device_id": "DEV-100"}}}, gaps=["repair_operations_warranty_tools"])
    add("deep_mixed", "先查余额，申请退款，再查看退款到账周期",
        [goal("balance", "query_balance"), goal("refund", "apply_refund"), policy(terms=["退款", "到账"])],
        edges=[("balance", "refund"), ("refund", "policy")], gaps=["balance_tool"], notes="缺订单与原因必须留空，不能臆造。")
    add("deep_mixed", f"你好，帮我查订单 {A} 的物流并开发票，抬头是{TITLE}。", [logistics(), invoice()])
    add("deep_mixed", f"你好，不要开票，帮我查订单 {A} 的物流和退款政策。",
        [logistics(), policy(terms=["退款", "退货"])], forbidden=["apply_invoice", "apply_refund"])
    add("deep_mixed", f"先查订单 {A} 的状态，再把查询结果交给人工客服。",
        [orders(), goal("handoff", "transfer_to_human")], edges=[("order", "handoff")], gaps=["handoff_plan_node"])
    add("deep_mixed", f"按照退款规则，先查订单 {A}，再帮我申请退款，原因是拍错了。", [orders(), refund()], edges=[("order", "refund")])
    add("deep_mixed", f"不要转人工，先查订单 {A} 物流，再开票，抬头是{TITLE}。",
        [logistics(), invoice()], edges=[("logistics", "invoice")], forbidden=["transfer_to_human"])
    add("deep_mixed", f"给订单 {A} 开票，抬头是{TITLE}，另外查一下订单 {B} 物流。", [invoice(), logistics("b", B)])
    ctx = base_context(); ctx["orders"] = [{"order_id": A, "created_at": "2026-11-06T14:00:00+08:00"},
                                           {"order_id": B, "created_at": "2026-11-05T14:00:00+08:00"}]
    add("deep_mixed", "查昨天那笔订单的物流，也查一下前天那笔订单的退款进度。",
        [logistics("yesterday", A), goal("day_before", "query_refund_status", B)], context=ctx)

    counts = Counter(label["group"] for _, label in records)
    assert counts == {"fast_greeting": 10, "fast_knowledge": 20, "fast_handoff": 10,
                      "deep_sequential": 20, "deep_parallel": 15, "deep_conditional": 15, "deep_mixed": 10}
    assert len(records) == len({p["case_id"] for p, _ in records}) == 100
    for _, label in records:
        goal_ids = {g["goal_id"] for g in label["required_goals"]}
        assert all(a in goal_ids and b in goal_ids for a, b in label["must_precede"] + label["must_be_independent"])
        assert all(c["target_goal"] in goal_ids and c["source_goal"] in goal_ids for c in label["conditions"])
    rng.shuffle(records)
    (destination / "private").mkdir(parents=True)
    public_path, key_path = destination / "inputs.jsonl", destination / "private/answer_key.jsonl"
    public_path.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p, _ in records), encoding="utf-8")
    key_path.write_text("".join(json.dumps(g, ensure_ascii=False) + "\n" for _, g in records), encoding="utf-8")
    manifest = {"version": "route_planner_v1", "authored_at": datetime.now(timezone.utc).isoformat(),
                "cases": len(records), "groups": dict(counts),
                "scopes": dict(Counter(g["scope"] for _, g in records)),
                "public_sha256": file_hash(public_path), "answer_key_sha256": file_hash(key_path),
                "source_hashes": source_hashes(), "builder_sha256": file_hash(__file__),
                "blind_protocol": "predict process reads only public inputs; score only after inference_seal.json"}
    write_json(destination / "manifest.json", manifest)
    print(json.dumps({"dataset": str(destination), "cases": len(records), "groups": dict(counts),
                      "public_sha256": manifest["public_sha256"], "answer_key_sha256": manifest["answer_key_sha256"]}))


if __name__ == "__main__":
    build()
