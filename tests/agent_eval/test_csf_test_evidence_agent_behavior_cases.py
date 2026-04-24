from __future__ import annotations

from pathlib import Path

import yaml

from tests.session.test_csf_test_evidence_artifact_shape import _prepare_valid_csf_test_evidence


FIXTURES = Path("tests/agent_eval/fixtures")
CASES = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def _load_case(case_id: str) -> dict:
    payload = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}[case_id]


def test_csf_test_evidence_success_case_requires_validators_before_review(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_test_evidence_runs_artifact_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _prepare_valid_csf_test_evidence(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_test_evidence_success_with_validators.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []


def test_csf_test_evidence_success_case_fails_when_semantic_validator_call_is_missing(
    tmp_path: Path,
) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_test_evidence_runs_semantic_validator_before_review")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    _prepare_valid_csf_test_evidence(lineage_root)

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_test_evidence_missing_semantic_validator.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "ordered event substring missing: csf_test_evidence semantic validator" in result.errors


def test_csf_test_evidence_reject_case_fails_if_review_transition_starts(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_test_evidence_rejects_variant_drift")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_test_evidence_illegal_review_transition.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "forbidden event substring observed: qros-review-cycle prepare" in result.errors


def test_csf_test_evidence_reject_case_passes_without_review_transition(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, parse_transcript_jsonl

    case = _load_case("csf_test_evidence_rejects_placeholder_rank_ic_completion")
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_csf_test_evidence_rejects_gate.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is True
    assert result.errors == []
