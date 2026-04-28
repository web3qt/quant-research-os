from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


TSS_TRAIN_FREEZE_DRAFT_FILE = "tss_train_freeze_draft.yaml"
TSS_TRAIN_FREEZE_GROUP_ORDER = [
    "calibration_contract",
    "threshold_contract",
    "search_governance_contract",
    "reuse_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _blank_tss_train_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "calibration_contract": {
                "confirmed": False,
                "draft": {
                    "train_window_source": "time_split.json::train",
                    "calibration_metric": "",
                    "calibration_note": "",
                },
                "missing_items": [],
            },
            "threshold_contract": {
                "confirmed": False,
                "draft": {
                    "threshold_field": "",
                    "candidate_thresholds": [],
                    "threshold_selection_rule": "",
                },
                "missing_items": [],
            },
            "search_governance_contract": {
                "confirmed": False,
                "draft": {
                    "candidate_variant_ids": [],
                    "kept_variant_ids": [],
                    "rejected_variant_ids": [],
                    "non_governable_axes_after_signal": ["input_field_map", "signal_expression"],
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": False,
                "draft": {
                    "frozen_signal_contract_reference": "03_tss_signal_ready/author/formal/signal_manifest.yaml",
                    "no_signal_redefinition_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "tss_test_evidence",
                    "reuse_constraints": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_tss_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "04_tss_train_freeze"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / TSS_TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_tss_train_freeze_draft())
    return stage_dir


def build_tss_train_freeze_from_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_formal_dir = lineage_root / "03_tss_signal_ready" / "author" / "formal"
    missing = [
        name
        for name in [
            "signal_manifest.yaml",
            "param_manifest.csv",
            "signal_panel.parquet",
            "signal_event_panel.parquet",
            "route_inheritance_contract.yaml",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"tss_signal_ready artifacts missing before tss_train_freeze build: {', '.join(missing)}")

    stage_dir = scaffold_tss_train_freeze(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    calibration_contract = groups["calibration_contract"]["draft"]
    threshold_contract = groups["threshold_contract"]["draft"]
    search_governance_contract = groups["search_governance_contract"]["draft"]
    reuse_contract = groups["reuse_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    candidate_ids = _string_list(search_governance_contract.get("candidate_variant_ids")) or ["baseline_v1"]
    kept_ids = _string_list(search_governance_contract.get("kept_variant_ids")) or candidate_ids[:1]
    rejected_ids = _string_list(search_governance_contract.get("rejected_variant_ids"))

    _dump_yaml(
        formal_dir / "tss_train_freeze.yaml",
        {
            "stage": "tss_train_freeze",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "primary_key": ["variant_id"],
            "train_window": {
                "source": calibration_contract.get("train_window_source", "time_split.json::train"),
            },
            "threshold_policy": threshold_contract.get("threshold_selection_rule", ""),
            "candidate_variant_ids": candidate_ids,
            "kept_variant_ids": kept_ids,
            "rejected_variant_ids": rejected_ids,
            "calibration_contract": calibration_contract,
            "threshold_contract": threshold_contract,
            "search_governance_contract": {
                **search_governance_contract,
                "candidate_variant_ids": candidate_ids,
                "kept_variant_ids": kept_ids,
                "rejected_variant_ids": rejected_ids,
            },
            "reuse_contract": reuse_contract,
            "delivery_contract": delivery_contract,
        },
    )
    thresholds = threshold_contract.get("candidate_thresholds")
    if not isinstance(thresholds, list) or not thresholds:
        thresholds = [0.0]
    _write_csv_rows(
        formal_dir / "train_threshold_ledger.csv",
        [
            {
                "variant_id": variant_id,
                "threshold_name": threshold_contract.get("threshold_field", "signal_value"),
                "threshold_value": thresholds[0],
                "selection_rule": threshold_contract.get("threshold_selection_rule", ""),
            }
            for variant_id in candidate_ids
        ],
        ["variant_id", "threshold_name", "threshold_value", "selection_rule"],
    )
    _write_csv_rows(
        formal_dir / "train_variant_ledger.csv",
        [
            {
                "variant_id": variant_id,
                "status": "kept" if variant_id in kept_ids else "rejected",
                "selection_rule": threshold_contract.get("threshold_selection_rule", ""),
            }
            for variant_id in candidate_ids
        ],
        ["variant_id", "status", "selection_rule"],
    )
    _write_csv_rows(
        formal_dir / "train_variant_rejects.csv",
        [{"variant_id": variant_id, "reject_reason": "not selected by train threshold rule"} for variant_id in rejected_ids],
        ["variant_id", "reject_reason"],
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_train_freeze",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_signal_ready",
            "primary_key": ["variant_id"],
            "machine_artifacts": [
                "tss_train_freeze.yaml",
                "train_threshold_ledger.csv",
                "train_variant_ledger.csv",
                "train_variant_rejects.csv",
                "run_manifest.json",
            ],
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_test_evidence"),
            "replay_command": "python -m runtime.tools.tss_train_runtime",
        },
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_TRAIN_FREEZE_DRAFT_FILE
    payload = _load_yaml(draft_path)
    groups = payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError(f"{draft_path.name}: groups must be a map")
    missing = [name for name in TSS_TRAIN_FREEZE_GROUP_ORDER if name not in groups]
    if missing:
        raise ValueError(f"{draft_path.name}: missing freeze groups: {', '.join(missing)}")
    unconfirmed = [name for name in TSS_TRAIN_FREEZE_GROUP_ORDER if not groups[name].get("confirmed")]
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
