from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.tss_holdout_runtime import (
    build_tss_holdout_validation_from_backtest_ready,
    scaffold_tss_holdout_validation,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_backtest_ready_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "06_tss_backtest_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "strategy_contract.yaml",
        "engine_compare.csv",
        "position_timeseries.parquet",
        "trade_ledger.csv",
        "tss_backtest_gate_table.csv",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")


def _tss_holdout_validation_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "window_contract": {
                "confirmed": confirmed,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "reuse_rule": "Holdout reuses frozen backtest strategy only.",
                    "drift_scope": "Compare signal and backtest behavior to test/backtest windows.",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": confirmed,
                "draft": {
                    "backtest_contract_source": "06_tss_backtest_ready/author/formal/strategy_contract.yaml",
                    "test_contract_source": "05_tss_test_evidence/author/formal/tss_test_gate_table.csv",
                    "no_reestimate_rule": "No threshold tuning in holdout.",
                },
                "missing_items": [],
            },
            "stability_contract": {
                "confirmed": confirmed,
                "draft": {
                    "direction_flip_rule": "Escalate direction flips.",
                    "frequency_collapse_rule": "Escalate event frequency collapse.",
                    "after_cost_rule": "Holdout must remain net positive after costs.",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": confirmed,
                "draft": {
                    "retryable_conditions": ["artifact defect"],
                    "child_lineage_trigger": "Open child lineage for new mechanism.",
                    "rollback_boundary": "No in-place tuning.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["tss_holdout_run_manifest.json"],
                    "consumer_stage": "terminal",
                    "field_doc_rule": "Every machine artifact needs field documentation.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_holdout_validation_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_holdout_validation(lineage_root)

    assert stage_dir == lineage_root / "07_tss_holdout_validation"
    draft_path = stage_dir / "author" / "draft" / "tss_holdout_validation_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "window_contract",
        "reuse_contract",
        "stability_contract",
        "failure_governance",
        "delivery_contract",
    }


def test_build_tss_holdout_validation_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_backtest_ready_stage(lineage_root)
    stage_dir = lineage_root / "07_tss_holdout_validation"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_holdout_validation_freeze_draft.yaml",
        _tss_holdout_validation_draft(confirmed=True),
    )

    built_dir = build_tss_holdout_validation_from_backtest_ready(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "tss_holdout_run_manifest.json").exists()
    assert (formal_dir / "holdout_signal_diagnostics.parquet").exists()
    assert (formal_dir / "holdout_event_compare.parquet").exists()
    assert (formal_dir / "holdout_backtest_compare.parquet").exists()
    assert pq.read_table(formal_dir / "holdout_signal_diagnostics.parquet").num_rows > 0
