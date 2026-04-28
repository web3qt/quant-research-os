from pathlib import Path

from tests.agent_eval.tss_agent_behavior_helpers import (
    assert_tss_reject_case_fails_if_review_transition_starts,
    assert_tss_reject_case_passes_without_review_transition,
    assert_tss_success_case_fails_when_semantic_validator_missing,
    assert_tss_success_case_requires_validators_before_review,
)


def test_tss_test_evidence_success_case_requires_validators_before_review(tmp_path: Path) -> None:
    assert_tss_success_case_requires_validators_before_review("tss_test_evidence", tmp_path)


def test_tss_test_evidence_success_case_fails_when_semantic_validator_call_is_missing(tmp_path: Path) -> None:
    assert_tss_success_case_fails_when_semantic_validator_missing("tss_test_evidence", tmp_path)


def test_tss_test_evidence_reject_case_fails_if_review_transition_starts(tmp_path: Path) -> None:
    assert_tss_reject_case_fails_if_review_transition_starts("tss_test_evidence", tmp_path)


def test_tss_test_evidence_reject_case_passes_without_review_transition(tmp_path: Path) -> None:
    assert_tss_reject_case_passes_without_review_transition("tss_test_evidence", tmp_path)
