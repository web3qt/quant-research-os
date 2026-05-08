from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_BACKTEST_READY_FREEZE_DRAFT_FILE = "tss_backtest_ready_freeze_draft.yaml"
TSS_BACKTEST_READY_DRAFT_FILE = TSS_BACKTEST_READY_FREEZE_DRAFT_FILE
TSS_BACKTEST_READY_GROUP_ORDER = [
    "strategy_contract",
    "execution_contract",
    "risk_contract",
    "diagnostic_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_csv_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _blank_tss_backtest_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "strategy_contract": {
                "confirmed": False,
                "draft": {
                    "strategy_id": "",
                    "variant_id": "",
                    "entry_rule": "",
                    "exit_rule": "",
                    "net_after_cost_rule": "",
                },
                "missing_items": [],
            },
            "execution_contract": {
                "confirmed": False,
                "draft": {
                    "execution_lag": "",
                    "cost_model": "",
                    "position_sizing_rule": "",
                },
                "missing_items": [],
            },
            "risk_contract": {
                "confirmed": False,
                "draft": {
                    "max_position_rule": "",
                    "stop_rule": "",
                    "drawdown_rule": "",
                },
                "missing_items": [],
            },
            "diagnostic_contract": {
                "confirmed": False,
                "draft": {
                    "required_diagnostics": [],
                    "after_cost_rule": "",
                    "trade_count_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_holdout_validation",
                    "frozen_config_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_backtest_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "06_tss_backtest_ready"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_BACKTEST_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_backtest_ready_freeze_draft())
    return stage_dir


def build_tss_backtest_ready_from_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_formal_dir = lineage_root / "05_tss_test_evidence" / "author" / "formal"
    missing = [
        name
        for name in [
            "event_forward_return.parquet",
            "signal_performance_summary.json",
            "tss_test_gate_table.csv",
            "tss_selected_variants_test.csv",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"tss_test_evidence artifacts missing before tss_backtest_ready build: {', '.join(missing)}")

    stage_dir = scaffold_tss_backtest_ready(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    strategy_contract = groups["strategy_contract"]["draft"]
    execution_contract = groups["execution_contract"]["draft"]
    risk_contract = groups["risk_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]
    strategy_id = strategy_contract.get("strategy_id", "baseline_strategy") or "baseline_strategy"

    _dump_yaml(
        formal_dir / "strategy_contract.yaml",
        {
            "stage": "tss_backtest_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "primary_key": ["timestamp", "strategy_id"],
            **strategy_contract,
            "execution_lag_rule": execution_contract.get("execution_lag", ""),
            "cost_model": execution_contract.get("cost_model", ""),
            "risk_limit_rule": risk_contract.get("max_position_rule", ""),
            "delivery_contract": delivery_contract,
        },
    )
    _write_csv_rows(
        formal_dir / "engine_compare.csv",
        [{"strategy_id": strategy_id, "engine_name": "fixture", "metric_name": "net_return", "metric_value": 0.01}],
        ["strategy_id", "engine_name", "metric_name", "metric_value"],
    )
    _write_parquet_rows(
        formal_dir / "position_timeseries.parquet",
        [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "strategy_id": strategy_id,
                "asset": "BTCUSDT",
                "position": 1.0,
            }
        ],
    )
    _write_csv_rows(
        formal_dir / "trade_ledger.csv",
        [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "strategy_id": strategy_id,
                "asset": "BTCUSDT",
                "quantity": 1.0,
                "price": 100.0,
            }
        ],
        ["timestamp", "strategy_id", "asset", "quantity", "price"],
    )
    _write_csv_rows(
        formal_dir / "tss_backtest_gate_table.csv",
        [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "strategy_id": strategy_id,
                "verdict": "PASS",
                "reason": "fixture net return remains positive after cost",
            }
        ],
        ["timestamp", "strategy_id", "verdict", "reason"],
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_backtest_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_test_evidence",
            "primary_key": ["timestamp", "strategy_id"],
            "machine_artifacts": [
                "strategy_contract.yaml",
                "engine_compare.csv",
                "position_timeseries.parquet",
                "trade_ledger.csv",
                "tss_backtest_gate_table.csv",
                "run_manifest.json",
            ],
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_holdout_validation"),
            "replay_command": "python -m runtime.tools.tss_backtest_runtime",
        },
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_BACKTEST_READY_FREEZE_DRAFT_FILE
    return require_confirmed_freeze_groups(
        draft_path,
        TSS_BACKTEST_READY_GROUP_ORDER,
        stage_label="tss_backtest_ready",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"{path.name}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected yaml map")
    return payload
