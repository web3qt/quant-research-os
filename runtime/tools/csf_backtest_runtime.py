from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


CSF_BACKTEST_READY_DRAFT_FILE = "csf_backtest_ready_draft.yaml"
CSF_BACKTEST_READY_GROUP_ORDER = [
    "portfolio_contract",
    "execution_contract",
    "risk_contract",
    "diagnostic_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_backtest_ready_draft() -> dict[str, Any]:
    return {
        "groups": {
            "portfolio_contract": {
                "confirmed": False,
                "draft": {
                    "portfolio_expression": "",
                    "selection_rule": "",
                    "weight_mapping_rule": "",
                    "gross_exposure_rule": "",
                },
                "missing_items": [],
            },
            "execution_contract": {
                "confirmed": False,
                "draft": {
                    "rebalance_execution_lag": "",
                    "turnover_budget_rule": "",
                    "cost_model": "",
                    "capacity_model": "",
                },
                "missing_items": [],
            },
            "risk_contract": {
                "confirmed": False,
                "draft": {
                    "max_name_weight_rule": "",
                    "net_exposure_rule": "",
                    "group_neutral_overlay": "",
                    "target_strategy_reference": "",
                },
                "missing_items": [],
            },
            "diagnostic_contract": {
                "confirmed": False,
                "draft": {
                    "required_diagnostics": [],
                    "after_cost_rule": "",
                    "name_level_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_config_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_backtest_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "06_csf_backtest_ready"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / CSF_BACKTEST_READY_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_backtest_ready_draft())
    return stage_dir


def build_csf_backtest_ready_from_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "05_csf_test_evidence"
    stage_dir = scaffold_csf_backtest_ready(lineage_root)
    upstream_formal_dir = ensure_stage_author_layout(upstream_dir)["author_formal_dir"]
    stage_formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]

    missing = [
        name
        for name in [
            "rank_ic_timeseries.parquet",
            "rank_ic_summary.json",
            "bucket_returns.parquet",
            "monotonicity_report.json",
            "breadth_coverage_report.parquet",
            "subperiod_stability_report.json",
            "filter_condition_panel.parquet",
            "target_strategy_condition_compare.parquet",
            "gated_vs_ungated_summary.json",
            "csf_test_gate_table.csv",
            "csf_selected_variants_test.csv",
            "csf_test_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(
            f"csf_test_evidence artifacts missing before csf_backtest_ready build: {', '.join(missing)}"
        )

    groups = _require_confirmed_freeze_groups(stage_dir)
    portfolio_contract = groups["portfolio_contract"]["draft"]
    execution_contract = groups["execution_contract"]["draft"]
    risk_contract = groups["risk_contract"]["draft"]
    diagnostic_contract = groups["diagnostic_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    portfolio_expression = _required_draft_value(portfolio_contract, "portfolio_expression")
    selection_rule = _required_draft_value(portfolio_contract, "selection_rule")
    weight_mapping_rule = _required_draft_value(portfolio_contract, "weight_mapping_rule")
    gross_exposure_rule = _required_draft_value(portfolio_contract, "gross_exposure_rule")
    rebalance_execution_lag = _required_draft_value(execution_contract, "rebalance_execution_lag")
    turnover_budget_rule = _required_draft_value(execution_contract, "turnover_budget_rule")
    cost_model = _required_draft_value(execution_contract, "cost_model")
    capacity_model = _required_draft_value(execution_contract, "capacity_model")
    max_name_weight_rule = _required_draft_value(risk_contract, "max_name_weight_rule")
    net_exposure_rule = _required_draft_value(risk_contract, "net_exposure_rule")
    group_neutral_overlay = _required_draft_value(risk_contract, "group_neutral_overlay")
    target_strategy_reference = str(risk_contract.get("target_strategy_reference", "")).strip()
    required_diagnostics = _string_list(diagnostic_contract.get("required_diagnostics", []))
    after_cost_rule = _required_draft_value(diagnostic_contract, "after_cost_rule")
    name_level_rule = _required_draft_value(diagnostic_contract, "name_level_rule")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_config_note = _required_draft_value(delivery_contract, "frozen_config_note")

    _dump_yaml(
        stage_formal_dir / "portfolio_contract.yaml",
        {
            "portfolio_expression": portfolio_expression,
            "selection_rule": selection_rule,
            "weight_mapping_rule": weight_mapping_rule,
            "gross_exposure_rule": gross_exposure_rule,
            "rebalance_execution_lag": rebalance_execution_lag,
            "turnover_budget_rule": turnover_budget_rule,
            "cost_model": cost_model,
            "capacity_model": capacity_model,
            "max_name_weight_rule": max_name_weight_rule,
            "net_exposure_rule": net_exposure_rule,
            "group_neutral_overlay": group_neutral_overlay,
            "target_strategy_reference": target_strategy_reference,
            "required_diagnostics": required_diagnostics,
        },
    )
    for name in [
        "portfolio_weight_panel.parquet",
        "turnover_capacity_report.parquet",
        "portfolio_summary.parquet",
        "name_level_metrics.parquet",
        "target_strategy_compare.parquet",
    ]:
        (stage_formal_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    with (stage_formal_dir / "rebalance_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["portfolio_expression", "selection_rule", "weight_mapping_rule"])
        writer.writerow([portfolio_expression, selection_rule, weight_mapping_rule])
    (stage_formal_dir / "cost_assumption_report.md").write_text(
        f"# 成本假设报告\n\n- 成本模型: {cost_model}\n- 容量模型: {capacity_model}\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "drawdown_report.json").write_text("{}\n", encoding="utf-8")
    with (stage_formal_dir / "csf_backtest_gate_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["portfolio_expression", "after_cost_rule", "name_level_rule"])
        writer.writerow([portfolio_expression, after_cost_rule, name_level_rule])
    (stage_formal_dir / "csf_backtest_contract.md").write_text(
        "\n".join(
            [
                "# CSF Backtest Contract",
                "",
                f"- 组合表达: {portfolio_expression}",
                f"- 选择规则: {selection_rule}",
                f"- 权重映射规则: {weight_mapping_rule}",
                f"- 总敞口规则: {gross_exposure_rule}",
                f"- 再平衡执行滞后: {rebalance_execution_lag}",
                f"- 换手预算规则: {turnover_budget_rule}",
                f"- 成本模型: {cost_model}",
                f"- 容量模型: {capacity_model}",
                f"- 单名称最大权重规则: {max_name_weight_rule}",
                f"- 净敞口规则: {net_exposure_rule}",
                f"- group neutral overlay: {group_neutral_overlay}",
                f"- 目标策略引用: {target_strategy_reference}",
                f"- 必需诊断项: {required_diagnostics}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结配置说明: {frozen_config_note}",
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
                "- portfolio_contract.yaml",
                "- portfolio_weight_panel.parquet",
                "- rebalance_ledger.csv",
                "- turnover_capacity_report.parquet",
                "- cost_assumption_report.md",
                "- portfolio_summary.parquet",
                "- name_level_metrics.parquet",
                "- drawdown_report.json",
                "- target_strategy_compare.parquet",
                "- csf_backtest_gate_table.csv",
                "- csf_backtest_contract.md",
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
                f"- `portfolio_expression`: 组合表达，当前为 {portfolio_expression}。",
                f"- `required_diagnostics`: 必需诊断项集合，当前为 {required_diagnostics}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(stage_dir)["author_draft_dir"] / CSF_BACKTEST_READY_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_BACKTEST_READY_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_backtest_ready draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_backtest_ready draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
