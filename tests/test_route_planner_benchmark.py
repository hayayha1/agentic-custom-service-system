"""Synthetic checker tests, independent of the sealed evaluation answer key."""
import json
import subprocess
import sys

import pytest

from scripts.route_planner_common import ROOT, PublicCase
from scripts.score_route_planner import align_goals, condition_match, graph_structure, score_one


def task(step, name="query_orders", order="ORD-UNIT-1", deps=()):
    return {"step_id": step, "tool_name": name, "description": "synthetic task",
            "arguments": {"order_id": order}, "depends_on": list(deps)}


def goal(name, order="ORD-UNIT-1", shared=False):
    return {"goal_id": name, "any_of": [{"tool": "query_orders", "arguments": {"order_id": order}}],
            "allow_shared_node": shared}


def test_public_schema_refuses_answers():
    with pytest.raises(ValueError):
        PublicCase(case_id="rp_123456abcdef", query="unit input", expected_route="Fast-Path")


def test_checker_uses_transitive_reachability():
    valid, ancestors, errors = graph_structure([task(10), task(20, deps=[10]), task(30, deps=[20])])
    assert valid and not errors
    assert "10" in ancestors["30"]
    assert "30" not in ancestors["10"]


@pytest.mark.parametrize("tasks", [[task(1, deps=[1])], [task(1), task(1)], [task(1, deps=[99])]])
def test_checker_rejects_invalid_graph(tasks):
    assert not graph_structure(tasks)[0]


def test_checker_preserves_multiple_entities_and_multiplicity():
    goals = [goal("first", "ORD-UNIT-1"), goal("second", "ORD-UNIT-2")]
    assert len(align_goals(goals, [task(1)])) == 1
    assert len(align_goals(goals, [task(1), task(2, order="ORD-UNIT-2")])) == 2
    assert len(align_goals([goal("a"), goal("b")], [task(1)])) == 1
    assert len(align_goals([goal("a", shared=True), goal("b", shared=True)], [task(1)])) == 2


def test_checker_requires_structured_condition_not_prose():
    required = {"field": "status", "operator": "eq", "value": "PAID"}
    assert not condition_match({"description": "if PAID, refund"}, required, 1)
    assert condition_match({"condition": {"source_task": 1, "field": "status", "operator": "==", "value": "PAID"}}, required, 1)


def test_checker_accepts_missing_slots_but_rejects_invented_parameters():
    partial = {**task(1, "apply_invoice"), "arguments": {"order_id": "ORD-UNIT-1"}}
    assert graph_structure([partial])[0]
    invented = {**partial, "arguments": {"order_id": "ORD-UNIT-1", "invoice_type": "special"}}
    assert not graph_structure([invented])[0]


def test_checker_rejects_false_dependency():
    public = PublicCase(case_id="rp_123456abcdef", query="ORD-UNIT-1 ORD-UNIT-2")
    label = {"case_id": public.case_id, "group": "deep_parallel", "scope": "current_regression", "capability_gaps": [],
             "expected_route": "Deep-Path", "expected_intent": None,
             "required_goals": [goal("a"), goal("b", "ORD-UNIT-2")], "must_precede": [],
             "must_be_independent": [["a", "b"]], "conditions": [], "forbidden_tools": [], "allowed_support_tools": []}
    prediction = {"repeat": 1, "mode": "native", "observed_route": "Deep-Path", "planner_calls": 1,
                  "plan": {"subtasks": [task(1), task(2, order="ORD-UNIT-2", deps=[1])]}, "error": None,
                  "calls": [], "route_latency_ms": 1, "planning_latency_ms": 10, "business_handler_calls": 0}
    row = score_one(public, label, prediction)
    assert row["all_goals_covered"]
    assert not row["passed"]
    assert row["independence_correct"] == 0


def test_forbidden_handoff_is_counted_even_without_a_task_node():
    public = PublicCase(case_id="rp_123456abcdef", query="Do not transfer")
    label = {"case_id": public.case_id, "group": "deep_mixed", "scope": "current_regression", "capability_gaps": [],
             "expected_route": "Deep-Path", "expected_intent": None, "required_goals": [], "must_precede": [],
             "must_be_independent": [], "conditions": [], "forbidden_tools": ["transfer_to_human"], "allowed_support_tools": []}
    prediction = {"repeat": 1, "mode": "native", "observed_route": "Fast-Path", "planner_calls": 0,
                  "plan": {"intent_category": "HUMAN_ESCALATION", "primary_action": "TRANSFER_TO_HUMAN", "subtasks": []},
                  "error": None, "calls": [], "route_latency_ms": 1, "planning_latency_ms": 1, "business_handler_calls": 0}
    assert score_one(public, label, prediction)["forbidden_actions"] == ["transfer_to_human"]


@pytest.mark.parametrize("directory", ["private", "results"])
def test_inference_read_guard_blocks_reference_directory(directory):
    code = f"from scripts.run_route_planner_blind import install_read_guard; from scripts.route_planner_common import DATASET; install_read_guard(); (DATASET/'{directory}'/'unit_fake_answer_key.jsonl').read_text()"
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert "Blind inference cannot read reference answers" in result.stderr
