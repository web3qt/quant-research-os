import json
from pathlib import Path

from tools.anti_drift import canonical_snapshot_from_session_context, diff_snapshot
from tools.anti_drift_scenarios import (
    prepare_csf_mandate_review_complete,
    prepare_mainline_mandate_review_complete,
    prepare_mainline_data_ready_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
)
from tools.research_session import run_research_session


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "anti_drift"
def _load_golden(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_run_research_session_snapshot_matches_mandate_review_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "01_mandate"
    write_minimal_stage_outputs(stage_dir, stage="mandate")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="mandate-review-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::mandate_review",),
    )

    assert diff_snapshot(_load_golden("mandate_review_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_failure_handler_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "btc_leads_alts"
    stage_dir = outputs_root / lineage_id / "05_test_evidence"
    write_minimal_stage_outputs(stage_dir, stage="test_evidence")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-retry-replay",
        evidence_refs=("tools/anti_drift_scenarios.py::test_evidence_retry",),
    )

    assert diff_snapshot(_load_golden("test_evidence_retry_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::csf_data_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_data_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_idea_intake_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::idea_intake_confirmation",),
    )

    assert diff_snapshot(_load_golden("idea_intake_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_mainline_data_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "mainline_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::data_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("data_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_signal_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "signal_ready_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_data_ready_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-confirmation",
        evidence_refs=("tools/anti_drift_scenarios.py::signal_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("signal_ready_confirmation_snapshot.json"), snapshot) == {}
