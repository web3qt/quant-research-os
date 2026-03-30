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
            },
        },
    )
    for name in [
        "train_factor_quality.parquet",
        "train_bucket_diagnostics.parquet",
        "train_neutralization_diagnostics.parquet",
    ]:
        (stage_dir / name).write_text("placeholder parquet payload\n", encoding="utf-8")
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
                f"- Winsorize policy: {winsorize_policy}",
                f"- Standardize policy: {standardize_policy}",
                f"- Missing fill policy: {missing_fill_policy}",
                f"- Coverage floor rule: {coverage_floor_rule}",
                f"- Neutralization policy: {neutralization_policy}",
                f"- Beta estimation window: {beta_estimation_window}",
                f"- Group taxonomy reference: {group_taxonomy_reference}",
                f"- Residualization formula: {residualization_formula}",
                f"- Ranking scope: {ranking_scope}",
                f"- Bucket schema: {bucket_schema}",
                f"- Quantile count: {quantile_count}",
                f"- Min names per bucket: {min_names_per_bucket}",
                f"- Rebalance frequency: {rebalance_frequency}",
                f"- Signal lag rule: {signal_lag_rule}",
                f"- Holding period rule: {holding_period_rule}",
                f"- Overlap policy: {overlap_policy}",
                f"- Consumer stage: {consumer_stage}",
                f"- Reuse constraints: {reuse_constraints}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# Artifact Catalog",
                "",
                "- csf_train_freeze.yaml",
                "- train_factor_quality.parquet",
                "- train_variant_ledger.csv",
                "- train_variant_rejects.csv",
                "- train_bucket_diagnostics.parquet",
                "- train_neutralization_diagnostics.parquet",
                "- csf_train_contract.md",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# Field Dictionary",
                "",
                f"- `candidate_variant_ids`: {candidate_variant_ids}",
                f"- `kept_variant_ids`: {kept_variant_ids}",
                f"- `rejected_variant_ids`: {rejected_variant_ids}",
                f"- `selection_rule`: {selection_rule}",
                f"- `machine_artifacts`: {machine_artifacts}",
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
