from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.agent_behavior_eval import AgentEvent, evaluate_behavior_case
from tests.helpers.stage_fixtures import (
    prepare_tss_backtest_ready,
    prepare_tss_data_ready,
    prepare_tss_holdout_validation,
    prepare_tss_signal_ready,
    prepare_tss_test_evidence,
    prepare_tss_train_freeze,
)


STAGE_BUILDERS = {
    "tss_data_ready": prepare_tss_data_ready,
    "tss_signal_ready": prepare_tss_signal_ready,
    "tss_train_freeze": prepare_tss_train_freeze,
    "tss_test_evidence": prepare_tss_test_evidence,
    "tss_backtest_ready": prepare_tss_backtest_ready,
    "tss_holdout_validation": prepare_tss_holdout_validation,
}

STAGE_SKILLS = {
    "tss_data_ready": "qros-tss-data-ready-author",
    "tss_signal_ready": "qros-tss-signal-ready-author",
    "tss_train_freeze": "qros-tss-train-freeze-author",
    "tss_test_evidence": "qros-tss-test-evidence-author",
    "tss_backtest_ready": "qros-tss-backtest-ready-author",
    "tss_holdout_validation": "qros-tss-holdout-validation-author",
}

CASES = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def assert_tss_success_case_requires_validators_before_review(stage: str, tmp_path: Path) -> None:
    case = load_tss_case(f"{stage}_runs_validators_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    STAGE_BUILDERS[stage](lineage_root)

    result = evaluate_behavior_case(case, _success_events(stage), lineage_root=lineage_root)

    assert result.passed is True
    assert result.errors == []


def assert_tss_success_case_fails_when_semantic_validator_missing(stage: str, tmp_path: Path) -> None:
    case = load_tss_case(f"{stage}_runs_validators_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    STAGE_BUILDERS[stage](lineage_root)

    result = evaluate_behavior_case(case, _missing_semantic_events(stage), lineage_root=lineage_root)

    assert result.passed is False
    assert f"ordered event substring missing: {stage} semantic validator" in result.errors


def assert_tss_reject_case_fails_if_review_transition_starts(stage: str, tmp_path: Path) -> None:
    case = load_tss_case(f"{stage}_rejects_gate")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(case, _illegal_review_events(stage), lineage_root=lineage_root)

    assert result.passed is False
    assert "forbidden event substring observed: qros-review-cycle prepare" in result.errors


def assert_tss_reject_case_passes_without_review_transition(stage: str, tmp_path: Path) -> None:
    case = load_tss_case(f"{stage}_rejects_gate")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(case, _reject_events(stage), lineage_root=lineage_root)

    assert result.passed is True
    assert result.errors == []


def load_tss_case(case_id: str) -> dict[str, Any]:
    payload = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}[case_id]


def _expected_events(stage: str, suffix: str) -> dict[str, list[str]]:
    if suffix == "rejects_gate":
        return {"forbidden_substrings": ["qros-review-cycle prepare", STAGE_SKILLS[stage].replace("-author", "-review")]}
    return {
        "ordered_substrings": [
            f"qros-validate-stage --stage {stage}",
            f"{stage} semantic validator",
            "qros-review-preflight",
            "qros-review-cycle prepare",
        ]
    }


def _success_events(stage: str) -> list[AgentEvent]:
    return [
        _skill_event(stage),
        _command_event(f"qros-validate-stage --stage {stage} --lineage-id agent_eval_{stage}"),
        _command_event(f"{stage} semantic validator passed"),
        _command_event(f"qros-review-preflight --stage {stage}"),
        _command_event(f"qros-review-cycle prepare --stage {stage}"),
    ]


def _missing_semantic_events(stage: str) -> list[AgentEvent]:
    return [
        _skill_event(stage),
        _command_event(f"qros-validate-stage --stage {stage} --lineage-id agent_eval_{stage}"),
        _command_event(f"qros-review-preflight --stage {stage}"),
        _command_event(f"qros-review-cycle prepare --stage {stage}"),
    ]


def _illegal_review_events(stage: str) -> list[AgentEvent]:
    return [
        _skill_event(stage),
        _command_event(f"qros-review-cycle prepare --stage {stage}"),
    ]


def _reject_events(stage: str) -> list[AgentEvent]:
    return [
        _skill_event(stage),
        _command_event(f"qros-review-preflight --stage {stage}"),
        _command_event(f"{stage} gate rejected before review"),
    ]


def _skill_event(stage: str) -> AgentEvent:
    skill = STAGE_SKILLS[stage]
    raw = {"event_type": "skill_call", "name": skill, "payload": {"skill": skill}}
    return AgentEvent(event_type="skill_call", name=skill, payload={"skill": skill}, raw=raw)


def _command_event(command: str) -> AgentEvent:
    raw = {"event_type": "tool_call", "name": "command_execution", "payload": {"command": command}}
    return AgentEvent(event_type="tool_call", name="command_execution", payload={"command": command}, raw=raw)
