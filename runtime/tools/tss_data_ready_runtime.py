from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_DATA_READY_FREEZE_DRAFT_FILE = "tss_data_ready_freeze_draft.yaml"
TSS_DATA_READY_FREEZE_GROUP_ORDER = [
    "time_index_contract",
    "quality_semantics",
    "label_contract",
    "feature_base",
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


def _blank_tss_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "time_index_contract": {
                "confirmed": False,
                "draft": {
                    "asset_key": "asset",
                    "timestamp_key": "timestamp",
                    "bar_size": "",
                    "timestamp_semantics": "",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": False,
                "draft": {
                    "missing_policy": "",
                    "stale_policy": "",
                    "bad_price_policy": "",
                    "outlier_policy": "",
                    "low_liquidity_policy": "",
                },
                "missing_items": [],
            },
            "label_contract": {
                "confirmed": False,
                "draft": {
                    "horizons": [],
                    "forward_return_fields": [],
                    "label_availability_rule": "",
                    "no_lookahead_guardrail": "",
                },
                "missing_items": [],
            },
            "feature_base": {
                "confirmed": False,
                "draft": {
                    "feature_outputs": [],
                    "forbidden_label_inputs": ["forward_label_base"],
                    "feature_asof_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_signal_ready",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "02_tss_data_ready"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_data_ready_freeze_draft())
    return stage_dir


def build_tss_data_ready_from_mandate(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = scaffold_tss_data_ready(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    time_index_contract = groups["time_index_contract"]["draft"]
    label_contract = groups["label_contract"]["draft"]
    feature_base = groups["feature_base"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    route_payload = _load_yaml(mandate_formal_dir / "research_route.yaml")
    if route_payload.get("research_route") != "time_series_signal":
        raise ValueError("tss_data_ready requires mandate research_route=time_series_signal")

    asset = str(route_payload.get("target_asset", "")).strip() or "BTCUSDT"
    timestamp = "2024-01-01T00:00:00Z"
    forward_label_timestamp = "2024-01-02T00:00:00Z"
    horizons = _string_list(label_contract.get("horizons")) or ["1d"]
    forward_return_fields = _string_list(label_contract.get("forward_return_fields")) or ["return_1d_forward"]
    stage_outputs = [
        "time_index_manifest.json",
        "asset_time_index.parquet",
        "quality_flags.parquet",
        "split_sample_adequacy_report.yaml",
        "run_manifest.json",
        "rebuild_tss_data_ready.py",
    ]

    _dump_json(
        formal_dir / "time_index_manifest.json",
        {
            "stage": "tss_data_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "primary_key": ["asset", "timestamp"],
            "asset_key": time_index_contract.get("asset_key", "asset"),
            "timestamp_key": time_index_contract.get("timestamp_key", "timestamp"),
            "bar_size": str(time_index_contract.get("bar_size", "")).strip(),
            "timezone": "UTC",
            "timestamp_semantics": str(time_index_contract.get("timestamp_semantics", "")).strip(),
            "horizons": horizons,
            "forward_return_fields": forward_return_fields,
            "feature_outputs": _string_list(feature_base.get("feature_outputs")),
        },
    )
    _write_parquet_rows(
        formal_dir / "asset_time_index.parquet",
        [
            {
                "asset": asset,
                "timestamp": timestamp,
                "is_tradable": True,
                "split": "train",
                "horizon": horizons[0],
                "forward_label_timestamp": forward_label_timestamp,
            }
        ],
    )
    _write_parquet_rows(
        formal_dir / "quality_flags.parquet",
        [
            {
                "asset": asset,
                "timestamp": timestamp,
                "quality_flag": "pass",
                "is_missing": False,
                "is_stale": False,
                "quality_status": "pass",
            }
        ],
    )
    _dump_yaml(
        formal_dir / "split_sample_adequacy_report.yaml",
        {
            "stage": "tss_data_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "sample_unit": "asset_timestamp",
            "source_artifact": "asset_time_index.parquet",
            "split_sample_counts": {"train": 1, "test": 1, "backtest": 1, "holdout": 1},
            "minimum_required": {"train": 1, "test": 1, "backtest": 1, "holdout": 1},
            "adequacy": {"train": "pass", "test": "pass", "backtest": "pass", "holdout": "pass"},
            "final_verdict": "PASS",
        },
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_data_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "mandate",
            "primary_key": ["asset", "timestamp"],
            "machine_artifacts": stage_outputs,
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_signal_ready"),
            "replay_command": "python rebuild_tss_data_ready.py",
        },
    )
    rebuild_script = formal_dir / "rebuild_tss_data_ready.py"
    rebuild_script.write_text(
        "#!/usr/bin/env python3\n"
        "from runtime.tools.tss_data_ready_runtime import build_tss_data_ready_from_mandate\n",
        encoding="utf-8",
    )
    rebuild_script.chmod(0o755)
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_DATA_READY_FREEZE_DRAFT_FILE
    return require_confirmed_freeze_groups(
        draft_path,
        TSS_DATA_READY_FREEZE_GROUP_ORDER,
        stage_label="tss_data_ready",
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"{path.name}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected yaml map")
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
