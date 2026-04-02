from __future__ import annotations

from pathlib import Path

from tools.anti_drift import CanonicalDecisionSnapshot, canonical_snapshot_from_session_context
from tools.research_session import run_research_session
from tools.anti_drift_scenarios_support import (
    prepare_csf_backtest_ready_review_complete,
    prepare_csf_mandate_review_complete,
    prepare_csf_signal_ready_review_complete,
    prepare_csf_test_evidence_review_complete,
    prepare_mainline_backtest_ready_review_complete,
    prepare_mainline_data_ready_review_complete,
    prepare_mainline_mandate_review_complete,
    prepare_mainline_signal_ready_review_complete,
    prepare_mainline_test_evidence_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
)


def snapshot_test_evidence_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry-replay",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::test_evidence_retry",),
    )


def snapshot_train_freeze_pass_for_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "train_retry_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="train_freeze")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-pass-for-retry",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::train_freeze_pass_for_retry",),
    )


def snapshot_backtest_ready_no_go(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "backtest_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_backtest"
    write_minimal_stage_outputs(stage_dir, stage="backtest_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-no-go",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::backtest_ready_no_go",),
    )


def snapshot_data_ready_child_lineage(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "data_ready_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-child-lineage",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::data_ready_child_lineage",),
    )


def snapshot_signal_ready_child_lineage(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "signal_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="signal_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-child-lineage",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::signal_ready_child_lineage",),
    )


def snapshot_holdout_validation_no_go(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "holdout_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_holdout"
    write_minimal_stage_outputs(stage_dir, stage="holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="holdout-validation-no-go",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::holdout_validation_no_go",),
    )


def snapshot_csf_train_freeze_pass_for_retry(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_train_retry_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_csf_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="csf_train_freeze")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-train-freeze-pass-for-retry",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::csf_train_freeze_pass_for_retry",),
    )


def snapshot_csf_backtest_ready_no_go(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_backtest_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_backtest_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-backtest-ready-no-go",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::csf_backtest_ready_no_go",),
    )


def snapshot_csf_data_ready_child_lineage(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_data_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-child-lineage",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::csf_data_ready_child_lineage",),
    )


def snapshot_csf_holdout_validation_no_go(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "csf_holdout_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_csf_holdout_validation"
    write_minimal_stage_outputs(stage_dir, stage="csf_holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-holdout-validation-no-go",
        evidence_refs=("tools/anti_drift_scenarios_failure.py::csf_holdout_validation_no_go",),
    )
