from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from tools.anti_drift import CanonicalDecisionSnapshot
from tools.anti_drift_scenarios_csf import (
    snapshot_csf_backtest_ready_confirmation,
    snapshot_csf_data_ready_confirmation,
    snapshot_csf_holdout_validation_review_complete,
    snapshot_csf_signal_ready_confirmation,
    snapshot_csf_test_evidence_confirmation,
    snapshot_csf_train_freeze_confirmation,
)
from tools.anti_drift_scenarios_failure import (
    snapshot_backtest_ready_no_go,
    snapshot_csf_backtest_ready_no_go,
    snapshot_csf_data_ready_child_lineage,
    snapshot_csf_holdout_validation_no_go,
    snapshot_csf_train_freeze_pass_for_retry,
    snapshot_data_ready_child_lineage,
    snapshot_holdout_validation_no_go,
    snapshot_signal_ready_child_lineage,
    snapshot_test_evidence_retry,
    snapshot_train_freeze_pass_for_retry,
)
from tools.anti_drift_scenarios_mainline import (
    snapshot_backtest_ready_confirmation,
    snapshot_data_ready_confirmation,
    snapshot_holdout_validation_review_complete,
    snapshot_idea_intake_confirmation,
    snapshot_mandate_review,
    snapshot_signal_ready_confirmation,
    snapshot_test_evidence_confirmation,
    snapshot_train_freeze_confirmation,
)
from tools.anti_drift_scenarios_support import (
    prepare_csf_backtest_ready_review_complete,
    prepare_csf_mandate_review_complete,
    prepare_csf_data_ready_review_complete,
    prepare_csf_signal_ready_review_complete,
    prepare_csf_test_evidence_review_complete,
    prepare_csf_train_freeze_review_complete,
    prepare_mainline_backtest_ready_review_complete,
    prepare_mainline_data_ready_review_complete,
    prepare_mainline_mandate_review_complete,
    prepare_mainline_signal_ready_review_complete,
    prepare_mainline_test_evidence_review_complete,
    prepare_mainline_train_freeze_review_complete,
    write_minimal_stage_outputs,
    write_placeholder_draft,
    write_stage_completion_certificate,
    write_yaml,
)


SCENARIOS: dict[str, Callable[[Path], CanonicalDecisionSnapshot]] = {
    "idea_intake_confirmation_snapshot.json": snapshot_idea_intake_confirmation,
    "mandate_review_snapshot.json": snapshot_mandate_review,
    "test_evidence_retry_snapshot.json": snapshot_test_evidence_retry,
    "train_freeze_pass_for_retry_snapshot.json": snapshot_train_freeze_pass_for_retry,
    "backtest_ready_no_go_snapshot.json": snapshot_backtest_ready_no_go,
    "data_ready_child_lineage_snapshot.json": snapshot_data_ready_child_lineage,
    "signal_ready_child_lineage_snapshot.json": snapshot_signal_ready_child_lineage,
    "holdout_validation_no_go_snapshot.json": snapshot_holdout_validation_no_go,
    "csf_train_freeze_pass_for_retry_snapshot.json": snapshot_csf_train_freeze_pass_for_retry,
    "csf_backtest_ready_no_go_snapshot.json": snapshot_csf_backtest_ready_no_go,
    "csf_data_ready_child_lineage_snapshot.json": snapshot_csf_data_ready_child_lineage,
    "csf_holdout_validation_no_go_snapshot.json": snapshot_csf_holdout_validation_no_go,
    "csf_data_ready_confirmation_snapshot.json": snapshot_csf_data_ready_confirmation,
    "csf_signal_ready_confirmation_snapshot.json": snapshot_csf_signal_ready_confirmation,
    "csf_train_freeze_confirmation_snapshot.json": snapshot_csf_train_freeze_confirmation,
    "csf_test_evidence_confirmation_snapshot.json": snapshot_csf_test_evidence_confirmation,
    "csf_backtest_ready_confirmation_snapshot.json": snapshot_csf_backtest_ready_confirmation,
    "csf_holdout_validation_review_complete_snapshot.json": snapshot_csf_holdout_validation_review_complete,
    "data_ready_confirmation_snapshot.json": snapshot_data_ready_confirmation,
    "signal_ready_confirmation_snapshot.json": snapshot_signal_ready_confirmation,
    "train_freeze_confirmation_snapshot.json": snapshot_train_freeze_confirmation,
    "test_evidence_confirmation_snapshot.json": snapshot_test_evidence_confirmation,
    "backtest_ready_confirmation_snapshot.json": snapshot_backtest_ready_confirmation,
    "holdout_validation_review_complete_snapshot.json": snapshot_holdout_validation_review_complete,
}


def export_default_snapshots(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with TemporaryDirectory() as tmp:
        outputs_root = Path(tmp) / "outputs"
        for file_name, builder in SCENARIOS.items():
            snapshot = builder(outputs_root)
            target = output_dir / file_name
            target.write_text(
                json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written.append(target)
    return written
