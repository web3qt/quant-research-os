from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.stage_program_scaffold import STAGE_PROGRAM_SPECS
from tests.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.test_research_session_runtime import _write_minimal_stage_outputs


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_empty_parquet(path: Path, schema: dict[str, pa.DataType]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({key: pa.array([], type=value) for key, value in schema.items()}), path)


def _prepare_csf_stage(tmp_path: Path, *, stage_key: str, stage_dir_name: str) -> Path:
    lineage_root = tmp_path / "outputs" / "topic_a"
    stage_dir = lineage_root / stage_dir_name
    _write_minimal_stage_outputs(stage_dir, stage=stage_key)

    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )

    ensure_stage_program(lineage_root, stage_key)
    write_fake_stage_provenance(lineage_root, stage_key)
    return stage_dir


def _write_review_request_and_result(stage_dir: Path, *, stage_key: str) -> None:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    handoff_manifest_path = stage_dir / "review" / "request" / "spawned_reviewer_handoff_manifest.yaml"
    _write_yaml(
        handoff_manifest_path,
        {
            "review_cycle_id": f"{stage_key}-cycle-1",
            "lineage_id": stage_dir.parent.name,
            "stage": spec["stage_id"],
            "required_program_dir": str(spec["program_dir"]),
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": [],
            "required_provenance_paths": ["program_execution_manifest.json"],
            "permitted_input_roots": ["review/request", "author/formal"],
            "permitted_output_roots": ["review/result"],
            "required_result_write_root": "review/result",
        },
    )
    handoff_manifest_digest = hashlib.sha256(
        handoff_manifest_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    request_payload = {
        "review_cycle_id": f"{stage_key}-cycle-1",
        "lineage_id": stage_dir.parent.name,
        "stage": spec["stage_id"],
        "author_identity": "author-agent",
        "author_session_id": "author-session",
        "required_program_dir": str(spec["program_dir"]),
        "required_program_entrypoint": "run_stage.py",
        "required_artifact_paths": [],
        "required_provenance_paths": ["program_execution_manifest.json"],
        "required_reviewer_mode": "adversarial",
        "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
        "handoff_manifest_digest": handoff_manifest_digest,
        "required_result_write_root": "review/result",
    }
    receipt_payload = {
        "review_cycle_id": f"{stage_key}-cycle-1",
        "launcher_owner": "qros-runtime-launcher",
        "launcher_session_id": "launcher-session",
        "spawn_mode": "spawned_agent",
        "fork_context": False,
        "write_root": "review/result",
        "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
        "handoff_manifest_digest": handoff_manifest_digest,
        "requested_reviewer_identity": "reviewer-agent",
        "requested_reviewer_session_id": "review-session",
        "receipt_written_at": "2026-04-17T03:00:00Z",
    }
    result_payload = {
        "review_cycle_id": f"{stage_key}-cycle-1",
        "reviewer_identity": "reviewer-agent",
        "reviewer_role": "reviewer",
        "reviewer_session_id": "review-session",
        "reviewer_mode": "adversarial",
        "reviewer_execution_mode": "spawned_agent",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_manifest_digest": handoff_manifest_digest,
        "review_loop_outcome": "CLOSURE_READY_PASS",
        "reviewed_program_dir": str(spec["program_dir"]),
        "reviewed_program_entrypoint": "run_stage.py",
        "reviewed_artifact_paths": [],
        "reviewed_provenance_paths": ["program_execution_manifest.json"],
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "downstream_permissions": [],
    }
    _write_yaml(stage_dir / "review" / "request" / "adversarial_review_request.yaml", request_payload)
    _write_yaml(stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml", receipt_payload)
    _write_yaml(stage_dir / "review" / "result" / "adversarial_review_result.yaml", result_payload)


def test_run_stage_review_blocks_csf_data_ready_when_panel_manifest_contract_is_incomplete(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_data_ready",
        stage_dir_name="02_csf_data_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_json(
        formal_dir / "panel_manifest.json",
        {
            "panel_primary_key": [],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel"],
        },
    )
    _write_review_request_and_result(stage_dir, stage_key="csf_data_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("panel_primary_key" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_signal_ready_when_factor_direction_is_missing(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_signal_ready",
        stage_dir_name="03_csf_signal_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_yaml(
        formal_dir / "factor_manifest.yaml",
        {
            "factor_id": "btc_lead_alt_follow",
            "factor_version": "v1",
            "factor_direction": "",
            "factor_structure": "single_factor",
            "panel_primary_key": ["date", "asset"],
            "raw_factor_fields": ["btc_move", "alt_residual"],
            "derived_factor_fields": ["lead_follow_score"],
            "final_score_field": "factor_value",
        },
    )
    _write_yaml(
        formal_dir / "component_factor_manifest.yaml",
        {
            "component_factor_ids": [],
            "score_combination_formula": "single_factor_passthrough",
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage_key="csf_signal_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("factor_direction" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_data_ready_when_membership_rows_are_empty(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_data_ready",
        stage_dir_name="02_csf_data_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_empty_parquet(
        formal_dir / "asset_universe_membership.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "in_universe": pa.bool_(),
        },
    )
    _write_review_request_and_result(stage_dir, stage_key="csf_data_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("observed_row_count" in item or "non-empty asset_universe_membership" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_data_ready_when_coverage_ratio_breaks_floor(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_data_ready",
        stage_dir_name="02_csf_data_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_json(
        formal_dir / "panel_manifest.json",
        {
            "panel_primary_key": ["date", "asset"],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel"],
            "coverage_floor_min_ratio": 0.95,
        },
    )
    _write_parquet(
        formal_dir / "cross_section_coverage.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 0.60, "asset_count": 2}],
    )
    _write_review_request_and_result(stage_dir, stage_key="csf_data_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("coverage_ratio" in item or "coverage floor" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_train_freeze_when_candidate_variants_are_empty(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_train_freeze",
        stage_dir_name="04_csf_train_freeze",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_yaml(
        formal_dir / "csf_train_freeze.yaml",
        {
            "preprocess_contract": {
                "winsorize_policy": "cross_section_2sided_quantile",
                "standardize_policy": "zscore_by_date",
                "missing_fill_policy": "no_fill",
                "coverage_floor_rule": "drop cross-sections below 95% coverage",
            },
            "neutralization_contract": {
                "neutralization_policy": "group_neutral",
                "beta_estimation_window": "60d",
                "group_taxonomy_reference": "sector_bucket_v1",
                "residualization_formula": "factor_value - group_mean(factor_value)",
            },
            "ranking_bucket_contract": {
                "ranking_scope": "full_universe",
                "bucket_schema": "quintile",
                "quantile_count": "5",
                "min_names_per_bucket": "10",
            },
            "rebalance_contract": {
                "rebalance_frequency": "1d",
                "signal_lag_rule": "trade next bar after score freeze",
                "holding_period_rule": "hold 5 trading days",
                "overlap_policy": "allow_overlap",
            },
            "search_governance_contract": {
                "candidate_variant_ids": [],
                "kept_variant_ids": ["baseline_v1"],
                "rejected_variant_ids": [],
                "selection_rule": "baseline-only first wave",
                "frozen_signal_contract_reference": "btc_shock_alt_fragility:v1",
                "train_governable_axes": ["btc_shock_return_bps"],
                "non_governable_axes_after_signal": ["raw_factor_fields"],
                "non_governable_axis_reject_rule": "reopen signal if frozen axes change",
            },
        },
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage_key="csf_train_freeze")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("candidate_variant_ids" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_train_freeze_when_train_quality_rows_are_empty(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_train_freeze",
        stage_dir_name="04_csf_train_freeze",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_empty_parquet(
        formal_dir / "train_factor_quality.parquet",
        {
            "variant_id": pa.string(),
            "quality_score": pa.float64(),
        },
    )
    _write_review_request_and_result(stage_dir, stage_key="csf_train_freeze")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("train_factor_quality" in item or "observed_row_count" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_train_freeze_when_variant_ledger_has_duplicate_variant_id(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_train_freeze",
        stage_dir_name="04_csf_train_freeze",
    )
    formal_dir = stage_dir / "author" / "formal"
    (formal_dir / "train_variant_ledger.csv").write_text(
        "\n".join(
            [
                "variant_id,status,selection_rule",
                "baseline_v1,kept,baseline-only first wave",
                "baseline_v1,rejected,baseline-only first wave",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_review_request_and_result(stage_dir, stage_key="csf_train_freeze")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("observed_duplicate_key" in item or "variant_id" in item for item in payload["blocking_findings"])


def test_run_stage_review_blocks_csf_signal_ready_when_factor_panel_has_duplicate_key(tmp_path: Path) -> None:
    stage_dir = _prepare_csf_stage(
        tmp_path,
        stage_key="csf_signal_ready",
        stage_dir_name="03_csf_signal_ready",
    )
    formal_dir = stage_dir / "author" / "formal"
    _write_parquet(
        formal_dir / "factor_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "BTCUSDT", "factor_value": 1.0},
            {"date": "2024-01-01", "asset": "BTCUSDT", "factor_value": 0.5},
        ],
    )
    (formal_dir / "run_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_review_request_and_result(stage_dir, stage_key="csf_signal_ready")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("observed_duplicate_key" in item or "factor_panel to be unique" in item for item in payload["blocking_findings"])
