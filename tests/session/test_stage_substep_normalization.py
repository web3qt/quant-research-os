from pathlib import Path

from runtime.tools.anti_drift import canonical_snapshot_from_session_context, session_stage_to_gate_stage
from runtime.tools.research_session import session_stage_base_name, summarize_session_status


def test_session_stage_base_name_supports_new_substep_suffixes() -> None:
    assert session_stage_base_name("data_ready_review_confirmation_pending") == "data_ready"
    assert session_stage_base_name("signal_ready_next_stage_confirmation_pending") == "signal_ready"
    assert session_stage_base_name("csf_backtest_ready_next_stage_confirmation_pending") == "csf_backtest_ready"


def test_session_stage_to_gate_stage_supports_new_substep_suffixes() -> None:
    assert session_stage_to_gate_stage("data_ready_review_confirmation_pending") == "data_ready"
    assert session_stage_to_gate_stage("holdout_validation_next_stage_confirmation_pending") == "holdout_validation"
    assert (
        session_stage_to_gate_stage("csf_holdout_validation_next_stage_confirmation_pending")
        == "csf_holdout_validation"
    )


def test_failure_routing_and_snapshot_shape_stay_stable_for_new_substep_labels() -> None:
    status = summarize_session_status(
        lineage_id="btc_leads_alts",
        lineage_root=Path("/tmp/outputs/btc_leads_alts"),
        lineage_mode="explicit_resume",
        lineage_selection_reason="Explicit lineage_id btc_leads_alts was provided, so qros-session is targeting that lineage directly.",
        current_stage="data_ready_review_confirmation_pending",
        current_route="time_series_signal",
        artifacts_written=[],
        gate_status="REVIEW_CONFIRMATION_PENDING",
        next_action="Await explicit review confirmation.",
        review_verdict="RETRY",
        requires_failure_handling=True,
        failure_stage="data_ready_review",
        failure_reason_summary="data_ready_review requires failure handling because review verdict is RETRY.",
    )

    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-review-confirm-retry",
        evidence_refs=("tests/session/test_stage_substep_normalization.py",),
    )

    assert status.next_action == "Enter failure handling for data_ready via qros-stage-failure-handler"
    assert snapshot.stage_id == "data_ready"
    assert snapshot.session_stage == "data_ready_review_confirmation_pending"
    assert snapshot.formal_decision == "RETRY"
    assert set(snapshot.to_dict()) == {
        "fixture_id",
        "input_digest",
        "snapshot_version",
        "schema_version",
        "lineage_mode",
        "lineage_selection_reason",
        "route_skill",
        "stage_id",
        "session_stage",
        "formal_decision",
        "required_artifacts",
        "downstream_permissions",
        "blocking_reasons",
        "lineage_transition",
        "evidence_refs",
        "failure_class",
        "severity",
    }
