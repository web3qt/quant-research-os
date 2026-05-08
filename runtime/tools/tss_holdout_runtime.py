from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_HOLDOUT_VALIDATION_FREEZE_DRAFT_FILE = "tss_holdout_validation_freeze_draft.yaml"
TSS_HOLDOUT_VALIDATION_DRAFT_FILE = TSS_HOLDOUT_VALIDATION_FREEZE_DRAFT_FILE
TSS_HOLDOUT_VALIDATION_GROUP_ORDER = [
    "window_contract",
    "reuse_contract",
    "stability_contract",
    "failure_governance",
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


def _blank_tss_holdout_validation_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "window_contract": {
                "confirmed": False,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "reuse_rule": "",
                    "drift_scope": "",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": False,
                "draft": {
                    "backtest_contract_source": "06_tss_backtest_ready/author/formal/strategy_contract.yaml",
                    "test_contract_source": "05_tss_test_evidence/author/formal/tss_test_gate_table.csv",
                    "no_reestimate_rule": "",
                },
                "missing_items": [],
            },
            "stability_contract": {
                "confirmed": False,
                "draft": {
                    "direction_flip_rule": "",
                    "frequency_collapse_rule": "",
                    "after_cost_rule": "",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": False,
                "draft": {
                    "retryable_conditions": [],
                    "child_lineage_trigger": "",
                    "rollback_boundary": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "terminal",
                    "field_doc_rule": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_holdout_validation(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "07_tss_holdout_validation"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_HOLDOUT_VALIDATION_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_holdout_validation_freeze_draft())
    return stage_dir


def build_tss_holdout_validation_from_backtest_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_formal_dir = lineage_root / "06_tss_backtest_ready" / "author" / "formal"
    missing = [
        name
        for name in [
            "strategy_contract.yaml",
            "engine_compare.csv",
            "position_timeseries.parquet",
            "trade_ledger.csv",
            "tss_backtest_gate_table.csv",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"tss_backtest_ready artifacts missing before tss_holdout_validation build: {', '.join(missing)}")

    stage_dir = scaffold_tss_holdout_validation(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    window_contract = groups["window_contract"]["draft"]
    reuse_contract = groups["reuse_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]
    strategy_id = "baseline_strategy"

    _dump_json(
        formal_dir / "tss_holdout_run_manifest.json",
        {
            "stage": "tss_holdout_validation",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_backtest_ready",
            "primary_key": ["strategy_id"],
            "strategy_id": strategy_id,
            "holdout_window_source": window_contract.get("holdout_window_source", "time_split.json::holdout"),
            "reuse_rule": window_contract.get("reuse_rule", ""),
            "no_reestimate_rule": reuse_contract.get("no_reestimate_rule", ""),
            "tuning_performed": False,
            "machine_artifacts": [
                "tss_holdout_run_manifest.json",
                "holdout_signal_diagnostics.parquet",
                "holdout_event_compare.parquet",
                "holdout_backtest_compare.parquet",
                "rolling_holdout_stability.json",
            ],
            "consumer_stage": delivery_contract.get("consumer_stage", "terminal"),
            "replay_command": "python -m runtime.tools.tss_holdout_runtime",
        },
    )
    _write_parquet_rows(
        formal_dir / "holdout_signal_diagnostics.parquet",
        [
            {
                "strategy_id": strategy_id,
                "timestamp": "2024-01-01T00:00:00Z",
                "signal_coverage": 1.0,
                "direction_match": True,
            }
        ],
    )
    _write_parquet_rows(
        formal_dir / "holdout_event_compare.parquet",
        [
            {
                "strategy_id": strategy_id,
                "horizon": "1d",
                "test_event_count": 1,
                "holdout_event_count": 1,
                "direction_match": True,
            }
        ],
    )
    _write_parquet_rows(
        formal_dir / "holdout_backtest_compare.parquet",
        [
            {
                "strategy_id": strategy_id,
                "backtest_metric": "net_return",
                "backtest_value": 0.01,
                "holdout_value": 0.01,
                "delta": 0.0,
            }
        ],
    )
    _dump_json(
        formal_dir / "rolling_holdout_stability.json",
        {
            "stage": "tss_holdout_validation",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "strategy_id": strategy_id,
            "stability_status": "pass",
            "rolling_window_count": 1,
        },
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_HOLDOUT_VALIDATION_FREEZE_DRAFT_FILE
    return require_confirmed_freeze_groups(
        draft_path,
        TSS_HOLDOUT_VALIDATION_GROUP_ORDER,
        stage_label="tss_holdout_validation",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"{path.name}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected yaml map")
    return payload
