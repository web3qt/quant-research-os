from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout
from runtime.tools.tss_signal_ready_contract_runtime import validate_tss_signal_ready_semantics


TSS_SIGNAL_READY_FREEZE_DRAFT_FILE = "tss_signal_ready_freeze_draft.yaml"
TSS_SIGNAL_READY_FREEZE_GROUP_ORDER = [
    "signal_identity",
    "input_contract",
    "signal_expression",
    "event_contract",
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


def _blank_tss_signal_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "signal_identity": {
                "confirmed": False,
                "draft": {
                    "signal_id": "",
                    "signal_version": "",
                    "signal_direction": "",
                    "target_asset": "",
                },
                "missing_items": [],
            },
            "input_contract": {
                "confirmed": False,
                "draft": {
                    "input_field_map": [],
                    "input_roots": [],
                    "forbidden_input_roots": ["forward_label_base"],
                },
                "missing_items": [],
            },
            "signal_expression": {
                "confirmed": False,
                "draft": {
                    "signal_field": "",
                    "expression": "",
                    "asof_rule": "",
                },
                "missing_items": [],
            },
            "event_contract": {
                "confirmed": False,
                "draft": {
                    "event_id_fields": ["asset", "timestamp", "param_id", "horizon"],
                    "horizons": [],
                    "event_trigger_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_train_freeze",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "03_tss_signal_ready"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_signal_ready_freeze_draft())
    return stage_dir


def build_tss_signal_ready_from_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_formal_dir = lineage_root / "02_tss_data_ready" / "author" / "formal"
    missing = [
        name
        for name in [
            "time_index_manifest.json",
            "asset_time_index.parquet",
            "quality_flags.parquet",
            "split_sample_adequacy_report.yaml",
            "run_manifest.json",
            "rebuild_tss_data_ready.py",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"tss_data_ready artifacts missing before tss_signal_ready build: {', '.join(missing)}")

    stage_dir = scaffold_tss_signal_ready(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    signal_identity = groups["signal_identity"]["draft"]
    input_contract = groups["input_contract"]["draft"]
    signal_expression = groups["signal_expression"]["draft"]
    event_contract = groups["event_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    signal_id = _required_value(signal_identity, "signal_id")
    signal_field = _required_value(signal_expression, "signal_field")
    horizons = _string_list(event_contract.get("horizons")) or ["1d"]
    input_field_map = input_contract.get("input_field_map")
    if not isinstance(input_field_map, list):
        input_field_map = []

    _dump_yaml(
        formal_dir / "signal_manifest.yaml",
        {
            "stage": "tss_signal_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "signal_id": signal_id,
            "signal_version": signal_identity.get("signal_version", "v1"),
            "signal_direction": signal_identity.get("signal_direction", ""),
            "target_asset": signal_identity.get("target_asset", ""),
            "primary_key": ["asset", "timestamp", "param_id", "horizon"],
            "timestamp_semantics": signal_expression.get("asof_rule", ""),
            "input_field_map": input_field_map,
            "input_roots": _string_list(input_contract.get("input_roots")),
            "output_signal_fields": [signal_field],
            "signal_field": signal_field,
            "expression": signal_expression.get("expression", ""),
            "asof_rule": signal_expression.get("asof_rule", ""),
            "horizons": horizons,
        },
    )
    _write_csv_rows(
        formal_dir / "param_manifest.csv",
        [{"param_id": "baseline", "horizon": horizons[0], "parameter_name": signal_id, "parameter_value": "frozen"}],
        ["param_id", "horizon", "parameter_name", "parameter_value"],
    )
    _write_parquet_rows(
        formal_dir / "signal_panel.parquet",
        [
            {
                "asset": signal_identity.get("target_asset", "BTCUSDT") or "BTCUSDT",
                "timestamp": "2024-01-01T00:00:00Z",
                "param_id": "baseline",
                "horizon": horizons[0],
                signal_field: 1.0,
            }
        ],
    )
    _write_parquet_rows(
        formal_dir / "signal_event_panel.parquet",
        [
            {
                "asset": signal_identity.get("target_asset", "BTCUSDT") or "BTCUSDT",
                "timestamp": "2024-01-01T00:00:00Z",
                "param_id": "baseline",
                "horizon": horizons[0],
                "event_name": "signal_triggered",
            }
        ],
    )
    source_route_artifact = "../01_mandate/author/formal/research_route.yaml"
    route_path = lineage_root / "01_mandate" / "author" / "formal" / "research_route.yaml"
    route_digest = hashlib.sha256(route_path.read_bytes()).hexdigest() if route_path.exists() else ""
    _dump_yaml(
        formal_dir / "route_inheritance_contract.yaml",
        {
            "stage": "tss_signal_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_route_artifact": source_route_artifact,
            "source_route_digest_sha256": route_digest,
            "inheritance_mode": "exact_copy",
        },
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_signal_ready",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_data_ready",
            "primary_key": ["asset", "timestamp", "param_id", "horizon"],
            "machine_artifacts": [
                "signal_manifest.yaml",
                "param_manifest.csv",
                "signal_panel.parquet",
                "signal_event_panel.parquet",
                "route_inheritance_contract.yaml",
                "run_manifest.json",
            ],
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_train_freeze"),
            "replay_command": "python -m runtime.tools.tss_signal_ready_runtime",
        },
    )

    semantic_result = validate_tss_signal_ready_semantics(formal_dir, lineage_root)
    if not semantic_result.valid:
        raise ValueError("tss_signal_ready formal artifacts do not pass semantic validation: " + "; ".join(semantic_result.errors))
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_SIGNAL_READY_FREEZE_DRAFT_FILE
    payload = _load_yaml(draft_path)
    groups = payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError(f"{draft_path.name}: groups must be a map")
    missing = [name for name in TSS_SIGNAL_READY_FREEZE_GROUP_ORDER if name not in groups]
    if missing:
        raise ValueError(f"{draft_path.name}: missing freeze groups: {', '.join(missing)}")
    unconfirmed = [name for name in TSS_SIGNAL_READY_FREEZE_GROUP_ORDER if not groups[name].get("confirmed")]
    if unconfirmed:
        raise ValueError(f"{draft_path.name}: freeze groups must be confirmed before build: {', '.join(unconfirmed)}")
    return groups


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise ValueError(f"{path.name}: yaml read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected yaml map")
    return payload


def _required_value(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} must be non-empty before tss_signal_ready build")
    return value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
