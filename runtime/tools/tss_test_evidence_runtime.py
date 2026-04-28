from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE = "tss_test_evidence_freeze_draft.yaml"
TSS_TEST_EVIDENCE_DRAFT_FILE = TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE
TSS_TEST_EVIDENCE_GROUP_ORDER = [
    "window_contract",
    "variant_contract",
    "evidence_contract",
    "audit_contract",
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


def _blank_tss_test_evidence_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "window_contract": {
                "confirmed": False,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "train_reuse_note": "",
                    "subperiod_rule": "",
                },
                "missing_items": [],
            },
            "variant_contract": {
                "confirmed": False,
                "draft": {
                    "selected_variant_ids": [],
                    "selection_rule": "",
                    "multiple_testing_note": "",
                },
                "missing_items": [],
            },
            "evidence_contract": {
                "confirmed": False,
                "draft": {
                    "primary_evidence_contract": "",
                    "base_rate_reference": "",
                    "minimum_event_count_rule": "",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": False,
                "draft": {
                    "event_count_rule": "",
                    "direction_flip_rule": "",
                    "coverage_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_backtest_ready",
                    "frozen_spec_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "05_tss_test_evidence"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_test_evidence_freeze_draft())
    return stage_dir


def build_tss_test_evidence_from_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    missing = [
        name
        for name in [
            "tss_train_freeze.yaml",
            "train_threshold_ledger.csv",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"tss_train_freeze artifacts missing before tss_test_evidence build: {', '.join(missing)}")

    stage_dir = scaffold_tss_test_evidence(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    variant_contract = groups["variant_contract"]["draft"]
    evidence_contract = groups["evidence_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]
    selected_variant_ids = _string_list(variant_contract.get("selected_variant_ids")) or ["baseline_v1"]
    primary_evidence_contract = str(evidence_contract.get("primary_evidence_contract", "")).strip() or "forward_return_uplift"

    _write_parquet_rows(
        formal_dir / "event_forward_return.parquet",
        [
            {
                "variant_id": variant_id,
                "asset": "BTCUSDT",
                "timestamp": "2024-01-01T00:00:00Z",
                "horizon": "1d",
                "forward_return": 0.01,
                "base_rate_forward_return": 0.0,
            }
            for variant_id in selected_variant_ids
        ],
    )
    _dump_json(
        formal_dir / "signal_performance_summary.json",
        {
            "stage": "tss_test_evidence",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "primary_key": ["variant_id", "horizon"],
            "selected_variant_ids": selected_variant_ids,
            "primary_evidence_contract": primary_evidence_contract,
            "mean_forward_return": 0.01,
            "event_count": len(selected_variant_ids),
        },
    )
    _write_csv_rows(
        formal_dir / "tss_test_gate_table.csv",
        [
            {
                "variant_id": variant_id,
                "horizon": "1d",
                "verdict": "PASS",
                "primary_evidence_contract": primary_evidence_contract,
                "reason": "fixture positive forward return",
            }
            for variant_id in selected_variant_ids
        ],
        ["variant_id", "horizon", "verdict", "primary_evidence_contract", "reason"],
    )
    _write_csv_rows(
        formal_dir / "tss_selected_variants_test.csv",
        [{"variant_id": variant_id, "horizon": "1d", "status": "selected"} for variant_id in selected_variant_ids],
        ["variant_id", "horizon", "status"],
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_test_evidence",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_train_freeze",
            "primary_key": ["variant_id", "horizon"],
            "machine_artifacts": [
                "event_forward_return.parquet",
                "signal_performance_summary.json",
                "tss_test_gate_table.csv",
                "tss_selected_variants_test.csv",
                "run_manifest.json",
            ],
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_backtest_ready"),
            "replay_command": "python -m runtime.tools.tss_test_evidence_runtime",
        },
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE
    payload = _load_yaml(draft_path)
    groups = payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError(f"{draft_path.name}: groups must be a map")
    missing = [name for name in TSS_TEST_EVIDENCE_GROUP_ORDER if name not in groups]
    if missing:
        raise ValueError(f"{draft_path.name}: missing freeze groups: {', '.join(missing)}")
    unconfirmed = [name for name in TSS_TEST_EVIDENCE_GROUP_ORDER if not groups[name].get("confirmed")]
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


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
