from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


CSF_SIGNAL_READY_FREEZE_DRAFT_FILE = "csf_signal_ready_freeze_draft.yaml"
CSF_SIGNAL_READY_FREEZE_GROUP_ORDER = [
    "factor_identity",
    "panel_contract",
    "factor_expression",
    "context_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_signal_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "factor_identity": {
                "confirmed": False,
                "draft": {
                    "factor_id": "",
                    "factor_version": "",
                    "factor_direction": "",
                    "factor_structure": "",
                },
                "missing_items": [],
            },
            "panel_contract": {
                "confirmed": False,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "as_of_semantics": "",
                    "coverage_contract": "",
                },
                "missing_items": [],
            },
            "factor_expression": {
                "confirmed": False,
                "draft": {
                    "raw_factor_fields": [],
                    "derived_factor_fields": [],
                    "final_score_field": "",
                    "missing_value_policy": "",
                },
                "missing_items": [],
            },
            "context_contract": {
                "confirmed": False,
                "draft": {
                    "group_context_fields": [],
                    "component_factor_ids": [],
                    "score_combination_formula": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_signal_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "03_csf_signal_ready"
    stage_dir.mkdir(parents=True, exist_ok=True)
    draft_path = stage_dir / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_signal_ready_freeze_draft())
    return stage_dir


def build_csf_signal_ready_from_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "02_csf_data_ready"
    stage_dir = scaffold_csf_signal_ready(lineage_root)

    missing = [
        name
        for name in [
            "panel_manifest.json",
            "asset_universe_membership.parquet",
            "cross_section_coverage.parquet",
            "eligibility_base_mask.parquet",
            "csf_data_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (upstream_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"csf_data_ready artifacts missing before csf_signal_ready build: {', '.join(missing)}")

    groups = _require_confirmed_freeze_groups(stage_dir)
    factor_identity = groups["factor_identity"]["draft"]
    panel_contract = groups["panel_contract"]["draft"]
    factor_expression = groups["factor_expression"]["draft"]
    context_contract = groups["context_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    factor_id = _required_draft_value(factor_identity, "factor_id")
    factor_version = _required_draft_value(factor_identity, "factor_version")
    factor_direction = _required_draft_value(factor_identity, "factor_direction")
    factor_structure = _required_draft_value(factor_identity, "factor_structure")
    panel_primary_key = _string_list(panel_contract.get("panel_primary_key", []))
    as_of_semantics = _required_draft_value(panel_contract, "as_of_semantics")
    coverage_contract = _required_draft_value(panel_contract, "coverage_contract")
    raw_factor_fields = _string_list(factor_expression.get("raw_factor_fields", []))
    derived_factor_fields = _string_list(factor_expression.get("derived_factor_fields", []))
    final_score_field = _required_draft_value(factor_expression, "final_score_field")
    missing_value_policy = _required_draft_value(factor_expression, "missing_value_policy")
    group_context_fields = _string_list(context_contract.get("group_context_fields", []))
    component_factor_ids = _string_list(context_contract.get("component_factor_ids", []))
    score_combination_formula = _required_draft_value(context_contract, "score_combination_formula")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_inputs_note = _required_draft_value(delivery_contract, "frozen_inputs_note")

    (stage_dir / "factor_panel.parquet").write_text("占位 factor panel 载荷\n", encoding="utf-8")
    _dump_yaml(
        stage_dir / "factor_manifest.yaml",
        {
            "factor_id": factor_id,
            "factor_version": factor_version,
            "factor_direction": factor_direction,
            "factor_structure": factor_structure,
            "panel_primary_key": panel_primary_key,
            "raw_factor_fields": raw_factor_fields,
            "derived_factor_fields": derived_factor_fields,
            "final_score_field": final_score_field,
        },
    )
    _dump_yaml(
        stage_dir / "component_factor_manifest.yaml",
        {
            "component_factor_ids": component_factor_ids,
            "score_combination_formula": score_combination_formula,
        },
    )
    for name in ["factor_coverage_report.parquet", "factor_group_context.parquet"]:
        (stage_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    (stage_dir / "factor_contract.md").write_text(
        "\n".join(
            [
                "# 因子合同",
                "",
                f"- 因子 ID: {factor_id}",
                f"- 因子版本: {factor_version}",
                f"- 因子方向: {factor_direction}",
                f"- 因子结构: {factor_structure}",
                f"- As-of 语义: {as_of_semantics}",
                f"- 覆盖合同: {coverage_contract}",
                f"- 缺失值策略: {missing_value_policy}",
                f"- 分数组合公式: {score_combination_formula}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结输入说明: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "factor_field_dictionary.md").write_text(
        "\n".join(
            [
                "# 因子字段字典",
                "",
                f"- `raw_factor_fields`: 原始因子字段集合，当前为 {raw_factor_fields}。",
                f"- `derived_factor_fields`: 派生因子字段集合，当前为 {derived_factor_fields}。",
                f"- `final_score_field`: 最终得分字段，当前为 {final_score_field}。",
                f"- `group_context_fields`: 分组上下文字段，当前为 {group_context_fields}。",
                f"- `component_factor_ids`: 组件因子 ID 集合，当前为 {component_factor_ids}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "csf_signal_ready_gate_decision.md").write_text(
        "\n".join(
            [
                "# CSF Signal Ready Gate Decision",
                "",
                "- 在 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- 下游消费阶段: {consumer_stage}",
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
                "- factor_panel.parquet",
                "- factor_manifest.yaml",
                "- component_factor_manifest.yaml",
                "- factor_coverage_report.parquet",
                "- factor_group_context.parquet",
                "- factor_contract.md",
                "- factor_field_dictionary.md",
                "- csf_signal_ready_gate_decision.md",
                "- field_dictionary.md",
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
                f"- `factor_id`: 因子 ID，当前为 {factor_id}。",
                f"- `factor_version`: 因子版本，当前为 {factor_version}。",
                f"- `factor_direction`: 因子方向，当前为 {factor_direction}。",
                f"- `factor_structure`: 因子结构，当前为 {factor_structure}。",
                f"- `panel_primary_key`: 面板主键，当前为 {panel_primary_key}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((stage_dir / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE).read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_SIGNAL_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_signal_ready draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_signal_ready draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
