from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


CSF_TEST_EVIDENCE_DRAFT_FILE = "csf_test_evidence_draft.yaml"
CSF_TEST_EVIDENCE_GROUP_ORDER = [
    "window_contract",
    "variant_contract",
    "evidence_contract",
    "audit_contract",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _blank_csf_test_evidence_draft() -> dict[str, Any]:
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
                    "factor_role": "",
                    "role_specific_note": "",
                },
                "missing_items": [],
            },
            "audit_contract": {
                "confirmed": False,
                "draft": {
                    "breadth_rule": "",
                    "flip_rule": "",
                    "coverage_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_spec_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_csf_test_evidence(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "05_csf_test_evidence"
    layout = ensure_stage_author_layout(stage_dir)
    draft_path = layout["author_draft_dir"] / CSF_TEST_EVIDENCE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_test_evidence_draft())
    return stage_dir


def build_csf_test_evidence_from_train_freeze(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    upstream_dir = lineage_root / "04_csf_train_freeze"
    mandate_dir = lineage_root / "01_mandate"
    stage_dir = scaffold_csf_test_evidence(lineage_root)
    upstream_formal_dir = ensure_stage_author_layout(upstream_dir)["author_formal_dir"]
    mandate_formal_dir = ensure_stage_author_layout(mandate_dir)["author_formal_dir"]
    stage_formal_dir = ensure_stage_author_layout(stage_dir)["author_formal_dir"]

    missing = [
        name
        for name in [
            "csf_train_freeze.yaml",
            "train_factor_quality.parquet",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
            "train_bucket_diagnostics.parquet",
            "train_neutralization_diagnostics.parquet",
            "csf_train_contract.md",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (upstream_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(
            f"csf_train_freeze artifacts missing before csf_test_evidence build: {', '.join(missing)}"
        )

    route_payload = yaml.safe_load((mandate_formal_dir / "research_route.yaml").read_text(encoding="utf-8")) or {}
    factor_role = str(route_payload.get("factor_role", "")).strip()

    groups = _require_confirmed_freeze_groups(stage_dir)
    window_contract = groups["window_contract"]["draft"]
    variant_contract = groups["variant_contract"]["draft"]
    evidence_contract = groups["evidence_contract"]["draft"]
    audit_contract = groups["audit_contract"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    test_window_source = _required_draft_value(window_contract, "test_window_source")
    train_reuse_note = _required_draft_value(window_contract, "train_reuse_note")
    subperiod_rule = _required_draft_value(window_contract, "subperiod_rule")
    selected_variant_ids = _string_list(variant_contract.get("selected_variant_ids", []))
    selection_rule = _required_draft_value(variant_contract, "selection_rule")
    multiple_testing_note = _required_draft_value(variant_contract, "multiple_testing_note")
    primary_evidence_contract = _required_draft_value(evidence_contract, "primary_evidence_contract")
    declared_factor_role = _required_draft_value(evidence_contract, "factor_role")
    role_specific_note = _required_draft_value(evidence_contract, "role_specific_note")
    breadth_rule = _required_draft_value(audit_contract, "breadth_rule")
    flip_rule = _required_draft_value(audit_contract, "flip_rule")
    coverage_note = _required_draft_value(audit_contract, "coverage_note")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_spec_note = _required_draft_value(delivery_contract, "frozen_spec_note")

    if factor_role and declared_factor_role and factor_role != declared_factor_role:
        raise ValueError("csf_test_evidence factor_role must match mandate research_route.yaml")

    for name in [
        "rank_ic_timeseries.parquet",
        "bucket_returns.parquet",
        "breadth_coverage_report.parquet",
        "filter_condition_panel.parquet",
        "target_strategy_condition_compare.parquet",
    ]:
        (stage_formal_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    (stage_formal_dir / "rank_ic_summary.json").write_text(
        json.dumps({"factor_role": declared_factor_role, "selected_variant_ids": selected_variant_ids}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "monotonicity_report.json",
        "subperiod_stability_report.json",
        "gated_vs_ungated_summary.json",
    ]:
        (stage_formal_dir / name).write_text("{}\n", encoding="utf-8")
    with (stage_formal_dir / "csf_test_gate_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "verdict", "primary_evidence_contract"])
        for variant_id in selected_variant_ids:
            writer.writerow([variant_id, "selected", primary_evidence_contract])
    with (stage_formal_dir / "csf_selected_variants_test.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "status"])
        for variant_id in selected_variant_ids:
            writer.writerow([variant_id, "selected"])
    (stage_formal_dir / "csf_test_contract.md").write_text(
        "\n".join(
            [
                "# CSF Test Contract",
                "",
                f"- Test 窗口来源: {test_window_source}",
                f"- Train 复用说明: {train_reuse_note}",
                f"- 子区间规则: {subperiod_rule}",
                f"- 选择规则: {selection_rule}",
                f"- 多重检验说明: {multiple_testing_note}",
                f"- 主证据合同: {primary_evidence_contract}",
                f"- 因子角色: {declared_factor_role}",
                f"- 角色特定说明: {role_specific_note}",
                f"- Breadth 规则: {breadth_rule}",
                f"- 翻转规则: {flip_rule}",
                f"- 覆盖说明: {coverage_note}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结规格说明: {frozen_spec_note}",
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
                "- rank_ic_timeseries.parquet",
                "- rank_ic_summary.json",
                "- bucket_returns.parquet",
                "- monotonicity_report.json",
                "- breadth_coverage_report.parquet",
                "- subperiod_stability_report.json",
                "- filter_condition_panel.parquet",
                "- target_strategy_condition_compare.parquet",
                "- gated_vs_ungated_summary.json",
                "- csf_test_gate_table.csv",
                "- csf_selected_variants_test.csv",
                "- csf_test_contract.md",
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
                f"- `selected_variant_ids`: 已选 variant ID 集合，当前为 {selected_variant_ids}。",
                f"- `primary_evidence_contract`: 主证据合同，当前为 {primary_evidence_contract}。",
                f"- `factor_role`: 因子角色，当前为 {declared_factor_role}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(stage_dir)["author_draft_dir"] / CSF_TEST_EVIDENCE_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_TEST_EVIDENCE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_test_evidence draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_test_evidence draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
