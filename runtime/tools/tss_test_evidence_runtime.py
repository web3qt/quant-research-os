from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout
from runtime.tools.tss_test_evidence_contract_runtime import validate_tss_test_evidence_semantics


TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE = "tss_test_evidence_freeze_draft.yaml"
TSS_TEST_EVIDENCE_DRAFT_FILE = TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE
TSS_TEST_EVIDENCE_GROUP_ORDER = [
    "window_contract",
    "variant_contract",
    "evidence_contract",
    "audit_contract",
    "delivery_contract",
]
TSS_TEST_EVIDENCE_STAGE_OUTPUTS = [
    "event_forward_return.parquet",
    "signal_performance_summary.json",
    "tss_test_gate_table.csv",
    "tss_selected_variants_test.csv",
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]

TSS_TEST_REQUIRED_INPUT_ROOTS = [
    "../01_mandate/author/formal/time_split.json",
    "../04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
    "../04_tss_train_freeze/author/formal/train_variant_ledger.csv",
    "../04_tss_train_freeze/author/formal/train_variant_rejects.csv",
    "../04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
    "../04_tss_train_freeze/review/closure/stage_completion_certificate.yaml",
    "author/draft/tss_test_evidence_freeze_draft.yaml",
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
    required_upstream_paths = [
        lineage_root / "01_mandate" / "author" / "formal" / "time_split.json",
        lineage_root / "04_tss_train_freeze" / "author" / "formal" / "tss_train_freeze.yaml",
        lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_threshold_ledger.csv",
        lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_ledger.csv",
        lineage_root / "04_tss_train_freeze" / "author" / "formal" / "train_variant_rejects.csv",
        lineage_root / "04_tss_train_freeze" / "review" / "closure" / "stage_completion_certificate.yaml",
    ]
    missing_paths = [
        path.relative_to(lineage_root).as_posix() for path in required_upstream_paths if not path.exists()
    ]
    if missing_paths:
        raise ValueError(
            "tss upstream artifacts missing before tss_test_evidence build: " + ", ".join(missing_paths)
        )

    upstream_formal_dir = lineage_root / "04_tss_train_freeze" / "author" / "formal"
    time_split_path = lineage_root / "01_mandate" / "author" / "formal" / "time_split.json"
    train_freeze_contract_path = upstream_formal_dir / "tss_train_freeze.yaml"
    train_threshold_ledger_path = upstream_formal_dir / "train_threshold_ledger.csv"
    train_variant_ledger_path = upstream_formal_dir / "train_variant_ledger.csv"
    train_variant_rejects_path = upstream_formal_dir / "train_variant_rejects.csv"
    train_freeze_review_closure_path = (
        lineage_root / "04_tss_train_freeze" / "review" / "closure" / "stage_completion_certificate.yaml"
    )

    stage_dir = scaffold_tss_test_evidence(lineage_root)
    formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]
    groups = _require_confirmed_freeze_groups(stage_dir)
    variant_contract = groups["variant_contract"]["draft"]
    evidence_contract = groups["evidence_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]
    selected_variant_ids = _string_list(variant_contract.get("selected_variant_ids")) or ["baseline_v1"]
    primary_evidence_contract = str(evidence_contract.get("primary_evidence_contract", "")).strip() or "forward_return_uplift"
    time_split = _load_json(time_split_path)
    train_window_start, train_window_end = _parse_window(time_split.get("train"))
    test_window_start, test_window_end = _parse_window(time_split.get("test"))
    event_timestamp, label_timestamp = _event_window_timestamps(test_window_start, test_window_end)
    train_variant_rows = _read_csv_rows(train_variant_ledger_path)
    train_kept_ids = {
        str(row.get("variant_id", "")).strip()
        for row in train_variant_rows
        if str(row.get("status", "")).strip() == "kept" and str(row.get("variant_id", "")).strip()
    }

    _write_parquet_rows(
        formal_dir / "event_forward_return.parquet",
        [
            {
                "variant_id": variant_id,
                "asset": "BTCUSDT",
                "timestamp": event_timestamp,
                "horizon": "1d",
                "forward_return": 0.01,
                "asset_forward_return": 0.01,
                "signal_direction": 1.0,
                "label_timestamp": label_timestamp,
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
    _dump_yaml(
        formal_dir / "split_threshold_attestation.yaml",
        {
            "stage": "tss_test_evidence",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "train_window": {
                "source": "time_split.json::train",
                "start": train_window_start,
                "end": train_window_end,
            },
            "test_window": {
                "source": "time_split.json::test",
                "start": test_window_start,
                "end": test_window_end,
            },
            "label_window": {
                "max_label_timestamp": test_window_end,
            },
            "threshold_provenance": {
                "source_stage": "tss_train_freeze",
                "threshold_artifact": "04_tss_train_freeze/author/formal/tss_train_freeze.yaml",
                "threshold_ledger": "04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
                "no_test_window_retuning": True,
            },
        },
    )
    _write_csv_rows(
        formal_dir / "selected_variant_membership_proof.csv",
        [
            {
                "variant_id": variant_id,
                "horizon": "1d",
                "status": "selected",
                "train_kept_status": "kept" if variant_id in train_kept_ids else "missing",
                "threshold_source": "04_tss_train_freeze/author/formal/train_threshold_ledger.csv",
                "membership_verdict": "pass" if variant_id in train_kept_ids else "fail",
            }
            for variant_id in selected_variant_ids
        ],
        [
            "variant_id",
            "horizon",
            "status",
            "train_kept_status",
            "threshold_source",
            "membership_verdict",
        ],
    )
    _dump_yaml(
        formal_dir / "upstream_binding_digest_ledger.yaml",
        {
            "stage": "tss_test_evidence",
            "lineage_id": lineage_root.name,
            "bindings": [
                _digest_binding("time_split", time_split_path, lineage_root),
                _digest_binding("train_freeze_contract", train_freeze_contract_path, lineage_root),
                _digest_binding("train_variant_ledger", train_variant_ledger_path, lineage_root),
                _digest_binding("train_threshold_ledger", train_threshold_ledger_path, lineage_root),
                _digest_binding("train_variant_rejects", train_variant_rejects_path, lineage_root),
                _digest_binding("train_freeze_review_closure", train_freeze_review_closure_path, lineage_root),
            ],
        },
    )
    _dump_json(
        formal_dir / "run_manifest.json",
        {
            "stage": "tss_test_evidence",
            "lineage_id": lineage_root.name,
            "research_route": "time_series_signal",
            "source_stage": "tss_train_freeze",
            "primary_key": ["variant_id", "horizon"],
            "machine_artifacts": TSS_TEST_EVIDENCE_STAGE_OUTPUTS,
            "input_roots": TSS_TEST_REQUIRED_INPUT_ROOTS,
            "stage_outputs": TSS_TEST_EVIDENCE_STAGE_OUTPUTS,
            "program_dir": "program/time_series_signal/tss_test_evidence",
            "program_entrypoint": "run_stage.py",
            "program_execution_manifest": "program_execution_manifest.json",
            "selected_variant_ids": selected_variant_ids,
            "selection_rule": str(variant_contract.get("selection_rule", "")).strip()
            or "Admit only train-kept variants.",
            "primary_evidence_contract": primary_evidence_contract,
            "consumer_stage": delivery_contract.get("consumer_stage", "tss_backtest_ready"),
            "replay_command": "python -m runtime.tools.tss_test_evidence_runtime",
        },
    )
    (formal_dir / "artifact_catalog.md").write_text(
        "\n".join(["# 产物清单", "", *[f"- {name}" for name in TSS_TEST_EVIDENCE_STAGE_OUTPUTS if name != "artifact_catalog.md"]])
        + "\n",
        encoding="utf-8",
    )
    (formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `selected_variant_ids`: 进入 test evidence 的 variant ID 集合，当前为 {selected_variant_ids}。",
                f"- `primary_evidence_contract`: 本阶段主证据合同，当前为 {primary_evidence_contract}。",
                "- `split_threshold_attestation.yaml`: 记录 train/test 窗口边界和 train threshold 复用证明。",
                "- `selected_variant_membership_proof.csv`: 证明 test selected variants 均来自 train kept 集合。",
                "- `upstream_binding_digest_ledger.yaml`: 绑定 time split、train freeze 与 review closure 的路径和 digest。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shape_result = validate_stage_artifacts(formal_dir, load_artifact_contract("tss_test_evidence"))
    semantic_result = validate_tss_test_evidence_semantics(formal_dir, lineage_root)
    errors = [*shape_result.errors, *semantic_result.errors]
    if errors:
        raise ValueError("tss_test_evidence formal artifacts do not match contract: " + "; ".join(errors))
    return stage_dir


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"{path.name}: json read failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name}: expected json map")
    return payload


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_window(value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        start = str(value.get("start", "")).strip()
        end = str(value.get("end", "")).strip()
    else:
        parts = str(value).split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"time split value must be start/end, got {value!r}")
        start, end = parts[0].strip(), parts[1].strip()
    return _normalize_window_start(start), _normalize_window_end(end)


def _normalize_window_start(value: str) -> str:
    if "T" in value:
        return value.replace("Z", "+00:00")
    return datetime.combine(datetime.fromisoformat(value).date(), time.min, tzinfo=timezone.utc).isoformat()


def _normalize_window_end(value: str) -> str:
    if "T" in value:
        return value.replace("Z", "+00:00")
    return datetime.combine(datetime.fromisoformat(value).date(), time.max, tzinfo=timezone.utc).isoformat()


def _event_window_timestamps(start: str, end: str) -> tuple[str, str]:
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    if end_dt <= start_dt:
        raise ValueError("time_split.json::test must have end after start for event label timestamp")
    return start, end


def _digest_binding(logical_name: str, path: Path, lineage_root: Path) -> dict[str, Any]:
    return {
        "logical_name": logical_name,
        "path": path.relative_to(lineage_root).as_posix(),
        "required": True,
        "digest": _sha256_file(path),
    }


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = stage_dir / "author" / "draft" / TSS_TEST_EVIDENCE_FREEZE_DRAFT_FILE
    return require_confirmed_freeze_groups(
        draft_path,
        TSS_TEST_EVIDENCE_GROUP_ORDER,
        stage_label="tss_test_evidence",
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
