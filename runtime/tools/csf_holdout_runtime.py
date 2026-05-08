from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_holdout_validation_contract_runtime import validate_csf_holdout_validation_semantics
from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
from runtime.tools.stage_artifact_layout import ensure_stage_author_layout


CSF_HOLDOUT_VALIDATION_DRAFT_FILE = "csf_holdout_validation_draft.yaml"
CSF_HOLDOUT_VALIDATION_GROUP_ORDER = [
    "window_contract",
    "reuse_contract",
    "stability_contract",
    "failure_governance",
    "delivery_contract",
]
CSF_HOLDOUT_VALIDATION_STAGE_OUTPUTS = [
    "csf_holdout_run_manifest.json",
    "holdout_factor_diagnostics.parquet",
    "holdout_test_compare.parquet",
    "holdout_portfolio_compare.parquet",
    "rolling_holdout_stability.json",
    "regime_shift_audit.json",
    "csf_holdout_gate_decision.md",
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
            "csf_backtest_gate_decision.md",
            "run_manifest.json",
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

    upstream_run_manifest = _load_json(upstream_formal_dir / "run_manifest.json")
    selected_variant_ids = _string_list(upstream_run_manifest.get("selected_variant_ids", []))
    if not selected_variant_ids:
        selected_variant_ids = _read_backtest_variant_ids(upstream_formal_dir / "csf_backtest_gate_table.csv")
    if not selected_variant_ids:
        raise ValueError("csf_holdout_validation requires at least one backtest-selected variant")
    portfolio_expression = str(upstream_run_manifest.get("portfolio_expression", "")).strip()
    portfolio_summary = _read_parquet_rows(upstream_formal_dir / "portfolio_summary.parquet")
    backtest_summary_by_variant = {
        str(row.get("variant_id", "")).strip(): row
        for row in portfolio_summary
        if str(row.get("variant_id", "")).strip()
    }

    (stage_formal_dir / "csf_holdout_run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_holdout_validation",
                "lineage_id": lineage_root.name,
                "source_stage": "csf_backtest_ready",
                "holdout_window_source": holdout_window_source,
                "time_split": time_split,
                "reuse_rule": reuse_rule,
                "drift_scope": drift_scope,
                "backtest_contract_source": backtest_contract_source,
                "test_contract_source": test_contract_source,
                "variant_reuse_rule": variant_reuse_rule,
                "no_reestimate_rule": no_reestimate_rule,
                "direction_flip_rule": direction_flip_rule,
                "coverage_rule": coverage_rule,
                "regime_shift_rule": regime_shift_rule,
                "retryable_conditions": retryable_conditions,
                "child_lineage_trigger": child_lineage_trigger,
                "rollback_boundary": rollback_boundary,
                "input_roots": [
                    "../06_csf_backtest_ready/author/formal/portfolio_contract.yaml",
                    "../06_csf_backtest_ready/author/formal/portfolio_weight_panel.parquet",
                    "../06_csf_backtest_ready/author/formal/csf_backtest_gate_table.csv",
                    "../06_csf_backtest_ready/author/formal/run_manifest.json",
                    "author/draft/csf_holdout_validation_draft.yaml",
                ],
                "stage_outputs": CSF_HOLDOUT_VALIDATION_STAGE_OUTPUTS,
                "program_dir": "program/cross_sectional_factor/holdout_validation",
                "program_entrypoint": "run_stage.py",
                "program_execution_manifest": "program_execution_manifest.json",
                "replay_command": f"python3 {lineage_root / 'program' / 'cross_sectional_factor' / 'holdout_validation' / 'run_stage.py'} --lineage-root {lineage_root}",
                "selected_variant_ids": selected_variant_ids,
                "portfolio_expression": portfolio_expression,
                "delivery_contract": {
                    "machine_artifacts": machine_artifacts,
                    "consumer_stage": consumer_stage,
                    "field_doc_rule": field_doc_rule,
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_parquet_rows(
        stage_formal_dir / "holdout_factor_diagnostics.parquet",
        [
            {
                "date": "2024-10-01",
                "variant_id": variant_id,
                "coverage_ratio": 0.98,
                "breadth": 120,
                "direction_match": True,
                "bucket_stability_score": 0.75,
            }
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "holdout_test_compare.parquet",
        [
            {
                "variant_id": variant_id,
                "backtest_mean_net_return": float(backtest_summary_by_variant.get(variant_id, {}).get("mean_net_return", 0.012)),
                "holdout_mean_net_return": 0.01,
                "direction_match": True,
            }
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "holdout_portfolio_compare.parquet",
        [
            {
                "variant_id": variant_id,
                "backtest_max_drawdown": float(backtest_summary_by_variant.get(variant_id, {}).get("max_drawdown", -0.08)),
                "holdout_max_drawdown": -0.07,
                "holdout_mean_net_return": 0.01,
                "net_return_delta": -0.002,
            }
            for variant_id in selected_variant_ids
        ],
    )
    (stage_formal_dir / "rolling_holdout_stability.json").write_text(
        json.dumps(
            {
                "stage": "csf_holdout_validation",
                "selected_variant_ids": selected_variant_ids,
                "direction_match": True,
                "stability_status": "pass",
                "rolling_window_count": 3,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "regime_shift_audit.json").write_text(
        json.dumps(
            {
                "stage": "csf_holdout_validation",
                "selected_variant_ids": selected_variant_ids,
                "regime_shift_detected": False,
                "audit_status": "pass",
                "explanation": "No material regime shift detected in the runtime fixture.",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
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
                "- artifact_catalog.md",
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
    shape_result = validate_stage_artifacts(stage_formal_dir, load_artifact_contract("csf_holdout_validation"))
    semantic_result = validate_csf_holdout_validation_semantics(stage_formal_dir, lineage_root)
    errors = [*shape_result.errors, *semantic_result.errors]
    if errors:
        raise ValueError("csf_holdout_validation formal artifacts do not match artifact contract: " + "; ".join(errors))
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = ensure_stage_author_layout(stage_dir)["author_draft_dir"] / CSF_HOLDOUT_VALIDATION_DRAFT_FILE
    return require_confirmed_freeze_groups(
        draft_path,
        CSF_HOLDOUT_VALIDATION_GROUP_ORDER,
        stage_label="csf_holdout_validation",
    )


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_holdout_validation draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} expected json map")
    return payload


def _read_backtest_variant_ids(path: Path) -> list[str]:
    import csv

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [str(row.get("variant_id", "")).strip() for row in rows if str(row.get("variant_id", "")).strip()]


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()
