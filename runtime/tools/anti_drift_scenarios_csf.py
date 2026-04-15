from __future__ import annotations

from pathlib import Path

from runtime.tools.anti_drift import CanonicalDecisionSnapshot, canonical_snapshot_from_session_context
from runtime.tools.research_session import run_research_session
from runtime.tools.anti_drift_scenarios_support import (
    review_closure_path,
    prepare_csf_backtest_ready_review_complete,
    prepare_csf_data_ready_review_complete,
    prepare_csf_mandate_review_complete,
    prepare_csf_signal_ready_review_complete,
    prepare_csf_test_evidence_review_complete,
    prepare_csf_train_freeze_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
    write_yaml,
)


def snapshot_csf_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_case"
    prepare_csf_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_data_ready_confirmation",),
    )


def snapshot_csf_signal_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_signal_case"
    prepare_csf_data_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-signal-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_signal_ready_confirmation",),
    )


def snapshot_csf_train_freeze_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_train_case"
    prepare_csf_signal_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-train-freeze-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_train_freeze_confirmation",),
    )


def snapshot_csf_test_evidence_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_test_case"
    prepare_csf_train_freeze_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-test-evidence-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_test_evidence_confirmation",),
    )


def snapshot_csf_backtest_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_backtest_case"
    prepare_csf_test_evidence_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-backtest-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_backtest_ready_confirmation",),
    )


def snapshot_csf_holdout_validation_review_complete(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_holdout_complete_case"
    prepare_csf_backtest_ready_review_complete(outputs_root / lineage_id)
    stage_dir = outputs_root / lineage_id / "07_csf_holdout_validation"
    write_minimal_stage_outputs(stage_dir, stage="csf_holdout_validation")
    write_yaml(review_closure_path(stage_dir, "latest_review_pack.yaml"), {"status": "ok"})
    write_yaml(review_closure_path(stage_dir, "stage_gate_review.yaml"), {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-holdout-validation-review-complete",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_holdout_validation_review_complete",),
    )
