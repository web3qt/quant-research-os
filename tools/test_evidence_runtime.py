from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


TEST_EVIDENCE_DRAFT_FILE = "test_evidence_draft.yaml"
TEST_EVIDENCE_GROUP_ORDER = [
    "window_contract",
    "formal_gate_contract",
    "admissibility_contract",
    "audit_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_test_evidence_draft(
    *,
    candidate_param_ids: list[str] | None = None,
    candidate_horizons: list[str] | None = None,
) -> dict[str, Any]:
    param_ids = candidate_param_ids or []
    horizons = candidate_horizons or []
    return {
        "groups": {
            "window_contract": {
                "confirmed": False,
                "draft": {
                    "test_window_source": "time_split.json::test",
                    "test_window_note": "",
                    "train_reuse_note": "",
                },
                "missing_items": [],
            },
            "formal_gate_contract": {
                "confirmed": False,
                "draft": {
                    "selected_param_ids": param_ids,
                    "candidate_best_h": horizons,
                    "best_h": "",
                    "formal_gate_note": "",
                    "threshold_reuse_note": "",
                },
                "missing_items": [],
            },
            "admissibility_contract": {
                "confirmed": False,
                "draft": {
                    "selected_symbols": [],
                    "admissibility_rule": "",
                    "rejection_rule": "",
                    "summary_note": "",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": False,
                "draft": {
                    "audit_items": [
                        "HAC t value",
                        "monotonic score",
                        "crowding overlap",
                    ],
                    "formal_vs_audit_boundary": "",
                    "crowding_scope": "",
                    "condition_analysis_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [
                        "report_by_h.parquet",
                        "symbol_summary.parquet",
                        "admissibility_report.parquet",
                        "test_gate_table.csv",
                        "selected_symbols_test.csv",
                        "selected_symbols_test.parquet",
                        "frozen_spec.json",
                    ],
                    "consumer_stage": "backtest_ready",
                    "frozen_spec_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    test_dir = lineage_root / "05_test_evidence"
    test_dir.mkdir(parents=True, exist_ok=True)

    draft_path = test_dir / TEST_EVIDENCE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(
            draft_path,
            _blank_test_evidence_draft(
                candidate_param_ids=_load_train_param_ids(lineage_root),
                candidate_horizons=_load_holding_horizons(lineage_root),
            ),
        )
    return test_dir


def build_test_evidence_from_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    data_ready_dir = lineage_root / "02_data_ready"
    signal_ready_dir = lineage_root / "03_signal_ready"
    train_dir = lineage_root / "04_train_freeze"
    mandate_dir = lineage_root / "01_mandate"
    test_dir = scaffold_test_evidence(lineage_root)

    missing_inputs: list[str] = []
    for path in [
        signal_ready_dir / "params",
        signal_ready_dir / "param_manifest.csv",
        train_dir / "train_thresholds.json",
        train_dir / "train_param_ledger.csv",
        data_ready_dir / "aligned_bars",
        mandate_dir / "time_split.json",
    ]:
        if not path.exists():
            missing_inputs.append(str(path.relative_to(lineage_root)))
    if missing_inputs:
        raise ValueError(
            "upstream artifacts missing before test_evidence build: " + ", ".join(missing_inputs)
        )

    freeze_groups = _require_confirmed_freeze_groups(test_dir)
    window_contract = freeze_groups["window_contract"]["draft"]
    formal_gate_contract = freeze_groups["formal_gate_contract"]["draft"]
    admissibility_contract = freeze_groups["admissibility_contract"]["draft"]
    audit_contract = freeze_groups["audit_contract"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    test_window_source = _required_draft_value(window_contract, "test_window_source")
    test_window_note = _required_draft_value(window_contract, "test_window_note")
    train_reuse_note = _required_draft_value(window_contract, "train_reuse_note")

    selected_param_ids = _string_list(formal_gate_contract.get("selected_param_ids", []))
    candidate_best_h = _string_list(formal_gate_contract.get("candidate_best_h", []))
    best_h = _required_draft_value(formal_gate_contract, "best_h")
    formal_gate_note = _required_draft_value(formal_gate_contract, "formal_gate_note")
    threshold_reuse_note = _required_draft_value(formal_gate_contract, "threshold_reuse_note")

    selected_symbols = _string_list(admissibility_contract.get("selected_symbols", []))
    admissibility_rule = _required_draft_value(admissibility_contract, "admissibility_rule")
    rejection_rule = _required_draft_value(admissibility_contract, "rejection_rule")
    summary_note = _required_draft_value(admissibility_contract, "summary_note")

    audit_items = _string_list(audit_contract.get("audit_items", []))
    formal_vs_audit_boundary = _required_draft_value(audit_contract, "formal_vs_audit_boundary")
    crowding_scope = _required_draft_value(audit_contract, "crowding_scope")
    condition_analysis_note = _required_draft_value(audit_contract, "condition_analysis_note")

    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_spec_note = _required_draft_value(delivery_contract, "frozen_spec_note")

    if not selected_param_ids:
        selected_param_ids = _load_train_param_ids(lineage_root)
    if best_h not in candidate_best_h and candidate_best_h:
        raise ValueError("best_h must be one of candidate_best_h")
    if not selected_symbols:
        raise ValueError("selected_symbols must contain at least one symbol")

    kept_param_ids = _load_train_param_ids(lineage_root)
    unknown_param_ids = sorted(set(selected_param_ids) - set(kept_param_ids))
    if unknown_param_ids:
        raise ValueError(
            "selected_param_ids must be drawn from train-kept param ids: " + ", ".join(unknown_param_ids)
        )

    (test_dir / "report_by_h.parquet").write_text(
        "\n".join(
            [
                "governance-first test_evidence 阶段的占位 report_by_h 产物",
                f"candidate_best_h={','.join(candidate_best_h)}",
                f"best_h={best_h}",
                f"formal_gate_note={formal_gate_note}",
                f"threshold_reuse_note={threshold_reuse_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "symbol_summary.parquet").write_text(
        "\n".join(
            [
                "governance-first test_evidence 阶段的占位 symbol_summary 产物",
                f"selected_symbols={','.join(selected_symbols)}",
                f"summary_note={summary_note}",
                f"admissibility_rule={admissibility_rule}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "admissibility_report.parquet").write_text(
        "\n".join(
            [
                "governance-first test_evidence 阶段的占位 admissibility 报告",
                f"admissibility_rule={admissibility_rule}",
                f"rejection_rule={rejection_rule}",
                f"selected_symbols={','.join(selected_symbols)}",
                f"selected_param_ids={','.join(selected_param_ids)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with (test_dir / "test_gate_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gate_type", "status", "note"])
        writer.writerow(["formal_gate", "PENDING_REVIEW", formal_gate_note])
        writer.writerow(["audit_gate", "PENDING_REVIEW", formal_vs_audit_boundary])

    (test_dir / "crowding_review.md").write_text(
        "\n".join(
            [
                "# Crowding Review",
                "",
                f"- 审计范围: {crowding_scope}",
                f"- Formal 与 audit 边界: {formal_vs_audit_boundary}",
                f"- 条件分析说明: {condition_analysis_note}",
                "",
                "## 审计项",
                "",
                *[f"- {item}" for item in audit_items],
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with (test_dir / "selected_symbols_test.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["symbol", "param_id", "best_h"])
        for symbol in selected_symbols:
            for param_id in selected_param_ids:
                writer.writerow([symbol, param_id, best_h])

    (test_dir / "selected_symbols_test.parquet").write_text(
        "\n".join(
            [
                "selected symbols 的占位 parquet 镜像",
                f"symbols={','.join(selected_symbols)}",
                f"param_ids={','.join(selected_param_ids)}",
                f"best_h={best_h}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "frozen_spec.json").write_text(
        json.dumps(
            {
                "stage": "test_evidence",
                "lineage_id": lineage_root.name,
                "source_stage": "train_calibration",
                "test_window_source": test_window_source,
                "test_window_note": test_window_note,
                "train_reuse_note": train_reuse_note,
                "selected_param_ids": selected_param_ids,
                "selected_symbols": selected_symbols,
                "best_h": best_h,
                "thresholds_source": "04_train_freeze/train_thresholds.json",
                "formal_gate_note": formal_gate_note,
                "formal_vs_audit_boundary": formal_vs_audit_boundary,
                "audit_items": audit_items,
                "consumer_stage": consumer_stage,
                "frozen_spec_note": frozen_spec_note,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "test_gate_decision.md").write_text(
        "\n".join(
            [
                "# Test Gate Decision",
                "",
                "- 在 review findings 和 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- Test 窗口来源: {test_window_source}",
                f"- 已选 symbols: {', '.join(selected_symbols)}",
                f"- 已选 param_ids: {', '.join(selected_param_ids)}",
                f"- 已冻结 best_h: {best_h}",
                f"- 下游消费阶段: {consumer_stage}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- report_by_h.parquet",
                "- symbol_summary.parquet",
                "- admissibility_report.parquet",
                "- test_gate_table.csv",
                "- crowding_review.md",
                "- selected_symbols_test.csv",
                "- selected_symbols_test.parquet",
                "- frozen_spec.json",
                "- test_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (test_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `test_window_source`: 上游 test 切分引用，当前为 `{test_window_source}`。",
                f"- `selected_param_ids`: 经 train 批准后进入 test 的参数 ID，当前为 {selected_param_ids}。",
                f"- `selected_symbols`: 冻结后纳入 backtest 评估的 whitelist，当前为 {selected_symbols}。",
                f"- `best_h`: 为下游消费者冻结的持有窗口，当前为 `{best_h}`。",
                f"- `formal_gate_note`: formal test gate 的摘要说明，当前为 `{formal_gate_note}`。",
                f"- `audit_items`: 本阶段跟踪的 audit-only 证据项，当前为 {audit_items}。",
                f"- `machine_artifacts`: 本阶段正式机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return test_dir


def _load_holding_horizons(lineage_root: Path) -> list[str]:
    time_split_path = lineage_root / "01_mandate" / "time_split.json"
    if not time_split_path.exists():
        return []
    payload = json.loads(time_split_path.read_text(encoding="utf-8"))
    return _string_list(payload.get("holding_horizons", []))


def _load_train_param_ids(lineage_root: Path) -> list[str]:
    ledger_path = lineage_root / "04_train_freeze" / "train_param_ledger.csv"
    if not ledger_path.exists():
        return []

    rows = ledger_path.read_text(encoding="utf-8").splitlines()
    if len(rows) <= 1:
        return []

    param_ids: list[str] = []
    for row in rows[1:]:
        parts = row.split(",")
        if len(parts) < 2:
            continue
        param_id = parts[0].strip()
        status = parts[1].strip()
        if param_id and status == "kept":
            param_ids.append(param_id)
    return param_ids


def _require_confirmed_freeze_groups(test_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((test_dir / TEST_EVIDENCE_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})

    missing = [name for name in TEST_EVIDENCE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"test_evidence draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"test_evidence draft missing required value: {key}")
    return value


def _string_list(values: list[Any]) -> list[str]:
    return [str(item).strip() for item in values if str(item).strip()]
