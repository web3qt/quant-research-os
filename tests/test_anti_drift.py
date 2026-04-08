from pathlib import Path

from tools.anti_drift import (
    SCHEMA_VERSION,
    SNAPSHOT_VERSION,
    canonical_snapshot_from_session_context,
    session_stage_to_gate_stage,
)
from tools.research_session import summarize_session_status


def test_session_stage_to_gate_stage_normalizes_runtime_suffixes() -> None:
    assert session_stage_to_gate_stage("data_ready_review") == "data_ready"
    assert session_stage_to_gate_stage("data_ready_confirmation_pending") == "data_ready"
    assert session_stage_to_gate_stage("train_freeze_author") == "train_calibration"
    assert session_stage_to_gate_stage("csf_holdout_validation_review_complete") == "csf_holdout_validation"


def test_canonical_snapshot_preserves_semantic_fields_for_review_stage() -> None:
    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=Path("/tmp/outputs/btc_leads_alts"),
        lineage_mode="explicit_resume",
        lineage_selection_reason="Explicit lineage_id btc_leads_alts was provided, so qros-session is targeting that lineage directly.",
        current_stage="data_ready_review",
        current_route="time_series_signal",
        artifacts_written=["02_data_ready/dataset_manifest.json"],
        gate_status="REVIEW_PENDING",
        next_action="Write review_findings.yaml and run data_ready review",
        open_risks=["dataset manifest missing peer coverage note"],
    )

    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-review-core",
        evidence_refs=("tests/test_anti_drift.py::test_canonical_snapshot_preserves_semantic_fields_for_review_stage",),
    )

    assert snapshot.fixture_id == "data-ready-review-core"
    assert snapshot.snapshot_version == SNAPSHOT_VERSION
    assert snapshot.schema_version == SCHEMA_VERSION
    assert snapshot.route_skill == "qros-data-ready-review"
    assert snapshot.stage_id == "data_ready"
    assert snapshot.session_stage == "data_ready_review"
    assert snapshot.formal_decision == "REVIEW_PENDING"
    assert "dataset_manifest.json" in snapshot.required_artifacts
    assert snapshot.downstream_permissions == ("signal_ready",)
    assert snapshot.blocking_reasons == (
        "data_ready is ready for independent adversarial review, but adversarial_review_request.yaml is missing.",
        "dataset manifest missing peer coverage note",
    )


def test_canonical_snapshot_uses_review_verdict_for_failure_handling() -> None:
    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=Path("/tmp/outputs/btc_leads_alts"),
        lineage_mode="explicit_resume",
        lineage_selection_reason="Explicit lineage_id btc_leads_alts was provided, so qros-session is targeting that lineage directly.",
        current_stage="test_evidence_review",
        current_route="time_series_signal",
        artifacts_written=["05_test_evidence/test_gate_table.csv"],
        gate_status="REVIEW_PENDING",
        next_action="Enter failure handling for test_evidence via qros-stage-failure-handler",
        review_verdict="RETRY",
        requires_failure_handling=True,
        failure_stage="test_evidence",
        failure_reason_summary="Review verdict blocks progression.",
    )

    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry",
        failure_class="REPRO_FAIL",
        severity="FAIL-SOFT",
    )

    assert snapshot.route_skill == "qros-stage-failure-handler"
    assert snapshot.stage_id == "test_evidence"
    assert snapshot.formal_decision == "RETRY"
    assert snapshot.failure_class == "REPRO_FAIL"
    assert snapshot.severity == "FAIL-SOFT"
    assert snapshot.blocking_reasons == ("Normal progression is blocked by review verdict RETRY.",)
