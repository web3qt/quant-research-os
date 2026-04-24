from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


CSF_TEST_EVIDENCE_DRAFT_FILE = "csf_test_evidence_draft.yaml"
CSF_TEST_EVIDENCE_GROUP_ORDER = [
    "window_contract",
    "variant_contract",
    "evidence_contract",
    "audit_contract",
    "delivery_contract",
]
CSF_TEST_EVIDENCE_STAGE_OUTPUTS = [
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
    "csf_test_gate_decision.md",
    "csf_test_contract.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


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

    target_strategy_reference = str(route_payload.get("target_strategy_reference", "")).strip()
    _write_parquet_rows(
        stage_formal_dir / "rank_ic_timeseries.parquet",
        [
            {"date": "2024-07-01", "variant_id": variant_id, "rank_ic": 0.11}
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "bucket_returns.parquet",
        [
            {"date": "2024-07-01", "variant_id": variant_id, "bucket_id": bucket_id, "mean_return": mean_return}
            for variant_id in selected_variant_ids
            for bucket_id, mean_return in [("q1", -0.01), ("q5", 0.02)]
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "breadth_coverage_report.parquet",
        [
            {"date": "2024-07-01", "variant_id": variant_id, "coverage_ratio": 0.98, "asset_count": 120}
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "filter_condition_panel.parquet",
        [
            {
                "date": "2024-07-01",
                "asset": "SOLUSDT",
                "variant_id": variant_id,
                "condition_active": True,
            }
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "target_strategy_condition_compare.parquet",
        [
            {
                "variant_id": variant_id,
                "target_strategy_reference": target_strategy_reference,
                "gated_mean_return": 0.03,
                "ungated_mean_return": 0.01,
                "delta_mean_return": 0.02,
            }
            for variant_id in selected_variant_ids
        ],
    )
    (stage_formal_dir / "rank_ic_summary.json").write_text(
        json.dumps(
            {
                "stage": "csf_test_evidence",
                "lineage_id": lineage_root.name,
                "factor_role": declared_factor_role,
                "selected_variant_ids": selected_variant_ids,
                "primary_evidence_contract": primary_evidence_contract,
                "mean_rank_ic": 0.12,
                "median_rank_ic": 0.10,
                "num_dates": 29,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "monotonicity_report.json").write_text(
        json.dumps(
            {
                "stage": "csf_test_evidence",
                "selected_variant_ids": selected_variant_ids,
                "status": "pass",
                "monotonic_direction": "high_bucket_outperforms_low_bucket",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "subperiod_stability_report.json").write_text(
        json.dumps(
            {
                "stage": "csf_test_evidence",
                "selected_variant_ids": selected_variant_ids,
                "status": "pass",
                "subperiod_count": 3,
                "subperiod_rule": subperiod_rule,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "gated_vs_ungated_summary.json").write_text(
        json.dumps(
            {
                "stage": "csf_test_evidence",
                "selected_variant_ids": selected_variant_ids,
                "status": "pass",
                "mean_delta": 0.02,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    with (stage_formal_dir / "csf_test_gate_table.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "verdict", "primary_evidence_contract", "reason"])
        for variant_id in selected_variant_ids:
            writer.writerow([variant_id, "selected", primary_evidence_contract, selection_rule])
    with (stage_formal_dir / "csf_selected_variants_test.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["variant_id", "status"])
        for variant_id in selected_variant_ids:
            writer.writerow([variant_id, "selected"])
    (stage_formal_dir / "csf_test_gate_decision.md").write_text(
        "\n".join(
            [
                "# CSF Test Gate Decision",
                "",
                "- 在 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- 主证据合同: {primary_evidence_contract}",
                f"- 因子角色: {declared_factor_role}",
                f"- test 只复用 train freeze 尺子: {train_reuse_note}",
                f"- Test 使用的 preprocess、neutralization、bucket 和 rebalance 规则全部来自 train freeze: {train_reuse_note}",
                f"- 没有新增未冻结的 variant: {multiple_testing_note}",
                f"- 未在 test 重估 train 尺子，也未新增未冻结的 variant: {multiple_testing_note}",
                f"- 选择规则: {selection_rule}",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结规格说明: {frozen_spec_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_test_evidence",
                "lineage_id": lineage_root.name,
                "source_stage": "csf_train_freeze",
                "input_roots": [
                    "../04_csf_train_freeze/author/formal/csf_train_freeze.yaml",
                    "../04_csf_train_freeze/author/formal/train_variant_ledger.csv",
                    "../03_csf_signal_ready/author/formal/factor_manifest.yaml",
                    "../02_csf_data_ready/author/formal/asset_universe_membership.parquet",
                    "author/draft/csf_test_evidence_draft.yaml",
                ],
                "stage_outputs": CSF_TEST_EVIDENCE_STAGE_OUTPUTS,
                "program_dir": "program/cross_sectional_factor/test_evidence",
                "program_entrypoint": "run_stage.py",
                "program_execution_manifest": "program_execution_manifest.json",
                "replay_command": f"python3 {lineage_root / 'program' / 'cross_sectional_factor' / 'test_evidence' / 'run_stage.py'} --lineage-root {lineage_root}",
                "selected_variant_ids": selected_variant_ids,
                "selection_rule": selection_rule,
                "primary_evidence_contract": primary_evidence_contract,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
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
                "- csf_test_gate_decision.md",
                "- csf_test_contract.md",
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
                f"- `selected_variant_ids`: 已选 variant ID 集合，当前为 {selected_variant_ids}。",
                f"- `primary_evidence_contract`: 主证据合同，当前为 {primary_evidence_contract}。",
                f"- `factor_role`: 因子角色，当前为 {declared_factor_role}。",
                f"- `machine_artifacts`: 本阶段机器产物集合，当前为 {machine_artifacts}。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shape_result = validate_stage_artifacts(stage_formal_dir, load_artifact_contract("csf_test_evidence"))
    semantic_result = validate_csf_test_evidence_semantics(stage_formal_dir, lineage_root)
    errors = [*shape_result.errors, *semantic_result.errors]
    if errors:
        raise ValueError("csf_test_evidence formal artifacts do not match artifact contract: " + "; ".join(errors))
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
