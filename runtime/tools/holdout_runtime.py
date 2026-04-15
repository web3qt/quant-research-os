from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


HOLDOUT_VALIDATION_DRAFT_FILE = "holdout_validation_draft.yaml"
HOLDOUT_VALIDATION_GROUP_ORDER = [
    "window_contract",
    "reuse_contract",
    "drift_audit",
    "failure_governance",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_holdout_validation_draft(
    *,
    selected_symbols: list[str] | None = None,
    best_h: str = "",
) -> dict[str, Any]:
    symbols = selected_symbols or []
    return {
        "groups": {
            "window_contract": {
                "confirmed": False,
                "draft": {
                    "holdout_window_source": "time_split.json::holdout",
                    "window_plan": ["single_window", "merged_window"],
                    "window_note": "",
                    "no_redefinition_guardrail": "",
                },
                "missing_items": [],
            },
            "reuse_contract": {
                "confirmed": False,
                "draft": {
                    "frozen_config_source": "06_backtest/backtest_frozen_config.json",
                    "selected_combo_source": "06_backtest/selected_strategy_combo.json",
                    "selected_symbols": symbols,
                    "best_h": best_h,
                    "no_reestimate_rule": "",
                    "no_whitelist_change_rule": "",
                },
                "missing_items": [],
            },
            "drift_audit": {
                "confirmed": False,
                "draft": {
                    "required_views": ["single_window", "merged_window"],
                    "direction_flip_rule": "",
                    "sparse_activity_rule": "",
                    "explanatory_note": "",
                },
                "missing_items": [],
            },
            "failure_governance": {
                "confirmed": False,
                "draft": {
                    "retryable_conditions": [],
                    "no_go_conditions": [],
                    "child_lineage_trigger": "",
                    "rollback_boundary": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [
                        "holdout_run_manifest.json",
                        "holdout_backtest_compare.csv",
                        "window_results/",
                    ],
                    "consumer_stage": "terminal",
                    "field_doc_rule": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_holdout_validation(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    holdout_dir = lineage_root / "07_holdout"
    layout = ensure_stage_author_layout(holdout_dir)

    draft_path = layout["author_draft_dir"] / HOLDOUT_VALIDATION_DRAFT_FILE
    if not draft_path.exists():
        selected_symbols, best_h = _load_backtest_context(lineage_root)
        _dump_yaml(
            draft_path,
            _blank_holdout_validation_draft(selected_symbols=selected_symbols, best_h=best_h),
        )
    return holdout_dir


def build_holdout_validation_from_backtest(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    mandate_dir = lineage_root / "01_mandate"
    backtest_dir = lineage_root / "06_backtest"
    holdout_dir = scaffold_holdout_validation(lineage_root)
    mandate_formal_dir = ensure_stage_author_layout(mandate_dir)["author_formal_dir"]
    backtest_formal_dir = ensure_stage_author_layout(backtest_dir)["author_formal_dir"]
    holdout_layout = ensure_stage_author_layout(holdout_dir)
    holdout_formal_dir = holdout_layout["author_formal_dir"]

    missing_inputs: list[str] = []
    for path in [
        mandate_formal_dir / "time_split.json",
        backtest_formal_dir / "backtest_frozen_config.json",
        backtest_formal_dir / "selected_strategy_combo.json",
    ]:
        if not path.exists():
            missing_inputs.append(str(path.relative_to(lineage_root)))
    if missing_inputs:
        raise ValueError(
            "upstream artifacts missing before holdout_validation build: "
            + ", ".join(missing_inputs)
        )

    freeze_groups = _require_confirmed_freeze_groups(holdout_dir)
    window_contract = freeze_groups["window_contract"]["draft"]
    reuse_contract = freeze_groups["reuse_contract"]["draft"]
    drift_audit = freeze_groups["drift_audit"]["draft"]
    failure_governance = freeze_groups["failure_governance"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    holdout_window_source = _required_draft_value(window_contract, "holdout_window_source")
    window_plan = _string_list(window_contract.get("window_plan", []))
    window_note = _required_draft_value(window_contract, "window_note")
    no_redefinition_guardrail = _required_draft_value(window_contract, "no_redefinition_guardrail")

    frozen_config_source = _required_draft_value(reuse_contract, "frozen_config_source")
    selected_combo_source = _required_draft_value(reuse_contract, "selected_combo_source")
    selected_symbols = _string_list(reuse_contract.get("selected_symbols", []))
    best_h = _required_draft_value(reuse_contract, "best_h")
    no_reestimate_rule = _required_draft_value(reuse_contract, "no_reestimate_rule")
    no_whitelist_change_rule = _required_draft_value(reuse_contract, "no_whitelist_change_rule")

    required_views = _string_list(drift_audit.get("required_views", []))
    direction_flip_rule = _required_draft_value(drift_audit, "direction_flip_rule")
    sparse_activity_rule = _required_draft_value(drift_audit, "sparse_activity_rule")
    explanatory_note = _required_draft_value(drift_audit, "explanatory_note")

    retryable_conditions = _string_list(failure_governance.get("retryable_conditions", []))
    no_go_conditions = _string_list(failure_governance.get("no_go_conditions", []))
    child_lineage_trigger = _required_draft_value(failure_governance, "child_lineage_trigger")
    rollback_boundary = _required_draft_value(failure_governance, "rollback_boundary")

    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    field_doc_rule = _required_draft_value(delivery_contract, "field_doc_rule")

    backtest_symbols, backtest_best_h = _load_backtest_context(lineage_root)
    if not selected_symbols:
        selected_symbols = list(backtest_symbols)
    if not selected_symbols:
        raise ValueError("selected_symbols must contain at least one symbol")
    unknown_symbols = sorted(set(selected_symbols) - set(backtest_symbols))
    if unknown_symbols:
        raise ValueError(
            "selected_symbols must be drawn from backtest frozen config: " + ", ".join(unknown_symbols)
        )
    if backtest_best_h and best_h != backtest_best_h:
        raise ValueError("best_h must match the frozen backtest best_h")

    if "single_window" not in required_views or "merged_window" not in required_views:
        raise ValueError("required_views must include single_window and merged_window")

    run_manifest = {
        "stage": "holdout_validation",
        "lineage_id": lineage_root.name,
        "source_stage": "backtest_ready",
        "holdout_window_source": holdout_window_source,
        "window_plan": window_plan,
        "window_note": window_note,
        "frozen_config_source": frozen_config_source,
        "selected_combo_source": selected_combo_source,
        "selected_symbols": selected_symbols,
        "best_h": best_h,
        "required_views": required_views,
        "consumer_stage": consumer_stage,
        "field_doc_rule": field_doc_rule,
    }
    (holdout_formal_dir / "holdout_run_manifest.json").write_text(
        json.dumps(run_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with (holdout_formal_dir / "holdout_backtest_compare.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["view", "direction_flip_flag", "structure_status", "note"])
        writer.writerow(["single_window", "false", "stable_pending_review", direction_flip_rule])
        writer.writerow(["merged_window", "false", "stable_pending_review", explanatory_note])

    results_dir = holdout_formal_dir / "window_results"
    results_dir.mkdir(exist_ok=True)
    for window_name in ("holdout_window_1", "holdout_merged"):
        window_dir = results_dir / window_name
        window_dir.mkdir(exist_ok=True)
        (window_dir / "portfolio_summary.parquet").write_text(
            f"{window_name} 的占位 portfolio summary\n",
            encoding="utf-8",
        )
        (window_dir / "trades.parquet").write_text(
            f"{window_name} 的占位 trades 产物\n",
            encoding="utf-8",
        )
        (window_dir / "portfolio_timeseries.parquet").write_text(
            f"{window_name} 的占位 portfolio timeseries 产物\n",
            encoding="utf-8",
        )
        (window_dir / "summary.txt").write_text(
            "\n".join(
                [
                    f"窗口: {window_name}",
                    f"已选 symbols: {', '.join(selected_symbols)}",
                    f"Best horizon: {best_h}",
                    f"稀疏活动规则: {sparse_activity_rule}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    (holdout_formal_dir / "holdout_gate_decision.md").write_text(
        "\n".join(
            [
                "# Holdout Gate Decision",
                "",
                "- 在 review findings 和 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- Holdout 窗口来源: {holdout_window_source}",
                f"- 禁止重估规则: {no_reestimate_rule}",
                f"- 禁止 whitelist 变更规则: {no_whitelist_change_rule}",
                f"- 方向翻转规则: {direction_flip_rule}",
                f"- CHILD LINEAGE 触发条件: {child_lineage_trigger}",
                f"- 下游消费阶段: {consumer_stage}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (holdout_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- holdout_run_manifest.json",
                "- holdout_backtest_compare.csv",
                "- window_results/",
                "- holdout_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (holdout_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `holdout_window_source`: holdout 窗口的冻结来源，当前为 `{holdout_window_source}`。",
                f"- `selected_symbols`: 在 holdout 中复用的 backtest 冻结 whitelist，当前为 {selected_symbols}。",
                f"- `best_h`: 在 holdout 中复用的冻结持有窗口，当前为 `{best_h}`。",
                f"- `required_views`: 必需比较视角，当前为 {required_views}。",
                f"- `retryable_conditions`: 允许受控重跑的条件，当前为 {retryable_conditions}。",
                f"- `no_go_conditions`: formal no-go 条件，当前为 {no_go_conditions}。",
                f"- `rollback_boundary`: holdout 的回滚边界，当前为 `{rollback_boundary}`。",
                f"- `machine_artifacts`: 本阶段正式机器产物集合，当前为 {machine_artifacts}。",
                f"- `field_doc_rule`: 字段文档要求，当前为 `{field_doc_rule}`。",
                f"- `no_redefinition_guardrail`: 禁止重定义 holdout 目的的护栏，当前为 `{no_redefinition_guardrail}`。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return holdout_dir


def _load_backtest_context(lineage_root: Path) -> tuple[list[str], str]:
    config_path = lineage_root / "06_backtest" / "author" / "formal" / "backtest_frozen_config.json"
    selected_combo_path = lineage_root / "06_backtest" / "author" / "formal" / "selected_strategy_combo.json"
    selected_symbols: list[str] = []
    best_h = ""

    for path in (config_path, selected_combo_path):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if not selected_symbols:
            selected_symbols = _string_list(payload.get("selected_symbols", []))
        if not best_h:
            best_h = str(payload.get("best_h", "")).strip()

    return selected_symbols, best_h


def _require_confirmed_freeze_groups(holdout_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(holdout_dir)["author_draft_dir"] / HOLDOUT_VALIDATION_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [
        name for name in HOLDOUT_VALIDATION_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing:
        raise ValueError(
            "holdout_validation draft groups must be confirmed before build: " + ", ".join(missing)
        )
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"holdout_validation draft missing required value: {key}")
    return value


def _string_list(values: list[Any]) -> list[str]:
    return [str(item).strip() for item in values if str(item).strip()]
