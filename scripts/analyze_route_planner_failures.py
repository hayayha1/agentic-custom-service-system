"""Explain a completed, sealed benchmark; no inference calls and no rescoring.

Keep diagnostic attribution separate from the originally published scores.
"""
import json
from collections import Counter
from pathlib import Path

from scripts.route_planner_common import DATASET, ROOT, file_hash, source_hashes, write_json


RUN = DATASET / "results/native_v1"
ROOT_NAMES = {
    "route": "路由先发生错误",
    "schema": "模型输出被契约校验拒绝",
    "condition": "计划缺少结构化条件",
    "capability": "缺少业务工具，返回空计划",
    "sequence": "真实的先后依赖缺失",
    "other": "其他待复核",
}


def attribution(trial):
    if trial["passed"]:
        return "pass"
    if not trial["route_correct"]:
        return "route"
    if trial["inference_error"]:
        return "schema"
    if "missing_or_wrong_structured_condition" in trial["failures"]:
        return "condition"
    if "dag:missing_dag" in trial["failures"] and trial["capability_gaps"]:
        return "capability"
    if "required_dependency" in trial["failures"]:
        return "sequence"
    return "other"


def ancestors(tasks):
    parents = {str(task["step_id"]): set(map(str, task.get("depends_on", []))) for task in tasks}
    def visit(node, seen=None):
        seen = set() if seen is None else seen
        for parent in parents.get(str(node), ()):
            if parent not in seen:
                seen.add(parent)
                visit(parent, seen)
        return seen
    return {node: visit(node) for node in parents}


def source(path, line):
    return f"[{Path(path).name}:{line}]({(ROOT / path).as_posix()}:{line})"


def compact_plan(plan):
    if not plan:
        return None
    return {"intent_category": plan.get("intent_category"), "primary_action": plan.get("primary_action"),
            "planner_mode": plan.get("planner_mode"), "summary": plan.get("summary"),
            "subtasks": [{k: task[k] for k in ("step_id", "tool_name", "task_type", "arguments", "depends_on", "description") if k in task}
                         for task in plan.get("subtasks", [])]}


