from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.csf_signal_ready_runtime import build_csf_signal_ready_from_data_ready, scaffold_csf_signal_ready
from tests.runtime.test_csf_signal_ready_semantic_validation import _valid_draft
from tests.runtime.test_csf_signal_ready_runtime import _prepare_csf_data_ready_stage, _write_yaml


FIXTURES = Path("tests/agent_eval/fixtures")
CASES = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def _load_case(case_id: str) -> dict:
    payload = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}[case_id]


def _build_valid_csf_signal_ready_lineage(lineage_root: Path) -> None:
    _prepare_csf_data_ready_stage(lineage_root)
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", _valid_draft())
    build_csf_signal_ready_from_data_ready(lineage_root)


def test_csf_signal_ready_success_case_requires_validators_before_review(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_signal_ready_runs_artifact_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _build_valid_csf_signal_ready_lineage(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_signal_ready_success_with_validators.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []


def test_csf_signal_ready_success_case_fails_when_semantic_validator_call_is_missing(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_signal_ready_runs_semantic_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _build_valid_csf_signal_ready_lineage(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_signal_ready_missing_semantic_validator.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "ordered event substring missing: csf_signal_ready semantic validator" in result.errors


def test_csf_signal_ready_reject_case_fails_if_review_transition_starts(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_signal_ready_rejects_non_csf_mandate_route")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_signal_ready_illegal_review_transition.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "forbidden event substring observed: qros-review-cycle prepare" in result.errors


def test_csf_signal_ready_reject_case_passes_without_review_transition(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_signal_ready_rejects_raw_field_without_input_binding")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_signal_ready_rejects_gate.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []
