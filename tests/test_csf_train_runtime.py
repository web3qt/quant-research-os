from pathlib import Path

import yaml

from runtime.tools.csf_train_runtime import build_csf_train_freeze_from_signal_ready, scaffold_csf_train_freeze


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _csf_train_freeze_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "preprocess_contract": {
                "confirmed": confirmed,
                "draft": {
                    "winsorize_policy": "cross_section_2sided_quantile",
                    "standardize_policy": "zscore_by_date",
                    "missing_fill_policy": "no_fill",
                    "coverage_floor_rule": "drop cross-sections below 95% coverage",
                },
                "missing_items": [],
            },
            "neutralization_contract": {
                "confirmed": confirmed,
                "draft": {
                    "neutralization_policy": "group_neutral",
                    "beta_estimation_window": "60d",
                    "group_taxonomy_reference": "sector_bucket_v1",
                    "residualization_formula": "factor_value - group_mean(factor_value)",
                },
                "missing_items": [],
            },
            "ranking_bucket_contract": {
                "confirmed": confirmed,
                "draft": {
                    "ranking_scope": "full_universe",
                    "bucket_schema": "quintile",
                    "quantile_count": "5",
                    "min_names_per_bucket": "10",
                },
                "missing_items": [],
            },
            "rebalance_contract": {
                "confirmed": confirmed,
                "draft": {
                    "rebalance_frequency": "1d",
                    "signal_lag_rule": "trade next bar after score freeze",
                    "holding_period_rule": "hold 5 trading days",
                    "overlap_policy": "allow_overlap",
                },
                "missing_items": [],
            },
            "search_governance_contract": {
                "confirmed": confirmed,
                "draft": {
                    "candidate_variant_ids": ["baseline_v1"],
                    "kept_variant_ids": ["baseline_v1"],
                    "rejected_variant_ids": [],
                    "selection_rule": "baseline-only first wave",
                    "frozen_signal_contract_reference": "btc_shock_alt_fragility:v1",
                    "train_governable_axes": [
                        "btc_shock_return_bps",
                        "beta_lookback_bars",
                        "short_bucket_pct",
                        "holding_minutes",
                    ],
                    "non_governable_axes_after_signal": [
                        "fragility_score_transform",
                        "raw_factor_fields",
                        "derived_factor_fields",
                        "score_combination_formula",
                    ],
                    "non_governable_axis_reject_rule": "variants that change signal-expression axes after csf_signal_ready must reopen csf_signal_ready instead of entering train_freeze",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["csf_train_freeze.yaml", "train_variant_ledger.csv"],
                    "consumer_stage": "csf_test_evidence",
                    "reuse_constraints": "Test must reuse the frozen train contract only.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_csf_signal_ready_stage(lineage_root: Path) -> None:
    stage_dir = lineage_root / "03_csf_signal_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
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
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")


def test_scaffold_csf_train_freeze_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_signal_ready_stage(lineage_root)

    stage_dir = scaffold_csf_train_freeze(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "04_csf_train_freeze"
    assert set(draft["groups"]) == {
        "preprocess_contract",
        "neutralization_contract",
        "ranking_bucket_contract",
        "rebalance_contract",
        "search_governance_contract",
        "delivery_contract",
    }


def test_build_csf_train_freeze_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_signal_ready_stage(lineage_root)
    stage_dir = lineage_root / "04_csf_train_freeze"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml", _csf_train_freeze_draft(confirmed=True))

    built_dir = build_csf_train_freeze_from_signal_ready(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "csf_train_freeze.yaml").exists()
    assert (formal_dir / "train_factor_quality.parquet").exists()
    assert (formal_dir / "train_variant_ledger.csv").exists()
    assert (formal_dir / "train_variant_rejects.csv").exists()
    assert (formal_dir / "train_bucket_diagnostics.parquet").exists()
    assert (formal_dir / "train_neutralization_diagnostics.parquet").exists()
    assert (formal_dir / "csf_train_contract.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()

    freeze_payload = yaml.safe_load((formal_dir / "csf_train_freeze.yaml").read_text(encoding="utf-8"))
    search_governance = freeze_payload["search_governance_contract"]
    assert search_governance["frozen_signal_contract_reference"] == "btc_shock_alt_fragility:v1"
    assert search_governance["train_governable_axes"] == [
        "btc_shock_return_bps",
        "beta_lookback_bars",
        "short_bucket_pct",
        "holding_minutes",
    ]
    assert search_governance["non_governable_axes_after_signal"] == [
        "fragility_score_transform",
        "raw_factor_fields",
        "derived_factor_fields",
        "score_combination_formula",
    ]
    assert (
        search_governance["non_governable_axis_reject_rule"]
        == "variants that change signal-expression axes after csf_signal_ready must reopen csf_signal_ready instead of entering train_freeze"
    )
