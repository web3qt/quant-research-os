from __future__ import annotations

from pathlib import Path

from tools.anti_drift import CanonicalDecisionSnapshot, canonical_snapshot_from_session_context
from tools.research_session import run_research_session
from tools.anti_drift_scenarios_support import (
    prepare_mainline_backtest_ready_review_complete,
    prepare_mainline_data_ready_review_complete,
    prepare_mainline_mandate_review_complete,
    prepare_mainline_signal_ready_review_complete,
    prepare_mainline_test_evidence_review_complete,
    prepare_mainline_train_freeze_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
    write_yaml,
)


def snapshot_idea_intake_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::idea_intake_confirmation",),
    )


def snapshot_mandate_review(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="mandate-review-replay",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::mandate_review",),
    )


def snapshot_data_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "mainline_case"
    prepare_mainline_mandate_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::data_ready_confirmation",),
    )


def snapshot_signal_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "signal_ready_case"
    prepare_mainline_data_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::signal_ready_confirmation",),
    )


def snapshot_train_freeze_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "train_freeze_case"
    prepare_mainline_signal_ready_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::train_freeze_confirmation",),
    )


def snapshot_test_evidence_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "test_evidence_case"
    prepare_mainline_train_freeze_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::test_evidence_confirmation",),
    )


def snapshot_backtest_ready_confirmation(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "backtest_ready_case"
    prepare_mainline_test_evidence_review_complete(outputs_root / lineage_id)
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::backtest_ready_confirmation",),
    )


def snapshot_holdout_validation_review_complete(outputs_root: Path) -> CanonicalDecisionSnapshot:
    lineage_id = "holdout_complete_case"
    prepare_mainline_backtest_ready_review_complete(outputs_root / lineage_id)
    stage_dir = outputs_root / lineage_id / "07_holdout"
    write_minimal_stage_outputs(stage_dir, stage="holdout_validation")
    write_yaml(stage_dir / "latest_review_pack.yaml", {"status": "ok"})
    write_yaml(stage_dir / "stage_gate_review.yaml", {"status": "ok"})
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    return canonical_snapshot_from_session_context(
        status,
        fixture_id="holdout-validation-review-complete",
        evidence_refs=("tools/anti_drift_scenarios_mainline.py::holdout_validation_review_complete",),
    )
