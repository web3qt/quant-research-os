from pathlib import Path

import pyarrow.parquet as pq
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.tss_backtest_runtime import (
    build_tss_backtest_ready_from_test_evidence,
    scaffold_tss_backtest_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_tss_test_evidence_stage(lineage_root: Path) -> None:
    formal_dir = lineage_root / "05_tss_test_evidence" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "event_forward_return.parquet",
        "signal_performance_summary.json",
        "tss_test_gate_table.csv",
        "tss_selected_variants_test.csv",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    (formal_dir / "tss_selected_variants_test.csv").write_text(
        "variant_id,status\nbaseline_v1,selected\n",
        encoding="utf-8",
    )


def _tss_backtest_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "strategy_contract": {
                "confirmed": confirmed,
                "draft": {
                    "strategy_id": "baseline_strategy",
                    "variant_id": "baseline_v1",
                    "entry_rule": "Enter when signal event fires.",
                    "exit_rule": "Exit after horizon closes.",
                    "net_after_cost_rule": "Require positive net return after fees and slippage.",
                },
                "missing_items": [],
            },
            "execution_contract": {
                "confirmed": confirmed,
                "draft": {
                    "execution_lag": "1 bar",
                    "cost_model": "fixed fee plus slippage",
                    "position_sizing_rule": "unit notional fixture",
                },
                "missing_items": [],
            },
            "risk_contract": {
                "confirmed": confirmed,
                "draft": {
                    "max_position_rule": "single asset one unit",
                    "stop_rule": "none in fixture",
                    "drawdown_rule": "report drawdown",
                },
                "missing_items": [],
            },
            "diagnostic_contract": {
                "confirmed": confirmed,
                "draft": {
                    "required_diagnostics": ["engine_compare", "position_timeseries"],
                    "after_cost_rule": "Gate uses net after cost.",
                    "trade_count_rule": "At least one fixture trade.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["strategy_contract.yaml", "position_timeseries.parquet"],
                    "consumer_stage": "tss_holdout_validation",
                    "frozen_config_note": "Holdout consumes this frozen strategy.",
                },
                "missing_items": [],
            },
        }
    }


def test_scaffold_tss_backtest_ready_creates_draft_under_tss_stage_dir(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"

    stage_dir = scaffold_tss_backtest_ready(lineage_root)

    assert stage_dir == lineage_root / "06_tss_backtest_ready"
    draft_path = stage_dir / "author" / "draft" / "tss_backtest_ready_freeze_draft.yaml"
    assert draft_path.exists()
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
    assert set(payload["groups"]) == {
        "strategy_contract",
        "execution_contract",
        "risk_contract",
        "diagnostic_contract",
        "delivery_contract",
    }


def test_build_tss_backtest_ready_writes_planned_formal_artifacts(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_test_evidence_stage(lineage_root)
    stage_dir = lineage_root / "06_tss_backtest_ready"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_backtest_ready_freeze_draft.yaml",
        _tss_backtest_ready_draft(confirmed=True),
    )

    built_dir = build_tss_backtest_ready_from_test_evidence(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "strategy_contract.yaml").exists()
    assert (formal_dir / "engine_compare.csv").exists()
    assert (formal_dir / "position_timeseries.parquet").exists()
    assert (formal_dir / "trade_ledger.csv").exists()
    assert (formal_dir / "tss_backtest_gate_table.csv").exists()
    assert pq.read_table(formal_dir / "position_timeseries.parquet").num_rows > 0
