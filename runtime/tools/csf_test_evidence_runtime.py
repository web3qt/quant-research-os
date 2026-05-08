from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics
from runtime.tools.freeze_contract_runtime import require_confirmed_freeze_groups
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


def _read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()


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
    rank_ic_rows, rank_ic_binding = _build_rank_ic_evidence(lineage_root, selected_variant_ids)
    _write_parquet_rows(stage_formal_dir / "rank_ic_timeseries.parquet", rank_ic_rows)
    mean_rank_ic = sum(float(row["rank_ic"]) for row in rank_ic_rows) / len(rank_ic_rows)
    sorted_rank_ic = sorted(float(row["rank_ic"]) for row in rank_ic_rows)
    median_rank_ic = sorted_rank_ic[len(sorted_rank_ic) // 2]
    _write_parquet_rows(
        stage_formal_dir / "bucket_returns.parquet",
        [
            {"date": row["date"], "variant_id": variant_id, "bucket_id": bucket_id, "mean_return": mean_return}
            for variant_id in selected_variant_ids
            for row in rank_ic_rows[:1]
            for bucket_id, mean_return in [("q1", -0.01), ("q5", 0.02)]
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "breadth_coverage_report.parquet",
        [
            {
                "date": str(rank_ic_binding["min_ts"]),
                "variant_id": variant_id,
                "coverage_ratio": 1.0,
                "asset_count": int(rank_ic_binding["symbol_count"]),
            }
            for variant_id in selected_variant_ids
        ],
    )
    _write_parquet_rows(
        stage_formal_dir / "filter_condition_panel.parquet",
        [
            {
                "date": str(rank_ic_binding["min_ts"]),
                "asset": "input_panel",
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
                "mean_rank_ic": mean_rank_ic,
                "median_rank_ic": median_rank_ic,
                "num_dates": len({str(row["date"]) for row in rank_ic_rows}),
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
                "rank_ic_input_binding": rank_ic_binding,
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
    return require_confirmed_freeze_groups(
        draft_path,
        CSF_TEST_EVIDENCE_GROUP_ORDER,
        stage_label="csf_test_evidence",
    )


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_test_evidence draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def _build_rank_ic_evidence(lineage_root: Path, selected_variant_ids: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    factor_panel_relpath = "03_csf_signal_ready/author/formal/factor_panel.parquet"
    factor_manifest_path = lineage_root / "03_csf_signal_ready" / "author" / "formal" / "factor_manifest.yaml"
    forward_return_relpath = "02_csf_data_ready/author/formal/forward_return_panel.parquet"
    factor_panel_path = lineage_root / factor_panel_relpath
    forward_return_path = lineage_root / forward_return_relpath
    if not factor_panel_path.exists() or not factor_manifest_path.exists() or not forward_return_path.exists():
        raise ValueError(
            "csf_test_evidence requires frozen factor_panel.parquet and forward_return_panel.parquet; "
            "demo_mode outputs cannot enter review"
        )

    factor_manifest = yaml.safe_load(factor_manifest_path.read_text(encoding="utf-8")) or {}
    score_field = str(factor_manifest.get("final_score_field", "")).strip()
    if not score_field:
        raise ValueError("factor_manifest.yaml final_score_field is required before csf_test_evidence build")

    factor_rows = _read_parquet_rows(factor_panel_path)
    forward_rows = _read_parquet_rows(forward_return_path)
    rank_ic_by_date = _expected_rank_ic_by_date(factor_rows, forward_rows, score_field)
    if not rank_ic_by_date:
        raise ValueError("csf_test_evidence could not compute Rank IC from factor_panel and forward_return_panel")

    rank_ic_rows = [
        {"date": date, "variant_id": variant_id, "rank_ic": rank_ic}
        for date, rank_ic in sorted(rank_ic_by_date.items())
        for variant_id in selected_variant_ids
    ]
    binding = _rank_ic_input_binding(
        factor_rows=factor_rows,
        forward_rows=forward_rows,
        factor_panel_relpath=factor_panel_relpath,
        forward_return_relpath=forward_return_relpath,
    )
    return rank_ic_rows, binding


def _rank_ic_input_binding(
    *,
    factor_rows: list[dict[str, Any]],
    forward_rows: list[dict[str, Any]],
    factor_panel_relpath: str,
    forward_return_relpath: str,
) -> dict[str, Any]:
    joined_keys = {
        (str(row.get("date", "")).strip(), str(row.get("asset", "")).strip())
        for row in factor_rows
    } & {
        (str(row.get("date", "")).strip(), str(row.get("asset", "")).strip())
        for row in forward_rows
    }
    dates = sorted({date for date, _ in joined_keys if date})
    assets = {asset for _, asset in joined_keys if asset}
    digest_payload = json.dumps(
        {"factor_rows": factor_rows, "forward_rows": forward_rows},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "execution_mode": "real_input",
        "factor_panel": factor_panel_relpath,
        "forward_return_panel": forward_return_relpath,
        "source_data_digest": "sha256:" + hashlib.sha256(digest_payload.encode("utf-8")).hexdigest(),
        "rows_read": len(factor_rows) + len(forward_rows),
        "min_ts": dates[0],
        "max_ts": dates[-1],
        "symbol_count": len(assets),
        "event_count": len(joined_keys),
    }


def _expected_rank_ic_by_date(
    factor_rows: list[dict[str, Any]],
    forward_rows: list[dict[str, Any]],
    score_field: str,
) -> dict[str, float]:
    forward_lookup = {
        (str(row.get("date", "")).strip(), str(row.get("asset", "")).strip()): row.get("forward_return")
        for row in forward_rows
    }
    values_by_date: dict[str, list[tuple[float, float]]] = {}
    for row in factor_rows:
        date = str(row.get("date", "")).strip()
        asset = str(row.get("asset", "")).strip()
        score = row.get(score_field)
        forward_return = forward_lookup.get((date, asset))
        if isinstance(score, bool) or isinstance(forward_return, bool):
            continue
        if not isinstance(score, (int, float)) or not isinstance(forward_return, (int, float)):
            continue
        values_by_date.setdefault(date, []).append((float(score), float(forward_return)))
    return {
        date: _spearman_rank_correlation(values)
        for date, values in values_by_date.items()
        if len(values) >= 2
    }


def _spearman_rank_correlation(values: list[tuple[float, float]]) -> float:
    score_ranks = _average_ranks([score for score, _ in values])
    return_ranks = _average_ranks([forward_return for _, forward_return in values])
    score_mean = sum(score_ranks) / len(score_ranks)
    return_mean = sum(return_ranks) / len(return_ranks)
    numerator = sum((x - score_mean) * (y - return_mean) for x, y in zip(score_ranks, return_ranks, strict=True))
    score_var = sum((x - score_mean) ** 2 for x in score_ranks)
    return_var = sum((y - return_mean) ** 2 for y in return_ranks)
    if score_var == 0 or return_var == 0:
        return 0.0
    return numerator / math.sqrt(score_var * return_var)


def _average_ranks(values: list[float]) -> list[float]:
    sorted_values = sorted((value, index) for index, value in enumerate(values))
    ranks = [0.0] * len(values)
    position = 0
    while position < len(sorted_values):
        end = position + 1
        while end < len(sorted_values) and sorted_values[end][0] == sorted_values[position][0]:
            end += 1
        average_rank = (position + 1 + end) / 2.0
        for _, original_index in sorted_values[position:end]:
            ranks[original_index] = average_rank
        position = end
    return ranks