def main():
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((RUN / "report.json").read_text(encoding="utf-8"))
    seal = json.loads((RUN / "inference_seal.json").read_text(encoding="utf-8"))
    assert seal["status"] == "complete" and seal["sources_unchanged"]
    assert file_hash(RUN / "predictions.jsonl") == report["prediction_sha256"]
    assert file_hash(DATASET / "inputs.jsonl") == manifest["public_sha256"]
    assert file_hash(DATASET / "private/answer_key.jsonl") == manifest["answer_key_sha256"]
    assert source_hashes() == manifest["source_hashes"], "Diagnose the frozen production revision only"
    predictions = {(row["case_id"], row["repeat"]): row for row in (
        json.loads(line) for line in (RUN / "predictions.jsonl").read_text(encoding="utf-8").splitlines())}
    labels = {row["case_id"]: row for row in (
        json.loads(line) for line in (DATASET / "private/answer_key.jsonl").read_text(encoding="utf-8").splitlines())}
    trials = report["trials"]
    failed = [trial for trial in trials if not trial["passed"]]
    primary = Counter(attribution(trial) for trial in failed)
    by_scope = {scope: Counter(attribution(trial) for trial in failed if trial["scope"] == scope)
                for scope in ("current_regression", "target_capability")}
    dependency = Counter()
    independence = Counter()
    empty_dag = Counter()
    extras = Counter()
    valid_nonempty = []
    fast_waste_tokens = 0
    for trial in trials:
        prediction = predictions[(trial["case_id"], trial["repeat"])]
        label = labels[trial["case_id"]]
        tasks = (prediction["plan"] or {}).get("subtasks", [])
        reachability = ancestors(tasks)
        alignment = {k: str(v) for k, v in trial["goal_alignment"].items()}
        for a, b in label["must_precede"]:
            if a not in alignment or b not in alignment:
                dependency["unverifiable_missing_goal"] += 1
            elif alignment[a] in reachability.get(alignment[b], set()):
                dependency["satisfied"] += 1
            else:
                dependency["actual_missing_dependency"] += 1
        for a, b in label["must_be_independent"]:
            if a not in alignment or b not in alignment:
                independence["unverifiable_missing_goal"] += 1
            else:
                serial = (alignment[a] in reachability.get(alignment[b], set()) or
                          alignment[b] in reachability.get(alignment[a], set()))
                independence["actual_false_dependency" if serial else "satisfied"] += 1
        if trial["expected_route"] == "Deep-Path" and not trial["dag_structure_valid"]:
            cause = "schema_rejected" if trial["inference_error"] else "misrouted_empty_plan" if not trial["route_correct"] else "native_empty_plan"
            empty_dag[cause] += 1
        extras["route" if not trial["route_correct"] else "schema" if trial["inference_error"] else "accepted"] += trial["extra_tasks"]
        if trial["expected_route"] == "Deep-Path" and trial["route_correct"] and not trial["inference_error"] and tasks:
            valid_nonempty.append(trial)
        if trial["expected_route"] == "Fast-Path" and not trial["route_correct"]:
            fast_waste_tokens += trial["tokens"]
    assert len(failed) == sum(primary.values()) == 136
    assert primary == {"route": 87, "schema": 20, "condition": 15, "capability": 5, "sequence": 9}
    assert len(valid_nonempty) == 110 and all(trial["all_goals_covered"] for trial in valid_nonempty)
    assert sum(dependency.values()) == 159 and sum(independence.values()) == 66
    failure_details = []
    for case in report["cases"]:
        if case["passed_repeats"] == report["repeats"]:
            continue
        case_trials = sorted([t for t in trials if t["case_id"] == case["case_id"]], key=lambda t: t["repeat"])
        observations = []
        for trial in case_trials:
            prediction = predictions[(trial["case_id"], trial["repeat"])]
            rejected_outputs = [compact_plan(call.get("response", {}).get("arguments")) for call in prediction["calls"]
                                if call.get("response") and prediction["error"]]
            observations.append({"repeat": trial["repeat"], "passed": trial["passed"],
                "primary_blocker": attribution(trial), "observed_route": trial["observed_route"],
                "planner_calls": prediction["planner_calls"], "failures": trial["failures"],
                "missing_goals": trial["missing_goals"], "accepted_plan": compact_plan(prediction["plan"]),
                "rejected_model_outputs": rejected_outputs, "error": prediction["error"]})
        failure_details.append({**case, "expected": labels[case["case_id"]], "observations": observations})
    assert len(failure_details) == 46
    diagnostics = {"benchmark_model": report["model"], "trials": len(trials), "failed_trials": len(failed),
        "failed_cases": len(failure_details), "primary_blockers": dict(primary),
        "primary_blockers_by_scope": {k: dict(v) for k, v in by_scope.items()},
        "dependency_diagnostics": dict(dependency), "independence_diagnostics": dict(independence),
        "missing_dag_diagnostics": dict(empty_dag), "extra_tasks_by_first_blocker": dict(extras),
        "accepted_deep_nonempty_trials": len(valid_nonempty),
        "complete_goals_in_accepted_deep_trials": sum(t["all_goals_covered"] for t in valid_nonempty),
        "extra_tokens_from_fast_misrouting": fast_waste_tokens,
        "original_prediction_sha256": report["prediction_sha256"],
        "original_report_sha256": file_hash(RUN / "report.json"),
        "diagnostic_only_no_new_inference": True,
        "case_details": failure_details}
    write_json(RUN / "failure_analysis.json", diagnostics)

    lines = ["# 路由与 Planner 联合盲测：详细失败原因报告", "",
        "## 1. 结论与分析范围", "",
        "本报告复核已封存的 100 条用例、每条 3 次、共 300 次 deepseek-chat 真实模型测试。没有追加模型调用、修改标准答案、修改被测生产代码或选择性补测。",
        "", "300 次中 164 次全项通过、136 次失败；100 个 Case 中 54 个三次均通过，45 个三次均失败，1 个两次通过一次失败。",
        "", "**主要瓶颈是路由、输出契约及尚未实现的能力。不能把所有低分直接归结为模型不会拆解任务。**进入正确 Deep 通道、通过契约且返回非空 DAG 的 110 次输出，全部覆盖了该次用例的必要目标；但其中仍有顺序依赖与条件表达不合格的情况。该条件统计仅用于定位，不能替代 61.1% 的端到端目标完整覆盖率。",
        "", "## 2. 失败如何分布：按首个阻断点互斥统计", "",
        "| 首个阻断点 | 次数 | 占136次失败 | 当前能力回归 | 目标能力验收 |",
        "|---|---:|---:|---:|---:|"]
    for key in ("route", "schema", "condition", "capability", "sequence"):
        lines.append(f"| {ROOT_NAMES[key]} | {primary[key]} | {primary[key]/136:.1%} | {by_scope['current_regression'][key]} | {by_scope['target_capability'][key]} |")
    lines += ["| 合计 | 136 | 100% | 82 | 54 |", "",
        "此表采用诊断顺序：路由→输出契约→条件→工具缺口→依赖。它不是独立模块故障概率，同一次请求可能有多个潜在问题。上游失败后，后续能力往往无法被实际观察；修复路由不意味着这些请求就会自动全部通过。",
        "", "当前能力回归：246 次中 164 次通过，66.7%；目标能力验收：54 次中 0 次通过。目标能力缺口没有跳过，也没有记为成功。",
        "", "## 3. 路由失败：87次，是最早的主要阻断点", "",
        "### 3.1 Fast误入Deep：14个Case、42次", "",
        "| 子类 | 失败Case | 失败次数 | 代表表达 |", "|---|---:|---:|---|",
        "| 寒暄/致谢/告别 | 4 | 12 | 你好呀！；早上好，请问在吗？；多谢你的帮助；辛苦了，回头见 |",
        "| 单条知识查询 | 8 | 24 | 客服上班时间、周末是否上班、运费承担、退款到账周期等 |",
        "| 人工转接同义表达 | 2 | 6 | 接个真人来聊吧；让人工专员接手这次咨询 |", "",
        "直接原因：寒暄使用整句集合匹配，知识查询主要看‘政策/规则/规范/教程/手册’，转人工只匹配少数固定短语。`strip().lower()` 没有解决口语、语气词、标点和同义表达。",
        "", f"代码证据：{source('app/services/agent/planning.py',64)}、{source('app/services/agent/planning.py',69)}、{source('app/services/agent/planning.py',72)}。",
        "", f"影响：本轮额外触发 42 次复杂规划，消耗 {fast_waste_tokens:,} 个上报 Token。预期 Fast 请求至规划返回的 P95 达到 2.86 秒，包含这些误入慢通道的请求。路由函数自身 P95=0.041毫秒只说明判断很快，不证明通道选对，更不是网页完整回复时延。",
        "", "### 3.2 Deep误入Fast：15个Case、45次", "",
        "其中 33 次被当成单条知识问题，12 次被当成立即转人工。",
        "", "**知识关键词提前短路。**复合请求只要含有‘规则/政策’，且没有‘顺便/并且/然后/同时’，就容易提前返回单步知识路由。‘先…再…最后…’‘分别…以及…’等组合没有被完整识别。",
        "", "代表 Case `rp_9e979d23627a`：",
        "> 按照退款规则，先查订单 ORD-A001，再帮我申请退款，原因是拍错了。", "",
        "预期：Deep；查单→退款。实际三次均返回 Fast、KNOWLEDGE_QA、单个 knowledge_retriever，查单和退款目标均未进入有效计划。",
        "", "**‘人工’字面命中忽略否定、条件和时序。**以下四个 Deep Case 各三次都被立即转人工：",
        "- `rp_6b4408ead5b3`：不要转人工，先查物流，再开票。",
        "- `rp_f5b650908342`：先查可退余额，余额满足才退款，否则转人工。",
        "- `rp_eb50ad3275c1`：先查订单状态，再把结果交给人工。",
        "- `rp_597942cabeca`：先查单和退款进度，最后告知售后人工客服的工作时间。", "",
        "前者形成3次明确禁止动作误规划；后三者分别丢失条件、前置任务，或把‘询问人工客服时间’错当成‘请求转人工’。本轮只测试规划，未真实发起转接。",
        "", f"直接证据：{source('app/services/agent/planning.py',66)} 的人工短语判断位于其他意图判断之前，未检查否定范围、句子角色或前置任务。",
        "", "建议：构建完整意图与约束识别，区分即时转接、条件转接、先办后转和仅提及人工服务；对口语和同义表达做规范化。不能只把本测试集的14个漏识别句子逐条加入白名单。",
        "", "## 4. 输出契约失败：20次均为ValidationError", "",
        "本轮没有记录到 HTTP 错误或网络超时。20次‘推理错误’实际上是模型输出被应用校验拒绝，应与模型服务不可用分开解释。",
        "", "### 4.1 CLARIFICATION类型与校验器冲突：19次", "",
        "Schema 声明 `task_type` 可以取 CLARIFICATION；同时，每个节点又必须绑定一个业务工具。后置校验器根据绑定工具只接受 READ_TOOL、WRITE_TOOL 或 KNOWLEDGE_QA，因此 CLARIFICATION 节点没有合法组合。",
        "", "```python\n# Schema允许\ntask_type: Literal['READ_TOOL', 'WRITE_TOOL', 'KNOWLEDGE_QA', 'CLARIFICATION']\n\n# 后置校验却要求严格等于工具的执行类型\nif step.task_type != expected:\n    raise ValueError('Task type must match the tool registry')\n```", "",
        f"代码证据：{source('app/services/agent/planning.py',25)}、{source('app/services/agent/planning.py',48)}、{source('app/services/agent/planning.py',55)}。",
        "", "19次输出中出现21个不匹配节点：CLARIFICATION绑定只读工具9个、写工具4个、知识工具8个。一份输出可以有多个不匹配节点，所以21不能与19相加。",
        "", "当前能力中的不稳定 Case `rp_4d959720cb18`（第2次）：",
        "> 查 ORD-A001 物流，同时查 ORD-B002 发票状态，最后汇总。", "",
        "模型已经生成两个正确的独立读取节点；随后添加了一个 CLARIFICATION＋query_orders 节点，想承载‘汇总/无法取得发票字段时追问’。应用因此拒绝整份计划。这同时暴露了控制节点契约冲突、缺少汇总节点表达，以及工具返回字段描述不够明确的问题。不能把该次失败简单记成‘模型没有理解两个查询目标’。",
        "", "建议：把工具节点、澄清节点、汇总节点区分为能被执行器处理的类型，明确各自字段与合法组合；工具目录说明应明确哪些查询返回 invoice_status。仅放宽校验也不够，否则澄清节点可能被误当作真实查询执行。",
        "", "### 4.2 顶层intent_category不在枚举中：1次", "",
        "Case `rp_6e6be1bbf865` 第2次，保修状态→免费维修/收费报价。模型返回顶层 `intent_category=CLARIFICATION`，但顶层枚举只允许查询、执行、复合任务、知识问答、寒暄或人工升级。",
        "", "这是另一处契约表达缺口：子任务允许出现澄清概念，顶层却没有对应类别；加上维修能力缺失，模型选择了当前接口无法接收的降级表达。应统一定义缺能力/缺信息时的合法输出，不能通过放行任意枚举解决。",
        "", "## 5. 确认存在的顺序依赖错误：3个Case、9次", "",
        "159条必要关系中：75条满足，75条因前置目标缺失无法核验，9条在目标齐全时仍没有正确建立。后者才是本轮能直接归因于顺序规划的错误。",
        "", "| Case | 用户要求 | 实际关系 | 缺失关系 |", "|---|---|---|---|",
        "| rp_b4345c06ba76 | 查单→开票→物流 | 查单→开票，查单→物流 | 开票→物流 |",
        "| rp_ff2ea6af7e47 | 查支付状态→说明开票规则 | 两节点均无依赖 | 查单→规则查询 |",
        "| rp_4add05c7f092 | 退款规则→查单→退款 | 规则与查单独立，退款等待两者 | 规则→查单 |", "",
        "第一条实际输出摘录：", "",
        "```json\n[\n  {\"step_id\": 1, \"tool_name\": \"query_orders\", \"depends_on\": []},\n  {\"step_id\": 2, \"tool_name\": \"apply_invoice\", \"depends_on\": [1]},\n  {\"step_id\": 3, \"tool_name\": \"query_logistics\", \"depends_on\": [1]}\n]\n```", "",
        "节点在数组里排第三，不表示它等待第二个节点完成。该计划 summary 虽写‘最后查询物流’，图中却没有2→3的可达路径。当前执行器碰巧串行遍历也不能证明DAG正确，后续采用并发调度时会暴露顺序偏差。",
        "", f"直接校验仅覆盖拓扑合法、工具类型和非空等约束：{source('app/services/agent/planning.py',48)}；没有将用户明确的先后要求校验为图约束。",
        "", "建议：区分用户指定的时间顺序与数据依赖；两者都可形成必须保留的前置关系。根据抽取的顺序约束检查可达性，而不是依赖 summary 或节点列表位置。不能把所有任务统一串行化，否则会损害独立任务的规划。",
        "", "## 6. 条件分支：当前结构不能表示可执行条件", "",
        "57条被要求的结构化条件，满足0条。按首个阻断点归桶，其中15次是在目标和计划均存在时，仍因缺少条件直接失败；其他带条件请求可能更早被路由或契约阻断，不能再次累加到失败总数。",
        "", "例：‘未开票才申请，已开票则只展示信息’。即使模型安排了查单→开票，若没有绑定 `invoice_status == NOT_APPLIED`，也不能保证开票动作只在正确分支执行。",
        "", "这是明确的结构能力缺口：SubTask 只有 depends_on，没有 condition/when/guard；extra='forbid' 又不允许新增顶层条件字段。把条件写在 description 里不能提供机器执行语义。",
        "", f"代码证据：{source('app/services/agent/planning.py',22)}。执行器当前仅按PENDING状态和父节点是否COMPLETED挑选任务：{source('app/workflow/agent_runtime.py',157)}，没有条件求值与分支跳过处理。后者是源码发现的执行层缺口，本轮没有实际运行工具来验证它。",
        "", "建议：共同实现条件Schema、结果字段引用、运算符白名单、条件未知的等待行为、分支跳过状态与汇聚规则；已核实条件可以常量折叠。单独新增一个condition字段不能完成条件分支能力。",
        "", "## 7. 业务工具与降级表达缺口", "",
        "18个目标能力Case共54次全部失败，涉及结构化条件、库存/下单/提醒、余额、报修/工单/通知/保修、先办后转人工的计划表达，以及专票类型参数。它们与当前能力回归分开统计。",
        "", "其中5次是正确进入Deep、模型返回合法顶层类别，但没有任何DAG节点：已知有库存/无库存时要求下单或登记提醒，注册工具没有对应能力，模型转而用CHITCHAT等类别说明无法办理。这样避免了编造工具，但不能算完成用户目标，也不应归因成‘模型有工具却拒不使用’。",
        "", "现有发票模型仅含订单号、抬头、税号、邮箱，缺少普票/专票类型参数。报修与库存等工具名也不在生产工具注册枚举中。",
        "", f"工具集合证据：{source('app/services/agent/planning.py',17)}；发票参数证据：{source('app/services/agent/contracts.py',36)}。",
        "", "建议：先明确产品支持范围和工具契约，缺能力时返回结构化的不支持/转人工结果；要通过目标能力验收，需要真实或明确隔离的模拟适配器。不得在生产计划中编造不存在的工具，或用 description 假装已具备执行能力。",
        "", "## 8. 必须澄清的评分解读", "",
        "### 8.1 并行57.6%不等于发现42.4%的错误串行依赖", "",
        "66对要求独立的目标中，38对目标均可定位且关系正确；其余28对因至少一个目标缺失而无法核验。**本轮在可核验的38对中，没有发现实际错误的串行依赖。**原指标保留57.6%，因为它是端到端满足率；诊断时不能把缺目标一律当成Planner添加了错误依赖。",
        "", "### 8.2 目标完整覆盖61.1%的缺失主要由上游造成", "",
        "180次Deep需求中110次目标齐全；其余70次由45次误路由、20次契约拒绝、5次缺工具空计划构成。仅在正确进入Deep且返回非空可接受DAG的110次中，本次规则没有发现目标遗漏或已提供参数不匹配。该诊断受本评测工具匹配与主题关键词规则约束，不代表已经证明所有自然语言目标都能被理解。",
        "", "### 8.3 额外任务33个并非33次真实多办业务", "",
        "评分中的33个未匹配额外节点，全部来自Deep误入Fast后返回的通用知识路由描述。它们没有对应上标准目标，被规则计为extra。正确进入Deep且返回可接受计划的部分，没有观测到未匹配冗余任务。不能据此宣称模型会执行33次多余业务。",
        "", "### 8.4 DAG结构79.4%不代表观察到大量环路", "",
        "180次Deep需求中143次有结构可接受的非空计划，37次被记missing_dag：20次契约拒绝、12次误入人工转接后空计划、5次原生模型因缺能力返回空计划。已接受计划中未发现环路、未知依赖或非法工具参数。143次包含部分误路由的单步知识描述，不能替代正确通道下的任务质量指标。",
        "", "### 8.5 零无依据订单不等于所有安全问题都已通过", "",
        "本轮规则没有发现额外编造订单号；但已有3次明确拒绝人工转接仍被规划转人工。未测试真实提交、权限绕过、网络重试、审批恢复、完整对话或高并发，不能从本报告推导这些环节合格。",
        "", "### 8.6 产品策略与评分边界需要显式冻结", "",
        "本集采用‘私有业务数据/业务变更/多目标/条件任务进入Deep’的产品策略。对‘上下文已知订单取消，因而只需解释政策’或‘两个知识主题能合并检索’等情形，另一个产品可以允许提前折叠后走Fast；若选择该策略，应发布新版本标注并重新测试，而不能事后修改本轮答案。本报告中的明确否定转人工、复合业务被政策词截断等问题不依赖这些边界选择。",
        "", "冻结目标匹配主要检查业务/知识工具和明确实体参数；本轮没有独立验收‘最后汇总’的输出义务，也没有对最终语言答案评分。因而‘110次必要目标齐全’仅指当前标签中列出的工具目标，不能扩大为最终回复已经完整满足所有表达要求。",
        "", "## 9. 修复顺序与验证建议", "",
        "| 优先级 | 修复对象 | 应验证的结果 |", "|---|---|---|",
        "| 第一批 | 否定/条件/前置任务下的转人工识别，简单查询覆盖，复合语义路由 | 禁止转接为0；Fast不调用复杂Planner；业务复合请求不被政策词截断 |",
        "| 第一批 | 澄清/汇总/工具节点的契约一致性 | Schema允许的结构可被校验及执行器一致处理；缺能力/缺信息有明确降级 |",
        "| 第二批 | 用户显式顺序约束 | 本报告三类缺边全部修复，同时保留真正独立任务 |",
        "| 第二批 | 条件表达与运行时分支 | 未知/真/假三种状态均有明确行为，互斥分支不同时执行 |",
        "| 按产品范围 | 库存、报修、余额等工具与专票参数 | 有真实能力契约、权限和失败结果；不使用假工具充数 |",
        "| 评测完善 | 拆分无法核验与真实依赖错误、空计划与非法图、路由描述与业务冗余 | 保留原始分数，新增诊断维度，避免误读 |", "",
        "本集答案已用于事后诊断，修复后可继续作为回归集；评估泛化时，应另设未用于调参的新盲测集。不可只记住这100个问题，或把未实现的Case改成跳过来提高分数。",
        "", "## 10. 审计与附件", "",
        f"- 原始预测SHA256：`{report['prediction_sha256']}`。",
        f"- 原始报告SHA256：`{file_hash(RUN / 'report.json')}`。",
        "- 本报告是原始盲测完成后的只读诊断，没有改变原始预测、标准答案或评分结果。",
        "- 附件 `failure_analysis.json` 保存46个失败Case的标准约束、三次实际计划、被拒绝的原始结构和首要阻断点。",
        "- 附件 `FAILED_CASE_DETAILS.md` 提供逐Case可读明细；原 `case_results.csv` 可查看全部100条结果。", ""]
    (RUN / "FAILURE_ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
    appendix = ["# 46个失败Case的逐条证据", "", "通过/失败均引用原始300次测试；下面不会追加模型调用。每条展示首个失败重复的计划，全部三次结构见failure_analysis.json。", ""]
    for index, case in enumerate(failure_details, 1):
        first_failure = next(o for o in case["observations"] if not o["passed"])
        expected = case["expected"]
        appendix += [f"## {index}. {case['case_id']}", "", f"- 问题：{case['query']}",
            f"- 分类/范围：{case['group']} / {case['scope']}；通过 {case['passed_repeats']}/3。",
            f"- 预期通道：{expected['expected_route']}；实际三次：" + "、".join(o["observed_route"] for o in case["observations"]),
            "- 首要阻断点：" + "；".join(f"{ROOT_NAMES.get(k,k)} {v}次" for k,v in Counter(o["primary_blocker"] for o in case["observations"] if not o["passed"]).items()),
            f"- 第{first_failure['repeat']}次失败项：" + "；".join(first_failure["failures"]), "",
            "预期目标与关系：", "", "```json", json.dumps({k: expected[k] for k in (
                "required_goals", "must_precede", "must_be_independent", "conditions", "forbidden_tools")}, ensure_ascii=False, indent=2), "```", "",
            "该次实际已接受计划：", "", "```json", json.dumps(first_failure["accepted_plan"], ensure_ascii=False, indent=2), "```", ""]
        if first_failure["rejected_model_outputs"]:
            appendix += ["该次被校验器拒绝的模型原始计划：", "", "```json", json.dumps(first_failure["rejected_model_outputs"], ensure_ascii=False, indent=2), "```", ""]
    (RUN / "FAILED_CASE_DETAILS.md").write_text("\n".join(appendix), encoding="utf-8")
    assert file_hash(RUN / "predictions.jsonl") == report["prediction_sha256"]
    assert file_hash(RUN / "report.json") == diagnostics["original_report_sha256"]
    print(json.dumps({"report": str(RUN / "FAILURE_ANALYSIS.md"), "failed_cases": len(failure_details),
        "failed_trials": len(failed), "primary_blockers": dict(primary), "original_results_unchanged": True}))


if __name__ == "__main__":
    main()
