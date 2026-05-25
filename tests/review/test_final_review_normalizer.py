from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.final_review_normalizer import (
    FORBIDDEN_FINAL_REVIEW_NORMALIZATION,
    NORMALIZED_FINAL_REVIEW_FILENAME,
    normalize_final_review_payload,
    write_normalized_final_review,
)


def _request() -> dict:
    return {
        "review_cycle_id": "review-cycle-001",
        "lineage_id": "lineage-alpha",
        "stage": "csf_signal_ready",
        "author_identity": "author-agent",
        "required_program_dir": "program/cross_sectional_factor/signal_ready",
        "required_program_entrypoint": "run_stage.py",
        "stage_content_artifact_paths": [
            "factor_manifest.yaml",
            "factor_panel.parquet",
            "component_factor_manifest.yaml",
        ],
        "required_artifact_paths": [
            "factor_manifest.yaml",
            "factor_panel.parquet",
            "component_factor_manifest.yaml",
            "route_inheritance_contract.yaml",
        ],
        "required_provenance_paths": ["program_execution_manifest.json"],
    }


def _receipt() -> dict:
    return {
        "review_cycle_id": "review-cycle-001",
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "review-session-001",
        "reviewer_agent_id": "reviewer-child-agent",
        "execution_mode": "spawned_agent",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
    }


def _final_review() -> dict:
    return {
        "lineage_id": "lineage-alpha",
        "stage_id": "csf_signal_ready",
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewed_artifact_paths": [
            "factor_panel.parquet",
            "component_factor_manifest.yaml",
            "factor_manifest.yaml",
        ],
        "reviewed_program_path": "program/cross_sectional_factor/signal_ready/run_stage.py",
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "PASS",
        "review_summary": "Reviewer confirmed scoped stage content.",
        "blocking_findings": [],
        "reservation_findings": [{"id": "R1", "text": "clarify wording"}],
        "info_findings": ["scope matched"],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": "",
        "downstream_permissions": ["csf_signal_ready_next_stage_confirmation_pending"],
        "recommended_next_action": "advance_to_train_freeze",
    }


def test_normalize_final_review_sorts_scope_and_serializes_finding_objects() -> None:
    payload = normalize_final_review_payload(_final_review(), _request(), _receipt())

    assert payload["review_cycle_id"] == "review-cycle-001"
    assert payload["lineage_id"] == "lineage-alpha"
    assert payload["stage_id"] == "csf_signal_ready"
    assert payload["author_identity"] == "author-agent"
    assert payload["reviewer_identity"] == "reviewer-agent"
    assert payload["reviewer_session_id"] == "review-session-001"
    assert payload["reviewer_agent_id"] == "reviewer-child-agent"
    assert payload["reviewed_artifact_paths"] == [
        "component_factor_manifest.yaml",
        "factor_manifest.yaml",
        "factor_panel.parquet",
    ]
    assert payload["rollback_stage"] is None
    assert payload["reservation_findings"] == ['{"id":"R1","text":"clarify wording"}']


def test_normalize_final_review_rejects_unbound_reviewer_agent() -> None:
    final_review = _final_review()
    final_review["reviewer_agent_id"] = "other-agent"

    with pytest.raises(ValueError, match="reviewer_agent_id does not match reviewer_receipt.yaml"):
        normalize_final_review_payload(final_review, _request(), _receipt())


def test_normalize_final_review_rejects_unsupported_verdict() -> None:
    final_review = _final_review()
    final_review["verdict"] = "APPROVED"

    with pytest.raises(ValueError, match=f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: unsupported verdict"):
        normalize_final_review_payload(final_review, _request(), _receipt())


def test_normalize_final_review_rejects_receipt_review_cycle_mismatch() -> None:
    receipt = _receipt()
    receipt["review_cycle_id"] = "review-cycle-002"

    with pytest.raises(ValueError, match="review_cycle_id does not match reviewer_receipt.yaml"):
        normalize_final_review_payload(_final_review(), _request(), receipt)


def test_normalize_final_review_rejects_scope_mismatch() -> None:
    final_review = _final_review()
    final_review["reviewed_artifact_paths"] = ["factor_manifest.yaml", "factor_panel.parquet"]

    with pytest.raises(ValueError, match="reviewed_artifact_paths do not match active request scope"):
        normalize_final_review_payload(final_review, _request(), _receipt())


def test_normalize_final_review_rejects_missing_review_summary() -> None:
    final_review = _final_review()
    del final_review["review_summary"]

    with pytest.raises(ValueError, match=FORBIDDEN_FINAL_REVIEW_NORMALIZATION):
        normalize_final_review_payload(final_review, _request(), _receipt())


def test_write_normalized_final_review_preserves_raw_file(tmp_path: Path) -> None:
    stage_dir = tmp_path / "lineage-alpha" / "03_csf_signal_ready"
    raw_path = stage_dir / "review" / "final_review.yaml"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text("raw: reviewer-owned\n", encoding="utf-8")

    written_path = write_normalized_final_review(stage_dir, _final_review(), _request(), _receipt())

    assert written_path == stage_dir / "review" / "result" / NORMALIZED_FINAL_REVIEW_FILENAME
    assert raw_path.read_text(encoding="utf-8") == "raw: reviewer-owned\n"
    payload = yaml.safe_load(written_path.read_text(encoding="utf-8"))
    assert payload["review_summary"] == "Reviewer confirmed scoped stage content."
