from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate
from tests.runtime.test_csf_data_ready_runtime import (
    _csf_data_ready_draft,
    _prepare_mandate_stage,
    _write_yaml,
)


FIXTURES = Path("tests/agent_eval/fixtures")
CASES = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def _load_case(case_id: str) -> dict:
    payload = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}[case_id]


def _build_valid_csf_data_ready_lineage(lineage_root: Path) -> None:
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)


def test_csf_data_ready_success_case_requires_validator_before_review(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_data_ready_runs_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _build_valid_csf_data_ready_lineage(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_data_ready_success_with_validator.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []


def test_csf_data_ready_success_case_fails_when_validator_call_is_missing(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_data_ready_runs_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _build_valid_csf_data_ready_lineage(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_data_ready_missing_validator.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "ordered event substring missing: qros-validate-stage --stage csf_data_ready" in result.errors


def test_csf_data_ready_reject_case_fails_if_review_transition_starts(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_data_ready_rejects_non_csf_mandate")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_data_ready_illegal_review_transition.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "forbidden event substring observed: qros-review-cycle prepare" in result.errors


def test_csf_data_ready_reject_case_passes_without_review_transition(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_data_ready_rejects_unconfirmed_freeze_groups")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_data_ready_rejects_gate.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []
