"""Post-inference scoring. This is the ONLY runner that loads reference labels.

Scores are computed from sealed predictions; it never calls an inference model.
"""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.route_planner_common import DATASET, ROOT, file_hash, read_public, write_json


REGISTERED_TOOLS = {"query_orders", "query_logistics", "query_refund_status", "apply_refund",
                    "update_shipping_address", "cancel_unpaid_order", "apply_invoice",
                    "expedite_shipping", "knowledge_retriever"}


def equivalent(actual, expected, field=""):
    if isinstance(expected, str) and isinstance(actual, str):
        a, e = actual.strip().casefold(), expected.strip().casefold()
        if field == "refund_reason":
            return a == e or (e in a and len(a) <= len(e) + 6 and not any(w in a for w in ("不是", "并非", "不要")))
        return a == e
    return actual == expected


def matches(task, matcher):
    if task.get("tool_name") != matcher["tool"]:
        return False
    arguments = task.get("arguments", {})
    if not all(equivalent(arguments.get(k), value, k) for k, value in matcher.get("arguments", {}).items()):
        return False
    text = str(task.get("description", "")) + json.dumps(arguments, ensure_ascii=False)
    if matcher.get("text_any") and not any(term in text for term in matcher["text_any"]):
        return False
    return True


def graph_structure(tasks):
    from app.services.agent.contracts import ARGUMENT_MODELS
    from pydantic import ValidationError
    ids = [str(t.get("step_id")) for t in tasks]
    reasons = []
    if len(ids) != len(set(ids)):
        reasons.append("duplicate_node_id")
    parents = {str(t["step_id"]): {str(d) for d in t.get("depends_on", [])} for t in tasks}
    if any(dependency not in parents for values in parents.values() for dependency in values):
        reasons.append("unknown_dependency")
    if any(t.get("tool_name") not in REGISTERED_TOOLS for t in tasks):
        reasons.append("unknown_tool")
    for task in tasks:
        name = task.get("tool_name")
        if name in ARGUMENT_MODELS:
            try:
                ARGUMENT_MODELS[name].model_validate(task.get("arguments", {}))
            except ValidationError as exc:
                # Missing fields can legitimately await clarification. Provided
                # fields must nevertheless conform to the actual tool contract.
                if any(error["type"] != "missing" for error in exc.errors(include_input=False)):
                    reasons.append("invalid_tool_arguments")
    ancestors, active = {}, set()
    def visit(node):
        if node in active:
            raise ValueError("cycle")
        if node in ancestors:
            return ancestors[node]
        active.add(node)
        found = set()
        for dependency in parents.get(node, ()):
            found.add(dependency)
            found.update(visit(dependency))
        active.remove(node)
        ancestors[node] = found
        return found
    try:
        for node in parents:
            visit(node)
    except ValueError:
        reasons.append("cycle")
    return not reasons, ancestors, reasons


def align_goals(goals, tasks):
    """Maximize covered goals; only explicitly mergeable goals may share a node."""
    candidates = {g["goal_id"]: [i for i, task in enumerate(tasks) if any(matches(task, m) for m in g["any_of"])] for g in goals}
    ordered = sorted(goals, key=lambda g: (len(candidates[g["goal_id"]]), g["goal_id"]))
    best = {}
    def search(index, mapping, used):
        nonlocal best
        if len(mapping) + len(ordered) - index <= len(best):
            return
        if index == len(ordered):
            best = dict(mapping)
            return
        goal = ordered[index]
        name = goal["goal_id"]
        for node in candidates[name]:
            previous = used.get(node, [])
            if previous and not (goal.get("allow_shared_node") and all(p.get("allow_shared_node") for p in previous)):
                continue
            mapping[name] = node
            used[node] = previous + [goal]
            search(index + 1, mapping, used)
            if previous:
                used[node] = previous
            else:
                used.pop(node, None)
            mapping.pop(name)
        search(index + 1, mapping, used)
    search(0, {}, {})
    return best


def condition_match(task, required, source_id):
    condition = task.get("condition") or task.get("when") or task.get("precondition")
    if not isinstance(condition, dict):
        return False
    aliases = {"==": "eq", "equals": "eq", "equal": "eq", "!=": "ne", "not_equal": "ne",
               ">": "gt", "greater_than": "gt", ">=": "gte", "greater_or_equal": "gte",
               "<=": "lte", "less_or_equal": "lte", "in": "in"}
    operator = condition.get("operator", condition.get("op"))
    operator = aliases.get(operator, operator)
    source = condition.get("source_task", condition.get("source_step", condition.get("source_step_id")))
    field = str(condition.get("field", "")).removeprefix("data.").removeprefix("order.")
    return (str(source) == str(source_id) and field == required["field"] and operator == required["operator"]
            and equivalent(condition.get("value"), required["value"]))


def score_one(public, label, prediction):
    plan = prediction.get("plan") or {}
    tasks = plan.get("subtasks", [])
    deep = label["expected_route"] == "Deep-Path"
    route_correct = prediction.get("observed_route") == label["expected_route"]
    evidence_ok = prediction["planner_calls"] >= 1 if deep and prediction["mode"] == "native" else prediction["planner_calls"] == 0 if not deep else False
    failures = []
    if not route_correct:
        failures.append("route_mismatch")
    if not evidence_ok:
        failures.append("planner_call_contract")
    if prediction.get("error"):
        failures.append("inference_error:" + prediction["error"]["type"])
    if not deep and label.get("expected_intent") != plan.get("intent_category"):
        failures.append("fast_destination_mismatch")
    structure_ok, ancestors, structural_errors = graph_structure(tasks)
    if deep and (not tasks or not prediction.get("plan")):
        structure_ok = False
        structural_errors.append("missing_dag")
    if deep and not structure_ok:
        failures.extend("dag:" + error for error in structural_errors)
    goals = label["required_goals"]
    alignment = align_goals(goals, tasks)
    missing = [g["goal_id"] for g in goals if g["goal_id"] not in alignment]
    if deep and missing:
        failures.append("missing_or_wrong_arguments:" + ",".join(missing))
    def node_id(goal_id):
        return str(tasks[alignment[goal_id]]["step_id"])
    correct_edges = 0
    edge_failures = []
    for before, after in label["must_precede"]:
        satisfied = (before in alignment and after in alignment and
                     node_id(before) in ancestors.get(node_id(after), set()))
        correct_edges += int(satisfied)
        if not satisfied:
            edge_failures.append([before, after])
    if edge_failures:
        failures.append("required_dependency")
    independent_ok = 0
    independence_failures = []
    for a, b in label["must_be_independent"]:
        satisfied = a in alignment and b in alignment and (
            node_id(a) not in ancestors.get(node_id(b), set()) and node_id(b) not in ancestors.get(node_id(a), set()))
        independent_ok += int(satisfied)
        if not satisfied:
            independence_failures.append([a, b])
    if independence_failures:
        failures.append("false_or_unverifiable_dependency")
    condition_ok = 0
    for condition in label["conditions"]:
        target, source = condition["target_goal"], condition["source_goal"]
        satisfied = target in alignment and source in alignment and condition_match(
            tasks[alignment[target]], condition, node_id(source))
        condition_ok += int(satisfied)
    if condition_ok != len(label["conditions"]):
        failures.append("missing_or_wrong_structured_condition")
    planned_actions = {t.get("tool_name") for t in tasks}
    if plan.get("primary_action"):
        planned_actions.add(plan["primary_action"].lower())
    if plan.get("intent_category") == "HUMAN_ESCALATION":
        planned_actions.add("transfer_to_human")
    forbidden = sorted(planned_actions & set(label["forbidden_tools"]))
    if forbidden:
        failures.append("forbidden_action")
    matched_nodes = set(alignment.values())
    extras = [i for i, task in enumerate(tasks) if i not in matched_nodes and task.get("tool_name") not in label["allowed_support_tools"]]
    # Fast policy descriptors are routing objects, not extra deep-planning tasks.
    if deep and extras:
        failures.append("unmatched_extra_task")
    known_order_ids = set(re.findall(r"ORD[-_][A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*", public.query + json.dumps(public.context, ensure_ascii=False), re.I))
    unknown_entities = [t["arguments"]["order_id"] for t in tasks if isinstance(t.get("arguments", {}).get("order_id"), str)
                        and t["arguments"]["order_id"].upper() not in {i.upper() for i in known_order_ids}]
    if unknown_entities:
        failures.append("ungrounded_order_entity")
    if prediction.get("business_handler_calls") != 0:
        failures.append("unexpected_business_execution")
    return {"case_id": label["case_id"], "repeat": prediction["repeat"], "group": label["group"],
        "scope": label["scope"], "capability_gaps": label["capability_gaps"], "query": public.query,
        "expected_route": label["expected_route"], "observed_route": prediction["observed_route"],
        "route_correct": route_correct, "planner_call_contract": evidence_ok,
        "passed": not failures, "failures": failures, "inference_error": prediction.get("error"),
        "dag_structure_valid": structure_ok if deep else None,
        "goals_expected": len(goals), "goals_covered": len(alignment), "all_goals_covered": not missing if deep else None,
        "goal_alignment": {goal: tasks[index]["step_id"] for goal, index in alignment.items()},
        "missing_goals": missing, "dependencies_expected": len(label["must_precede"]), "dependencies_correct": correct_edges,
        "independence_expected": len(label["must_be_independent"]), "independence_correct": independent_ok,
        "conditions_expected": len(label["conditions"]), "conditions_correct": condition_ok,
        "extra_tasks": len(extras) if deep else 0, "task_count": len(tasks),
        "forbidden_actions": forbidden, "ungrounded_entities": unknown_entities,
        "route_latency_ms": prediction["route_latency_ms"], "planning_latency_ms": prediction["planning_latency_ms"],
        "tokens": sum(call.get("response", {}).get("usage", {}).get("total_tokens", 0) for call in prediction["calls"])}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def percentile(values, fraction):
    values = sorted(v for v in values if v is not None)
    return values[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def summarize(rows):
    fast = [r for r in rows if r["expected_route"] == "Fast-Path"]
    deep = [r for r in rows if r["expected_route"] == "Deep-Path"]
    return {"predictions": len(rows), "passed": sum(r["passed"] for r in rows),
        "pass_rate": ratio(sum(r["passed"] for r in rows), len(rows)),
        "route_accuracy": ratio(sum(r["route_correct"] for r in rows), len(rows)),
        "fast_misrouted": sum(not r["route_correct"] for r in fast), "fast_count": len(fast),
        "deep_misrouted": sum(not r["route_correct"] for r in deep), "deep_count": len(deep),
        "inference_errors": sum(r["inference_error"] is not None for r in rows),
        "complete_goal_coverage": ratio(sum(r["all_goals_covered"] for r in deep), len(deep)),
        "goal_recall": ratio(sum(r["goals_covered"] for r in deep), sum(r["goals_expected"] for r in deep)),
        "dag_structure_validity": ratio(sum(r["dag_structure_valid"] for r in deep), len(deep)),
        "required_dependency_rate": ratio(sum(r["dependencies_correct"] for r in rows), sum(r["dependencies_expected"] for r in rows)),
        "independence_rate": ratio(sum(r["independence_correct"] for r in rows), sum(r["independence_expected"] for r in rows)),
        "structured_condition_rate": ratio(sum(r["conditions_correct"] for r in rows), sum(r["conditions_expected"] for r in rows)),
        "extra_task_rate": ratio(sum(r["extra_tasks"] for r in deep), sum(r["task_count"] for r in deep)),
        "forbidden_action_predictions": sum(bool(r["forbidden_actions"]) for r in rows),
        "ungrounded_entity_predictions": sum(bool(r["ungrounded_entities"]) for r in rows),
        "route_latency_p95_ms": percentile([r["route_latency_ms"] for r in rows], .95),
        "fast_end_to_plan_p95_ms": percentile([r["planning_latency_ms"] for r in fast], .95),
        "deep_end_to_plan_p95_ms": percentile([r["planning_latency_ms"] for r in deep], .95),
        "reported_tokens": sum(r["tokens"] for r in rows)}


def markdown_report(report, cases):
    def pct(value):
        return "不适用" if value is None else f"{value:.1%}"
    total = report["overall"]
    lines = ["# 路由与 Planner 联合盲测结果", "", f"模型：`{report['model']}`；运行方式：`{report['mode']}`。",
        f"固定用例 {report['unique_cases']} 条，每条 {report['repeats']} 次，共 {total['predictions']} 次。",
        "", "## 主要结果", "", "| 指标 | 结果 |", "|---|---:|",
        f"| 全项通过 | {total['passed']}/{total['predictions']}（{pct(total['pass_rate'])}） |",
        f"| 路由准确率 | {pct(total['route_accuracy'])} |",
        f"| Fast 误入 Deep | {total['fast_misrouted']}/{total['fast_count']} |",
        f"| Deep 误入 Fast | {total['deep_misrouted']}/{total['deep_count']} |",
        f"| Deep 目标完整覆盖率 | {pct(total['complete_goal_coverage'])} |",
        f"| Deep DAG 结构合法率 | {pct(total['dag_structure_validity'])} |",
        f"| 必要先后关系满足率 | {pct(total['required_dependency_rate'])} |",
        f"| 独立任务关系满足率 | {pct(total['independence_rate'])} |",
        f"| 结构化条件满足率 | {pct(total['structured_condition_rate'])} |",
        f"| 推理错误 | {total['inference_errors']} |",
        f"| 禁止动作被规划 | {total['forbidden_action_predictions']} 次 |",
        f"| 无依据订单实体 | {total['ungrounded_entity_predictions']} 次 |",
        f"| 路由判断 P95 | {total['route_latency_p95_ms']:.3f} ms |",
        f"| 预期 Fast 请求至规划返回 P95（包含误入慢通道） | {total['fast_end_to_plan_p95_ms'] / 1000:.2f} s |",
        f"| Deep 请求至规划完成 P95 | {total['deep_end_to_plan_p95_ms'] / 1000:.2f} s |",
        f"| 已上报模型 Token | {total['reported_tokens']} |", "",
        "完整通过要求路由、调用证据、目标、实体、依赖、独立性、条件、冗余和禁止动作全部合格。所有目标能力缺口均计入失败，没有跳过。",
        "", "## 按类别", "", "| 类别 | 次数 | 路由准确率 | 全项通过率 | 目标完整覆盖率 |", "|---|---:|---:|---:|---:|"]
    for name, value in report["by_group"].items():
        lines.append(f"| {name} | {value['predictions']} | {pct(value['route_accuracy'])} | {pct(value['pass_rate'])} | {pct(value['complete_goal_coverage'])} |")
    lines += ["", "## 按能力范围", "", "| 范围 | 次数 | 路由准确率 | 全项通过率 |", "|---|---:|---:|---:|"]
    for name, value in report["by_scope"].items():
        lines.append(f"| {name} | {value['predictions']} | {pct(value['route_accuracy'])} | {pct(value['pass_rate'])} |")
    lines += ["", "## 失败归因与结论", "",
        "本次结果未达到设计方案提出的路由、目标覆盖、依赖、并行与条件分支验收门槛。",
        "", "1. **路由覆盖不足且缺少组合语义判断。**‘周末客服也上班吗？’等简单问题进入 Deep；含‘政策/规则’的复合请求被提前送入 Fast，后续业务目标丢失。",
        "2. **否定转人工被错误匹配。**‘不要转人工，先查物流，再开票’被判为立即人工转接，属于禁止动作误规划。",
        "3. **顺序约束没有稳定落实到图。**部分计划的 summary 写了‘最后查询物流’，实际物流节点却只依赖查单，没有依赖开票节点。评分使用图结构而非 summary 中的承诺。",
        "4. **输出契约存在冲突。**生产 Schema 向模型提供 CLARIFICATION 类型，但 DAG 校验器要求每个节点严格匹配 READ_TOOL/WRITE_TOOL/KNOWLEDGE_QA，澄清节点因此被拒绝。",
        "5. **结构化条件与业务工具仍有缺口。**TaskPlan 缺少可执行条件字段，库存、余额、报修等工具未完整注册；目标能力验收保留这些失败。",
        "", "校验错误统计："]
    for reason, count in report["validation_error_reasons"].items():
        lines.append(f"- {reason}：{count} 次。")
    lines += ["", "建议修复优先级：先处理路由的否定/复合意图，再统一澄清节点契约和任务类型校验，随后补充条件表达与缺失工具，最后优化图依赖。此次测试没有修改生产实现，也没有按答案选择性重跑。"]
    lines += ["", "## 三次重复稳定性", "", f"所有重复均通过的用例：{report['all_repeats_passed_cases']}/{report['unique_cases']}。",
              f"所有重复路由均正确的用例：{report['all_repeats_route_correct_cases']}/{report['unique_cases']}。",
              "", "## 盲测与审计", "",
              "- 输入与答案分别存储；推理进程禁止读取答案目录与数据集生成器。",
              "- 模型只接收原始问题、业务上下文、生产系统提示词和生产工具 Schema，不接收答案、类别、标签、评分规则或用例 ID。",
              "- 全部推理完成后生成输出指纹，评分进程随后才读取答案；评分不调用模型。",
              "- 被测生产文件在测试前后指纹一致；没有根据测试答案调整路由或提示词。",
              "- 没有执行业务处理器，仅调用真实 Planner；并行指标评价计划中的独立性，不代表执行器并发。",
              f"- 输入 SHA256：`{report['input_sha256']}`。",
              f"- 答案 SHA256：`{report['answer_key_sha256']}`。",
              f"- 输出 SHA256：`{report['prediction_sha256']}`。",
              "", "## 判定边界", "",
              "- 通道按实际 fast_route 决策测量。Fast 简单知识描述对象不视作复杂规划；Deep 要有 submit_plan 调用证据。",
              "- 必要依赖按图的可达性判断；允许独立节点交换顺序。明确允许合并的知识目标可共用节点。",
              "- 精确业务实体及已提供参数用代码匹配；政策主题用预先冻结关键词组匹配。没有用另一个模型主观打分。",
              "- 报修、库存、余额等目标在现有注册工具中尚不完整，列入 target_capability，保留失败以表示功能缺口。",
              "- 当前生产计划 Schema 不支持结构化条件；自然语言写到‘如果’不能替代可执行条件。",
              "- 路由 P95 只测 fast_route 函数自身，不含状态库、知识检索或网页回复；不能据此宣称端到端回复达到毫秒级。",
              "- 本结果验证当前版本在该固定集上的表现，不构成独立第三方认证。",
              "", "## 逐 Case 结果", "", "| Case | 类别 | 问题 | 通过次数 | 主要失败项 |", "|---|---|---|---:|---|"]
    for case in cases:
        query = case["query"].replace("|", "／").replace("\n", " ")
        reasons = "；".join(case["failure_counts"])
        lines.append(f"| {case['case_id']} | {case['group']} | {query} | {case['passed_repeats']}/{report['repeats']} | {reasons or '—'} |")
    return "\n".join(lines) + "\n"


def run(args):
    run_dir = Path(args.run_dir)
    # The complete inference seal is checked before any reference file is opened.
    seal = json.loads((run_dir / "inference_seal.json").read_text(encoding="utf-8"))
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    predictions_path = run_dir / "predictions.jsonl"
    assert seal["status"] == "complete" and seal["sources_unchanged"]
    assert not seal["reference_reads_blocked"] and not seal["reference_answers_loaded"]
    assert seal["input_sha256"] == manifest["public_sha256"] == file_hash(DATASET / "inputs.jsonl")
    assert seal["sources_before"] == manifest["source_hashes"]
    assert seal["prediction_sha256"] == file_hash(predictions_path)
    predictions = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines()]
    assert len(predictions) == seal["expected_predictions"]
    pairs = {(p["case_id"], p["repeat"]) for p in predictions}
    assert len(pairs) == len(predictions)
    public = {case.case_id: case for case in read_public(DATASET / "inputs.jsonl")}
    assert pairs == {(identifier, repeat) for identifier in public for repeat in range(1, seal["repeats"] + 1)}
    for prediction in predictions:
        for call in prediction["calls"]:
            request = json.dumps(call["request"], ensure_ascii=False)
            assert all(forbidden not in request for forbidden in ("expected_route", "required_goals", "must_precede", "must_be_independent", "capability_gaps", prediction["case_id"]))
    key_path = DATASET / "private/answer_key.jsonl"
    assert manifest["answer_key_sha256"] == file_hash(key_path)
    scoring_started = datetime.now(timezone.utc).isoformat()
    assert scoring_started > seal["finished_at"]
    labels = {row["case_id"]: row for row in (json.loads(line) for line in key_path.read_text(encoding="utf-8").splitlines())}
    assert public.keys() == labels.keys()
    rows = [score_one(public[p["case_id"]], labels[p["case_id"]], p) for p in predictions]
    # Replay validation locally for diagnostics only; no model is called and no
    # sealed prediction is altered by this post-inference analysis.
    from app.services.agent.planning import TaskPlan
    from pydantic import ValidationError
    validation_reasons = Counter()
    for prediction in predictions:
        if (prediction.get("error") or {}).get("type") == "ValidationError":
            for call in prediction["calls"]:
                if call.get("response"):
                    try:
                        TaskPlan.model_validate(call["response"]["arguments"])
                    except ValidationError as exc:
                        validation_reasons.update(error["msg"] for error in exc.errors(include_input=False))
    case_rows = []
    for identifier, label in labels.items():
        trials = [row for row in rows if row["case_id"] == identifier]
        case_rows.append({"case_id": identifier, "query": public[identifier].query,
                          "group": label["group"], "scope": label["scope"],
                          "passed_repeats": sum(t["passed"] for t in trials),
                          "route_correct_repeats": sum(t["route_correct"] for t in trials),
                          "failure_counts": dict(Counter(f for t in trials for f in t["failures"]))})
    report = {"mode": seal["mode"], "model": seal["model"], "repeats": seal["repeats"], "unique_cases": len(public),
        "inference_started_at": seal["started_at"], "inference_finished_at": seal["finished_at"], "scoring_started_at": scoring_started,
        "input_sha256": seal["input_sha256"], "answer_key_sha256": manifest["answer_key_sha256"],
        "prediction_sha256": seal["prediction_sha256"], "overall": summarize(rows),
        "by_group": {name: summarize([r for r in rows if r["group"] == name]) for name in manifest["groups"]},
        "by_scope": {name: summarize([r for r in rows if r["scope"] == name]) for name in manifest["scopes"]},
        "all_repeats_passed_cases": sum(c["passed_repeats"] == seal["repeats"] for c in case_rows),
        "all_repeats_route_correct_cases": sum(c["route_correct_repeats"] == seal["repeats"] for c in case_rows),
        "failure_counts": dict(Counter(f for row in rows for f in row["failures"])), "cases": case_rows, "trials": rows}
    report["validation_error_reasons"] = dict(validation_reasons)
    report["scorer_sha256"] = file_hash(__file__)
    report["business_handler_calls"] = 0
    report["native_planner_calls"] = sum(p["planner_calls"] for p in predictions)
    overall = report["overall"]
    thresholds = {"route_accuracy": .98, "complete_goal_coverage": .95, "dag_structure_validity": 1,
                  "required_dependency_rate": .98, "independence_rate": .95, "structured_condition_rate": .95}
    report["acceptance"] = {name: {"required": limit, "actual": overall[name],
                            "passed": overall[name] is not None and overall[name] >= limit}
                            for name, limit in thresholds.items()}
    report["acceptance"]["forbidden_actions"] = {"required": 0, "actual": overall["forbidden_action_predictions"],
                                                  "passed": overall["forbidden_action_predictions"] == 0}
    report["acceptance_passed"] = all(item["passed"] for item in report["acceptance"].values())
    write_json(run_dir / "report.json", report)
    (run_dir / "REPORT.md").write_text(markdown_report(report, case_rows), encoding="utf-8")
    with (run_dir / "case_results.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "group", "scope", "query", "passed_repeats", "route_correct_repeats", "failure_counts"])
        writer.writeheader()
        for case in case_rows:
            writer.writerow({**case, "failure_counts": json.dumps(case["failure_counts"], ensure_ascii=False)})
    print(json.dumps({"report": str(run_dir / "REPORT.md"), "overall": report["overall"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    run(parser.parse_args())
