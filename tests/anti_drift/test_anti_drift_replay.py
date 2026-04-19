import json
from pathlib import Path

from tests.helpers.repo_paths import TESTS_ROOT
from runtime.tools.anti_drift import canonical_snapshot_from_session_context, diff_snapshot
from runtime.tools.anti_drift_scenarios import (
    prepare_csf_backtest_ready_review_complete,
    prepare_csf_mandate_review_complete,
    prepare_csf_data_ready_review_complete,
    prepare_csf_signal_ready_review_complete,
    prepare_csf_test_evidence_review_complete,
    prepare_csf_train_freeze_review_complete,
    prepare_mainline_backtest_ready_review_complete,
    prepare_mainline_signal_ready_review_complete,
    prepare_mainline_mandate_review_complete,
    prepare_mainline_data_ready_review_complete,
    prepare_mainline_test_evidence_review_complete,
    prepare_mainline_train_freeze_review_complete,
    write_minimal_stage_outputs,
    write_stage_completion_certificate,
)
from runtime.tools.anti_drift_scenarios_support import review_closure_path
from runtime.tools.research_session import run_research_session


FIXTURE_DIR = TESTS_ROOT / "fixtures" / "anti_drift"
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
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::mandate_review",),
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
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::test_evidence_retry",),
    )

    assert diff_snapshot(_load_golden("test_evidence_retry_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_train_freeze_pass_for_retry_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "train_retry_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="train_freeze")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-pass-for-retry",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::train_freeze_pass_for_retry",),
    )

    assert diff_snapshot(_load_golden("train_freeze_pass_for_retry_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_backtest_ready_no_go_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "backtest_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_backtest"
    write_minimal_stage_outputs(stage_dir, stage="backtest_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-no-go",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::backtest_ready_no_go",),
    )

    assert diff_snapshot(_load_golden("backtest_ready_no_go_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_data_ready_child_lineage_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "data_ready_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="data_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="data-ready-child-lineage",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::data_ready_child_lineage",),
    )

    assert diff_snapshot(_load_golden("data_ready_child_lineage_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_signal_ready_child_lineage_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "signal_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_data_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "03_signal_ready"
    write_minimal_stage_outputs(stage_dir, stage="signal_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="signal-ready-child-lineage",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::signal_ready_child_lineage",),
    )

    assert diff_snapshot(_load_golden("signal_ready_child_lineage_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_train_freeze_pass_for_retry_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_train_retry_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_signal_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "04_csf_train_freeze"
    write_minimal_stage_outputs(stage_dir, stage="csf_train_freeze")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS FOR RETRY")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-train-freeze-pass-for-retry",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::csf_train_freeze_pass_for_retry",),
    )

    assert diff_snapshot(_load_golden("csf_train_freeze_pass_for_retry_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_backtest_ready_no_go_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_backtest_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_test_evidence_review_complete(lineage_root)
    stage_dir = lineage_root / "06_csf_backtest_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_backtest_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-backtest-ready-no-go",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::csf_backtest_ready_no_go",),
    )

    assert diff_snapshot(_load_golden("csf_backtest_ready_no_go_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_data_ready_child_lineage_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_data_child_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_mandate_review_complete(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="CHILD LINEAGE")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-child-lineage",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::csf_data_ready_child_lineage",),
    )

    assert diff_snapshot(_load_golden("csf_data_ready_child_lineage_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_holdout_validation_no_go_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "holdout_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_holdout"
    write_minimal_stage_outputs(stage_dir, stage="holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="holdout-validation-no-go",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::holdout_validation_no_go",),
    )

    assert diff_snapshot(_load_golden("holdout_validation_no_go_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_holdout_validation_no_go_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_holdout_no_go_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_csf_holdout_validation"
    write_minimal_stage_outputs(stage_dir, stage="csf_holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="NO-GO")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-holdout-validation-no-go",
        evidence_refs=("runtime/tools/anti_drift_scenarios_failure.py::csf_holdout_validation_no_go",),
    )

    assert diff_snapshot(_load_golden("csf_holdout_validation_no_go_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_mandate_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-data-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_data_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_data_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_signal_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_signal_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_data_ready_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-signal-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_signal_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_signal_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_train_freeze_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_train_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_signal_ready_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-train-freeze-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_train_freeze_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_train_freeze_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_test_evidence_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_test_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_train_freeze_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-test-evidence-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_test_evidence_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_test_evidence_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_backtest_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_backtest_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_test_evidence_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-backtest-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_backtest_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("csf_backtest_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_csf_holdout_review_complete_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "csf_holdout_complete_case"
    lineage_root = outputs_root / lineage_id
    prepare_csf_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_csf_holdout_validation"
    write_minimal_stage_outputs(stage_dir, stage="csf_holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    review_closure_path(stage_dir, "latest_review_pack.yaml").parent.mkdir(parents=True, exist_ok=True)
    review_closure_path(stage_dir, "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    review_closure_path(stage_dir, "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="csf-holdout-validation-review-complete",
        evidence_refs=("runtime/tools/anti_drift_scenarios_csf.py::csf_holdout_validation_review_complete",),
    )

    assert diff_snapshot(_load_golden("csf_holdout_validation_review_complete_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_idea_intake_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    status = run_research_session(
        outputs_root=outputs_root,
        raw_idea="BTC leads high-liquidity alts after shock events",
    )
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="idea-intake-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::idea_intake_confirmation",),
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
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::data_ready_confirmation",),
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
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::signal_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("signal_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_train_freeze_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "train_freeze_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_signal_ready_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="train-freeze-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::train_freeze_confirmation",),
    )

    assert diff_snapshot(_load_golden("train_freeze_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_test_evidence_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "test_evidence_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_train_freeze_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="test-evidence-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::test_evidence_confirmation",),
    )

    assert diff_snapshot(_load_golden("test_evidence_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_backtest_ready_confirmation_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "backtest_ready_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_test_evidence_review_complete(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="backtest-ready-confirmation",
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::backtest_ready_confirmation",),
    )

    assert diff_snapshot(_load_golden("backtest_ready_confirmation_snapshot.json"), snapshot) == {}


def test_run_research_session_snapshot_matches_holdout_review_complete_golden(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_id = "holdout_complete_case"
    lineage_root = outputs_root / lineage_id
    prepare_mainline_backtest_ready_review_complete(lineage_root)
    stage_dir = lineage_root / "07_holdout"
    write_minimal_stage_outputs(stage_dir, stage="holdout_validation")
    write_stage_completion_certificate(stage_dir / "stage_completion_certificate.yaml", stage_status="PASS")
    review_closure_path(stage_dir, "latest_review_pack.yaml").parent.mkdir(parents=True, exist_ok=True)
    review_closure_path(stage_dir, "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    review_closure_path(stage_dir, "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_id)
    snapshot = canonical_snapshot_from_session_context(
        status,
        fixture_id="holdout-validation-review-complete",
        evidence_refs=("runtime/tools/anti_drift_scenarios_mainline.py::holdout_validation_review_complete",),
    )

    assert diff_snapshot(_load_golden("holdout_validation_review_complete_snapshot.json"), snapshot) == {}
