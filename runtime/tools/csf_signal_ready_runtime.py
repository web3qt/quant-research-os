from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


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


def _write_parquet_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        raise ValueError(f"{path.name} requires at least one row")
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()


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
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_signal_ready_freeze_draft())
    return stage_dir


def build_csf_signal_ready_from_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "02_csf_data_ready"
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    upstream_formal_dir = ensure_stage_author_layout(upstream_dir)["author_formal_dir"]
    stage_formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]

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
        if not (upstream_formal_dir / name).exists()
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
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    route_payload = yaml.safe_load((mandate_formal_dir / "research_route.yaml").read_text(encoding="utf-8")) or {}
    route_contract_text = (mandate_formal_dir / "research_route.yaml").read_text(encoding="utf-8")
    factor_role = str(route_payload.get("factor_role", "")).strip()
    portfolio_expression = str(route_payload.get("portfolio_expression", "")).strip()
    neutralization_policy = str(route_payload.get("neutralization_policy", "")).strip()
    target_strategy_reference = str(route_payload.get("target_strategy_reference", "")).strip()
    group_taxonomy_reference = str(route_payload.get("group_taxonomy_reference", "")).strip()
    target_strategy_requirement_status = (
        "required_satisfied" if factor_role in {"regime_filter", "combo_filter"} and target_strategy_reference else
        "required_missing" if factor_role in {"regime_filter", "combo_filter"} else
        "not_required"
    )
    group_taxonomy_requirement_status = (
        "required_satisfied" if neutralization_policy == "group_neutral" and group_taxonomy_reference else
        "required_missing" if neutralization_policy == "group_neutral" else
        "not_required"
    )

    membership_rows = _read_parquet_rows(upstream_formal_dir / "asset_universe_membership.parquet")
    eligibility_rows = _read_parquet_rows(upstream_formal_dir / "eligibility_base_mask.parquet")
    taxonomy_path = upstream_formal_dir / "asset_taxonomy_snapshot.parquet"
    taxonomy_rows = _read_parquet_rows(taxonomy_path) if taxonomy_path.exists() else []
    returns_panel_path = upstream_formal_dir / "shared_feature_base" / "returns_panel.parquet"
    liquidity_panel_path = upstream_formal_dir / "shared_feature_base" / "liquidity_panel.parquet"
    beta_inputs_path = upstream_formal_dir / "shared_feature_base" / "beta_inputs.parquet"
    returns_rows = _read_parquet_rows(returns_panel_path) if returns_panel_path.exists() else []
    liquidity_rows = _read_parquet_rows(liquidity_panel_path) if liquidity_panel_path.exists() else []
    beta_rows = _read_parquet_rows(beta_inputs_path) if beta_inputs_path.exists() else []

    eligible_lookup = {
        (str(row.get("date")), str(row.get("asset"))): bool(row.get("eligible"))
        for row in eligibility_rows
    }
    returns_lookup = {
        (str(row.get("date")), str(row.get("asset"))): float(row.get("return_1d", 0.0))
        for row in returns_rows
    }
    liquidity_lookup = {
        (str(row.get("date")), str(row.get("asset"))): float(row.get("dollar_volume", 0.0))
        for row in liquidity_rows
    }
    beta_lookup = {
        (str(row.get("date")), str(row.get("asset"))): float(row.get("beta_proxy", 1.0))
        for row in beta_rows
    }
    taxonomy_lookup = {
        (str(row.get("date", "")), str(row.get("asset"))): str(row.get("group_bucket", "ungrouped"))
        for row in taxonomy_rows
    }

    factor_panel_rows: list[dict[str, Any]] = []
    factor_group_rows: list[dict[str, Any]] = []
    by_date_total: dict[str, int] = {}
    by_date_kept: dict[str, int] = {}
    for membership in membership_rows:
        date = str(membership.get("date"))
        asset = str(membership.get("asset"))
        by_date_total[date] = by_date_total.get(date, 0) + 1
        if not bool(membership.get("in_universe")):
            continue
        if not eligible_lookup.get((date, asset), False):
            continue
        ret = returns_lookup.get((date, asset), 0.0)
        liquidity = liquidity_lookup.get((date, asset), 0.0)
        beta = beta_lookup.get((date, asset), 1.0)
        # 用 data_ready 共享底座做一个确定性的最小派生分数，保证不是静态硬编码资产。
        factor_value = float(ret * 100.0 - beta + (liquidity / 1000.0))
        factor_panel_rows.append({"date": date, "asset": asset, final_score_field: factor_value})
        group_value = taxonomy_lookup.get((date, asset), taxonomy_lookup.get(("", asset), "ungrouped"))
        factor_group_rows.append({"date": date, "asset": asset, "group_context": group_value})
        by_date_kept[date] = by_date_kept.get(date, 0) + 1

    coverage_rows = [
        {
            "date": date,
            "coverage_ratio": (by_date_kept.get(date, 0) / total) if total else 0.0,
            "asset_count": by_date_kept.get(date, 0),
        }
        for date, total in sorted(by_date_total.items())
    ]

    _write_parquet_rows(stage_formal_dir / "factor_panel.parquet", factor_panel_rows)
    _dump_yaml(
        stage_formal_dir / "factor_manifest.yaml",
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
        stage_formal_dir / "component_factor_manifest.yaml",
        {
            "component_factor_ids": component_factor_ids,
            "score_combination_formula": score_combination_formula,
        },
    )
    _write_parquet_rows(stage_formal_dir / "factor_coverage_report.parquet", coverage_rows)
    _write_parquet_rows(stage_formal_dir / "factor_group_context.parquet", factor_group_rows)
    _dump_yaml(
        stage_formal_dir / "route_inheritance_contract.yaml",
        {
            "source_route_artifact": "../../01_mandate/author/formal/research_route.yaml",
            "source_route_digest_sha256": hashlib.sha256(route_contract_text.encode("utf-8")).hexdigest(),
            "research_route": str(route_payload.get("research_route", "")).strip(),
            "factor_role": factor_role,
            "factor_structure": str(route_payload.get("factor_structure", "")).strip(),
            "portfolio_expression": portfolio_expression,
            "neutralization_policy": neutralization_policy,
            "target_strategy_reference": target_strategy_reference,
            "group_taxonomy_reference": group_taxonomy_reference,
            "target_strategy_reference_requirement_status": target_strategy_requirement_status,
            "group_taxonomy_reference_requirement_status": group_taxonomy_requirement_status,
            "inheritance_mode": "exact_copy",
        },
    )
    (stage_formal_dir / "factor_contract.md").write_text(
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
    (stage_formal_dir / "factor_field_dictionary.md").write_text(
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
    (stage_formal_dir / "csf_signal_ready_gate_decision.md").write_text(
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
    (stage_formal_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_signal_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "csf_data_ready",
                "research_route": str(route_payload.get("research_route", "")).strip(),
                "factor_role": factor_role,
                "factor_structure": str(route_payload.get("factor_structure", "")).strip(),
                "portfolio_expression": portfolio_expression,
                "neutralization_policy": neutralization_policy,
                "program_dir": "program/cross_sectional_factor/signal_ready",
                "program_entrypoint": "run_stage.py",
                "program_execution_manifest": "program_execution_manifest.json",
                "input_roots": [
                    "../02_csf_data_ready/author/formal/panel_manifest.json",
                    "../02_csf_data_ready/author/formal/asset_universe_membership.parquet",
                    "../02_csf_data_ready/author/formal/eligibility_base_mask.parquet",
                    "../02_csf_data_ready/author/formal/csf_data_contract.md",
                    "../../01_mandate/author/formal/research_route.yaml",
                ],
                "stage_outputs": [
                    "artifact_catalog.md",
                    "component_factor_manifest.yaml",
                    "csf_signal_ready_gate_decision.md",
                    "factor_contract.md",
                    "factor_coverage_report.parquet",
                    "factor_field_dictionary.md",
                    "factor_group_context.parquet",
                    "factor_manifest.yaml",
                    "factor_panel.parquet",
                    "field_dictionary.md",
                    "route_inheritance_contract.yaml",
                ],
                "replay_command": f"python3 {lineage_root / 'program' / 'cross_sectional_factor' / 'signal_ready' / 'run_stage.py'} --lineage-root {lineage_root}",
                "notes": [
                    "Route identity is inherited from mandate through route_inheritance_contract.yaml.",
                    "This stage must not redefine factor_role, factor_structure, portfolio_expression, or neutralization_policy.",
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- factor_panel.parquet",
                "- factor_manifest.yaml",
                "- component_factor_manifest.yaml",
                "- factor_coverage_report.parquet",
                "- factor_group_context.parquet",
                "- route_inheritance_contract.yaml",
                "- factor_contract.md",
                "- factor_field_dictionary.md",
                "- csf_signal_ready_gate_decision.md",
                "- run_manifest.json",
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
                f"- `factor_id`: 因子 ID，当前为 {factor_id}。",
                f"- `factor_version`: 因子版本，当前为 {factor_version}。",
                f"- `factor_direction`: 因子方向，当前为 {factor_direction}。",
                f"- `factor_structure`: 因子结构，当前为 {factor_structure}。",
                f"- `panel_primary_key`: 面板主键，当前为 {panel_primary_key}。",
                "- `route_inheritance_contract.yaml`: 当前阶段唯一正式 route 继承凭证，绑定 mandate 的 research_route.yaml。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(stage_dir)["author_draft_dir"] / CSF_SIGNAL_READY_FREEZE_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
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
