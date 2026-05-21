from __future__ import annotations

import json
from pathlib import Path

from runtime.tools.review_eligibility import ReviewEligibilityStatus, compute_review_eligibility


def test_compute_review_eligibility_blocks_semantic_fail(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps(
            {
                "semantic_gate": {
                    "status": "fail",
                    "reason_code": "CSF_TEST_EVIDENCE_METRIC_FAIL",
                    "reason": "mean_rank_ic <= 0",
                }
            }
        ),
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="CSF_TEST_EVIDENCE_METRIC_FAIL",
        blocking_reason="mean_rank_ic <= 0",
        review_blocking_surface="semantic_gate",
        authorized_review_skill=None,
        requires_failure_handling=True,
        failure_stage="csf_test_evidence",
        failure_reason_summary="mean_rank_ic <= 0",
    )


def test_compute_review_eligibility_allows_clean_review_entry(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps({"semantic_gate": {"status": "pass"}}),
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_signal_ready",
        review_skill="qros-csf-signal-ready-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=True,
        blocking_reason_code=None,
        blocking_reason=None,
        review_blocking_surface=None,
        authorized_review_skill="qros-csf-signal-ready-review",
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
    )


def test_compute_review_eligibility_blocks_failure_package_and_preserves_failure_routing_context(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps(
            {
                "semantic_gate": {"status": "pass"},
                "failure_package": {
                    "reason_code": "FAILURE_PACKAGE_OPEN",
                    "reason": "Failure handling package is still active.",
                    "stage": "csf_data_ready",
                    "failure_reason_summary": "Route to failure handling before review.",
                },
            }
        ),
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="FAILURE_PACKAGE_OPEN",
        blocking_reason="Failure handling package is still active.",
        review_blocking_surface="failure_package",
        authorized_review_skill=None,
        requires_failure_handling=True,
        failure_stage="csf_data_ready",
        failure_reason_summary="Route to failure handling before review.",
    )


def test_compute_review_eligibility_blocks_malformed_failure_package_payload(
    tmp_path: Path,
) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps(
            {
                "semantic_gate": {"status": "pass"},
                "failure_package": {
                    "stage": "csf_signal_ready",
                    "failure_reason_summary": "Malformed failure package payload.",
                },
            }
        ),
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="MALFORMED_FAILURE_PACKAGE",
        blocking_reason="failure_package must include reason_code and reason.",
        review_blocking_surface="failure_package",
        authorized_review_skill=None,
        requires_failure_handling=True,
        failure_stage="csf_signal_ready",
        failure_reason_summary="Malformed failure package payload.",
    )


def test_compute_review_eligibility_blocks_invalid_json_truth_file(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="MALFORMED_REVIEW_ELIGIBILITY_JSON",
        blocking_reason=(
            "Invalid JSON in canonical review eligibility truth: "
            f"{lineage_root / 'review_eligibility.json'}"
        ),
        review_blocking_surface="semantic_gate",
        authorized_review_skill=None,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
    )


def test_compute_review_eligibility_blocks_non_object_truth_payload(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)
    (lineage_root / "review_eligibility.json").write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    status = compute_review_eligibility(
        lineage_root=lineage_root,
        current_stage="csf_test_evidence",
        review_skill="qros-csf-test-evidence-review",
    )

    assert status == ReviewEligibilityStatus(
        eligible_for_review=False,
        blocking_reason_code="MALFORMED_REVIEW_ELIGIBILITY_PAYLOAD",
        blocking_reason="Canonical review eligibility truth must be a JSON object.",
        review_blocking_surface="semantic_gate",
        authorized_review_skill=None,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
    )
