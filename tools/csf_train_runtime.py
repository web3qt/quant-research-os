from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml


CSF_TRAIN_FREEZE_DRAFT_FILE = "csf_train_freeze_draft.yaml"
CSF_TRAIN_FREEZE_GROUP_ORDER = [
    "preprocess_contract",
    "neutralization_contract",
    "ranking_bucket_contract",
    "rebalance_contract",
    "search_governance_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_train_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "preprocess_contract": {
                "confirmed": False,
                "draft": {
                    "winsorize_policy": "",
                    "standardize_policy": "",
                    "missing_fill_policy": "",
                    "coverage_floor_rule": "",
                },
                "missing_items": [],
            },
            "neutralization_contract": {
                "confirmed": False,
                "draft": {
                    "neutralization_policy": "",
                    "beta_estimation_window": "",
                    "group_taxonomy_reference": "",
                    "residualization_formula": "",
                },
                "missing_items": [],
            },
            "ranking_bucket_contract": {
                "confirmed": False,
                "draft": {
                    "ranking_scope": "",
                    "bucket_schema": "",
                    "quantile_count": "",
                    "min_names_per_bucket": "",
                },
                "missing_items": [],
            },
            "rebalance_contract": {
                "confirmed": False,
                "draft": {
                    "rebalance_frequency": "",
                    "signal_lag_rule": "",
                    "holding_period_rule": "",
                    "overlap_policy": "",
                },
                "missing_items": [],
            },
            "search_governance_contract": {
                "confirmed": False,
                "draft": {
                    "candidate_variant_ids": [],
                    "kept_variant_ids": [],
                    "rejected_variant_ids": [],
                    "selection_rule": "",
                    "frozen_signal_contract_reference": "",
                    "train_governable_axes": [],
                    "non_governable_axes_after_signal": [],
                    "non_governable_axis_reject_rule": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "reuse_constraints": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "04_csf_train_freeze"
    stage_dir.mkdir(parents=True, exist_ok=True)
    draft_path = stage_dir / CSF_TRAIN_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_train_freeze_draft())
    return stage_dir


def build_csf_train_freeze_from_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "03_csf_signal_ready"
    stage_dir = scaffold_csf_train_freeze(lineage_root)

    missing = [
        name
        for name in [
            "factor_panel.parquet",
            "factor_manifest.yaml",
            "component_factor_manifest.yaml",
            "factor_coverage_report.parquet",
            "factor_group_context.parquet",
            "factor_contract.md",
            "factor_field_dictionary.md",
            "csf_signal_ready_gate_decision.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (upstream_dir / name).exists()
    ]
    if missing:
        raise ValueError(
            f"csf_signal_ready artifacts missing before csf_train_freeze build: {', '.join(missing)}"
        )

    groups = _require_confirmed_freeze_groups(stage_dir)
    preprocess_contract = groups["preprocess_contract"]["draft"]
    neutralization_contract = groups["neutralization_contract"]["draft"]
    ranking_bucket_contract = groups["ranking_bucket_contract"]["draft"]
    rebalance_contract = groups["rebalance_contract"]["draft"]
    search_governance_contract = groups["search_governance_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    winsorize_policy = _required_draft_value(preprocess_contract, "winsorize_policy")
    standardize_policy = _required_draft_value(preprocess_contract, "standardize_policy")
    missing_fill_policy = _required_draft_value(preprocess_contract, "missing_fill_policy")
    coverage_floor_rule = _required_draft_value(preprocess_contract, "coverage_floor_rule")
    neutralization_policy = _required_draft_value(neutralization_contract, "neutralization_policy")
    beta_estimation_window = _required_draft_value(neutralization_contract, "beta_estimation_window")
    group_taxonomy_reference = _required_draft_value(neutralization_contract, "group_taxonomy_reference")
    residualization_formula = _required_draft_value(neutralization_contract, "residualization_formula")
    ranking_scope = _required_draft_value(ranking_bucket_contract, "ranking_scope")
    bucket_schema = _required_draft_value(ranking_bucket_contract, "bucket_schema")
    quantile_count = _required_draft_value(ranking_bucket_contract, "quantile_count")
    min_names_per_bucket = _required_draft_value(ranking_bucket_contract, "min_names_per_bucket")
    rebalance_frequency = _required_draft_value(rebalance_contract, "rebalance_frequency")
    signal_lag_rule = _required_draft_value(rebalance_contract, "signal_lag_rule")
    holding_period_rule = _required_draft_value(rebalance_contract, "holding_period_rule")
    overlap_policy = _required_draft_value(rebalance_contract, "overlap_policy")
    candidate_variant_ids = _string_list(search_governance_contract.get("candidate_variant_ids", []))
    kept_variant_ids = _string_list(search_governance_contract.get("kept_variant_ids", []))
    rejected_variant_ids = _string_list(search_governance_contract.get("rejected_variant_ids", []))
    selection_rule = _required_draft_value(search_governance_contract, "selection_rule")
    frozen_signal_contract_reference = _required_draft_value(
        search_governance_contract, "frozen_signal_contract_reference"
    )
    train_governable_axes = _string_list(search_governance_contract.get("train_governable_axes", []))
    non_governable_axes_after_signal = _string_list(
        search_governance_contract.get("non_governable_axes_after_signal", [])
    )
    non_governable_axis_reject_rule = _required_draft_value(
        search_governance_contract, "non_governable_axis_reject_rule"
    )
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    reuse_constraints = _required_draft_value(delivery_contract, "reuse_constraints")

    _dump_yaml(
        stage_dir / "csf_train_freeze.yaml",
        {
            "preprocess_contract": {
                "winsorize_policy": winsorize_policy,
                "standardize_policy": standardize_policy,
                "missing_fill_policy": missing_fill_policy,
                "coverage_floor_rule": coverage_floor_rule,
            },
            "neutralization_contract": {
                "neutralization_policy": neutralization_policy,
                "beta_estimation_window": beta_estimation_window,
                "group_taxonomy_reference": group_taxonomy_reference,
                "residualization_formula": residualization_formula,
            },
            "ranking_bucket_contract": {
                "ranking_scope": ranking_scope,
                "bucket_schema": bucket_schema,
                "quantile_count": quantile_count,
                "min_names_per_bucket": min_names_per_bucket,
            },
            "rebalance_contract": {
                "rebalance_frequency": rebalance_frequency,
                "signal_lag_rule": signal_lag_rule,
                "holding_period_rule": holding_period_rule,
                "overlap_policy": overlap_policy,
            },
            "search_governance_contract": {
                "candidate_variant_ids": candidate_variant_ids,
                "kept_variant_ids": kept_variant_ids,
                "rejected_variant_ids": rejected_variant_ids,
                "selection_rule": selection_rule,
                "frozen_signal_contract_reference": frozen_signal_contract_reference,
                "train_governable_axes": train_governable_axes,
                "non_governable_axes_after_signal": non_governable_axes_after_signal,
                "non_governable_axis_reject_rule": non_governable_axis_reject_rule,
            },
        },
    )
    for name in [
        "train_factor_quality.parquet",
        "train_bucket_diagnostics.parquet",
        "train_neutralization_diagnostics.parquet",
    ]:
        (stage_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    with (stage_dir / "train_variant_ledger.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "status", "selection_rule"])
        for variant_id in candidate_variant_ids:
            status = "kept" if variant_id in kept_variant_ids else "rejected"
            writer.writerow([variant_id, status, selection_rule])
    with (stage_dir / "train_variant_rejects.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "reject_reason"])
        for variant_id in rejected_variant_ids:
            writer.writerow([variant_id, selection_rule])
    (stage_dir / "csf_train_contract.md").write_text(
        "\n".join(
            [
                "# CSF Train Contract",
                "",
                f"- Winsorize 策略: {winsorize_policy}",
                f"- Standardize 策略: {standardize_policy}",
                f"- 缺失填补策略: {missing_fill_policy}",
                f"- 覆盖率下限规则: {coverage_floor_rule}",
                f"- 中性化策略: {neutralization_policy}",
                f"- Beta 估计窗口: {beta_estimation_window}",
                f"- 分组体系引用: {group_taxonomy_reference}",
                f"- 残差化公式: {residualization_formula}",
                f"- 排名范围: {ranking_scope}",
                f"- 分桶 schema: {bucket_schema}",
                f"- 分位数数量: {quantile_count}",
                f"- 每桶最少名称数: {min_names_per_bucket}",
                f"- 再平衡频率: {rebalance_frequency}",
                f"- 信号滞后规则: {signal_lag_rule}",
                f"- 持有期规则: {holding_period_rule}",
                f"- 重叠策略: {overlap_policy}",
                f"- Frozen signal contract reference: {frozen_signal_contract_reference}",
                f"- Train-governable axes: {', '.join(train_governable_axes)}",
                f"- Non-governable axes after signal: {', '.join(non_governable_axes_after_signal)}",
                f"- Non-governable-axis reject rule: {non_governable_axis_reject_rule}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 复用约束: {reuse_constraints}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- csf_train_freeze.yaml",
                "- train_factor_quality.parquet",
                "- train_variant_ledger.csv",
                "- train_variant_rejects.csv",
                "- train_bucket_diagnostics.parquet",
                "- train_neutralization_diagnostics.parquet",
                "- csf_train_contract.md",
                "- field_dictionary.md",
                "- frozen signal axes are explicitly excluded from train governance",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `candidate_variant_ids`: 候选 variant ID 集合，当前为 {candidate_variant_ids}。",
                f"- `kept_variant_ids`: 保留的 variant ID 集合，当前为 {kept_variant_ids}。",
                f"- `rejected_variant_ids`: 拒绝的 variant ID 集合，当前为 {rejected_variant_ids}。",
                f"- `selection_rule`: 选择规则，当前为 {selection_rule}。",
                f"- `frozen_signal_contract_reference`: 上游 signal contract 引用，当前为 {frozen_signal_contract_reference}。",
                f"- `train_governable_axes`: signal_ready 之后仍允许在 train 调整的轴，当前为 {train_governable_axes}。",
                f"- `non_governable_axes_after_signal`: 改动后必须重开 csf_signal_ready 的轴，当前为 {non_governable_axes_after_signal}。",
                f"- `non_governable_axis_reject_rule`: 这些轴的拒绝规则，当前为 {non_governable_axis_reject_rule}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((stage_dir / CSF_TRAIN_FREEZE_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_TRAIN_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_train_freeze draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_train_freeze draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
