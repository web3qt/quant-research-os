from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


CSF_HOLDOUT_VALIDATION_DRAFT_FILE = "csf_holdout_validation_draft.yaml"
CSF_HOLDOUT_VALIDATION_GROUP_ORDER = [
    "window_contract",
    "reuse_contract",
    "stability_contract",
    "failure_governance",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_holdout_validation_draft() -> dict[str, Any]:
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
                    "backtest_contract_source": "",
                    "test_contract_source": "",
                    "variant_reuse_rule": "",
                    "no_reestimate_rule": "",
                },
                "missing_items": [],
            },
            "stability_contract": {
                "confirmed": False,
                "draft": {
                    "direction_flip_rule": "",
                    "coverage_rule": "",
                    "regime_shift_rule": "",
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
                    "consumer_stage": "",
                    "field_doc_rule": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_holdout_validation(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "07_csf_holdout_validation"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_holdout_validation_draft())
    return stage_dir


def build_csf_holdout_validation_from_backtest(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "06_csf_backtest_ready"
    mandate_dir = lineage_root / "01_mandate"
    stage_dir = scaffold_csf_holdout_validation(lineage_root)
    upstream_formal_dir = ensure_stage_author_layout(upstream_dir)["author_formal_dir"]
    mandate_formal_dir = ensure_stage_author_layout(mandate_dir)["author_formal_dir"]
    stage_formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]

    missing = [
        name
        for name in [
            "portfolio_contract.yaml",
            "portfolio_weight_panel.parquet",
            "rebalance_ledger.csv",
            "turnover_capacity_report.parquet",
            "cost_assumption_report.md",
            "portfolio_summary.parquet",
            "name_level_metrics.parquet",
            "drawdown_report.json",
            "target_strategy_compare.parquet",
            "csf_backtest_gate_table.csv",
            "csf_backtest_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(
            f"csf_backtest_ready artifacts missing before csf_holdout_validation build: {', '.join(missing)}"
        )

    groups = _require_confirmed_freeze_groups(stage_dir)
    window_contract = groups["window_contract"]["draft"]
    reuse_contract = groups["reuse_contract"]["draft"]
    stability_contract = groups["stability_contract"]["draft"]
    failure_governance = groups["failure_governance"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    holdout_window_source = _required_draft_value(window_contract, "holdout_window_source")
    reuse_rule = _required_draft_value(window_contract, "reuse_rule")
    drift_scope = _required_draft_value(window_contract, "drift_scope")
    backtest_contract_source = _required_draft_value(reuse_contract, "backtest_contract_source")
    test_contract_source = _required_draft_value(reuse_contract, "test_contract_source")
    variant_reuse_rule = _required_draft_value(reuse_contract, "variant_reuse_rule")
    no_reestimate_rule = _required_draft_value(reuse_contract, "no_reestimate_rule")
    direction_flip_rule = _required_draft_value(stability_contract, "direction_flip_rule")
    coverage_rule = _required_draft_value(stability_contract, "coverage_rule")
    regime_shift_rule = _required_draft_value(stability_contract, "regime_shift_rule")
    retryable_conditions = _string_list(failure_governance.get("retryable_conditions", []))
    child_lineage_trigger = _required_draft_value(failure_governance, "child_lineage_trigger")
    rollback_boundary = _required_draft_value(failure_governance, "rollback_boundary")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    field_doc_rule = _required_draft_value(delivery_contract, "field_doc_rule")

    time_split = {}
    time_split_path = mandate_formal_dir / "time_split.json"
    if time_split_path.exists():
        time_split = json.loads(time_split_path.read_text(encoding="utf-8"))

    (stage_formal_dir / "csf_holdout_run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_holdout_validation",
                "lineage_id": lineage_root.name,
                "holdout_window_source": holdout_window_source,
                "time_split": time_split,
                "reuse_rule": reuse_rule,
                "backtest_contract_source": backtest_contract_source,
                "test_contract_source": test_contract_source,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "holdout_factor_diagnostics.parquet",
        "holdout_test_compare.parquet",
        "holdout_portfolio_compare.parquet",
    ]:
        (stage_formal_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    for name in ["rolling_holdout_stability.json", "regime_shift_audit.json"]:
        (stage_formal_dir / name).write_text("{}\n", encoding="utf-8")
    (stage_formal_dir / "csf_holdout_gate_decision.md").write_text(
        "\n".join(
            [
                "# CSF Holdout Gate Decision",
                "",
                "- 在 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- Holdout 窗口来源: {holdout_window_source}",
                f"- 复用规则: {reuse_rule}",
                f"- 漂移审计范围: {drift_scope}",
                f"- Variant 复用规则: {variant_reuse_rule}",
                f"- 禁止重估规则: {no_reestimate_rule}",
                f"- 方向翻转规则: {direction_flip_rule}",
                f"- 覆盖率规则: {coverage_rule}",
                f"- Regime shift 规则: {regime_shift_rule}",
                f"- 可重试条件: {retryable_conditions}",
                f"- CHILD LINEAGE 触发条件: {child_lineage_trigger}",
                f"- 回滚边界: {rollback_boundary}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 字段文档规则: {field_doc_rule}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- csf_holdout_run_manifest.json",
                "- holdout_factor_diagnostics.parquet",
                "- holdout_test_compare.parquet",
                "- holdout_portfolio_compare.parquet",
                "- rolling_holdout_stability.json",
                "- regime_shift_audit.json",
                "- csf_holdout_gate_decision.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `holdout_window_source`: holdout 窗口来源，当前为 {holdout_window_source}。",
                f"- `retryable_conditions`: 可重试条件集合，当前为 {retryable_conditions}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(stage_dir)["author_draft_dir"] / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [
        name for name in CSF_HOLDOUT_VALIDATION_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing:
        raise ValueError(
            f"csf_holdout_validation draft groups must be confirmed before build: {', '.join(missing)}"
        )
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_holdout_validation draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
