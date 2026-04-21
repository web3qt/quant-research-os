"""Shared stage fixture builders for CSF pipeline tests.

Each builder creates a complete stage's formal artifacts in a lineage_root,
simulating what the author runtime would produce. Builders are composable:
upstream stages must be built before downstream stages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    import polars as pl

    path.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(path)


def _write_text(path: Path, content: str = "ok\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Freeze draft fixtures — simulate human decisions
# ---------------------------------------------------------------------------

MANDATE_FREEZE_DRAFT = {
    "groups": {
        "research_intent": {
            "confirmed": True,
            "draft": {
                "research_question": "Does BTC momentum predict ALT returns?",
                "primary_hypothesis": "BTC lead effect transfers to ALTs.",
                "counter_hypothesis": "Shared beta only.",
                "research_route": "cross_sectional_factor",
                "factor_role": "standalone_alpha",
                "factor_structure": "single_factor",
                "portfolio_expression": "long_short_market_neutral",
                "neutralization_policy": "group_neutral",
                "target_strategy_reference": "",
                "group_taxonomy_reference": "sector_bucket_v1",
                "excluded_routes": ["time_series_signal"],
                "route_rationale": ["Cross-asset ranking is the primary expression."],
            },
        },
        "scope_contract": {
            "confirmed": True,
            "draft": {
                "market": "binance perp",
                "universe": "high liquidity alts",
                "target_task": "study",
            },
        },
        "data_contract": {
            "confirmed": True,
            "draft": {
                "data_source": "binance um futures klines",
                "bar_size": "5m",
                "holding_horizons": ["15m", "30m"],
                "timestamp_semantics": "close-to-close utc bars",
                "no_lookahead_guardrail": "labels use completed bars only",
            },
        },
        "execution_contract": {
            "confirmed": True,
            "draft": {
                "execution_constraints": "No look-ahead bias.",
                "must_reuse_constraints": ["data_source", "bar_size"],
                "change_requires_relineage": ["research_route", "time_split"],
            },
        },
    },
}

CSF_DATA_READY_FREEZE_DRAFT = {
    "groups": {
        "panel_contract": {
            "confirmed": True,
            "draft": {
                "panel_primary_key": ["date", "asset"],
                "cross_section_time_key": "date",
                "asset_key": "asset",
                "universe_membership_rule": "Use the frozen mandate universe snapshot per date.",
            },
            "missing_items": [],
        },
        "taxonomy_contract": {
            "confirmed": True,
            "draft": {
                "group_taxonomy_reference": "sector_bucket_v1",
                "group_mapping_rule": "Map every asset into one stable research bucket.",
                "taxonomy_note": "Group taxonomy stays frozen for downstream group-neutral analysis.",
            },
            "missing_items": [],
        },
        "eligibility_contract": {
            "confirmed": True,
            "draft": {
                "eligibility_base_rule": "Drop dates and assets failing minimum liquidity and coverage.",
                "coverage_floor_rule": "Require 95% panel coverage before downstream factor computation.",
                "mask_audit_note": "Eligibility stays separate from factor-specific missingness.",
            },
            "missing_items": [],
        },
        "shared_feature_base": {
            "confirmed": True,
            "draft": {
                "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
                "shared_feature_note": "Shared base stops before thesis-specific factor logic.",
            },
            "missing_items": [],
        },
        "delivery_contract": {
            "confirmed": True,
            "draft": {
                "machine_artifacts": [
                    "panel_manifest.json",
                    "asset_universe_membership.parquet",
                    "cross_section_coverage.parquet",
                    "eligibility_base_mask.parquet",
                ],
                "consumer_stage": "csf_signal_ready",
                "frozen_inputs_note": "Downstream factor builders must consume the frozen panel base.",
            },
            "missing_items": [],
        },
    },
}

CSF_SIGNAL_READY_FREEZE_DRAFT = {
    "groups": {
        "factor_identity": {
            "confirmed": True,
            "draft": {
                "factor_id": "btc_lead_alt_follow",
                "factor_version": "v1",
                "factor_direction": "high_better",
                "factor_structure": "single_factor",
            },
            "missing_items": [],
        },
        "panel_contract": {
            "confirmed": True,
            "draft": {
                "panel_primary_key": ["date", "asset"],
                "as_of_semantics": "Factor values are frozen at the cross-section close.",
                "coverage_contract": "Require at least 95% asset coverage per cross-section.",
            },
            "missing_items": [],
        },
        "factor_expression": {
            "confirmed": True,
            "draft": {
                "raw_factor_fields": ["btc_move", "alt_residual"],
                "derived_factor_fields": ["lead_follow_score"],
                "final_score_field": "factor_value",
                "missing_value_policy": "Preserve nulls and report eligibility separately.",
            },
            "missing_items": [],
        },
        "context_contract": {
            "confirmed": True,
            "draft": {
                "group_context_fields": ["sector_bucket"],
                "component_factor_ids": [],
                "score_combination_formula": "single_factor_passthrough",
            },
            "missing_items": [],
        },
        "delivery_contract": {
            "confirmed": True,
            "draft": {
                "machine_artifacts": ["factor_panel.parquet", "factor_manifest.yaml"],
                "consumer_stage": "csf_train_freeze",
                "frozen_inputs_note": "Train may set preprocessing rules but not redefine the factor.",
            },
            "missing_items": [],
        },
    },
}

# ---------------------------------------------------------------------------
# Stage builders
# ---------------------------------------------------------------------------


def prepare_mandate(lineage_root: Path) -> Path:
    """Create mandate stage with route = cross_sectional_factor."""
    stage_dir = lineage_root / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)

    for name in ["mandate.md", "research_scope.md", "run_config.toml", "artifact_catalog.md", "field_dictionary.md"]:
        _write_text(formal_dir / name)

    _write_json(
        formal_dir / "time_split.json",
        {"train": "2024-01-01:2024-06-30", "test": "2024-07-01:2024-09-30", "backtest": "2024-10-01:2024-12-31", "holdout": "2025-01-01:2025-03-31"},
    )
    _write_yaml(formal_dir / "parameter_grid.yaml", {"parameters": [{"name": "lookback", "values": [5, 10, 20]}]})
    _write_json(
        formal_dir / "run_manifest.json",
        {"stage": "mandate", "lineage_id": lineage_root.name, "stage_outputs": []},
    )

    _write_yaml(
        formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_market_neutral",
            "neutralization_policy": "group_neutral",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    return stage_dir


def prepare_csf_data_ready(lineage_root: Path) -> Path:
    """Create csf_data_ready stage with realistic parquet artifacts."""
    stage_dir = lineage_root / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        formal_dir / "panel_manifest.json",
        {
            "panel_primary_key": ["date", "asset"],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
            "coverage_floor_min_ratio": 0.95,
        },
    )
    _write_parquet(
        formal_dir / "asset_universe_membership.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "in_universe": True},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "in_universe": True},
        ],
    )
    _write_parquet(
        formal_dir / "cross_section_coverage.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 2}],
    )
    _write_parquet(
        formal_dir / "eligibility_base_mask.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "eligible": True},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "eligible": True},
        ],
    )
    _write_parquet(
        formal_dir / "asset_taxonomy_snapshot.parquet",
        [
            {"asset": "SOLUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "majors"},
            {"asset": "DOGEUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "memes"},
        ],
    )
    for name in ["csf_data_contract.md", "csf_data_ready_gate_decision.md", "artifact_catalog.md", "field_dictionary.md"]:
        _write_text(formal_dir / name)
    _write_json(
        formal_dir / "run_manifest.json",
        {"stage": "csf_data_ready", "lineage_id": lineage_root.name, "stage_outputs": ["panel_manifest.json", "asset_universe_membership.parquet"]},
    )
    _write_text(formal_dir / "rebuild_csf_data_ready.py", "# rebuild script\n")

    shared_dir = formal_dir / "shared_feature_base"
    shared_dir.mkdir(exist_ok=True)
    _write_parquet(
        shared_dir / "returns_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "return_1d": 0.02},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "return_1d": -0.01},
        ],
    )
    _write_parquet(
        shared_dir / "liquidity_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "dollar_volume": 1000.0},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "dollar_volume": 500.0},
        ],
    )
    _write_parquet(
        shared_dir / "beta_inputs.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "beta_proxy": 1.0},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "beta_proxy": 1.2},
        ],
    )

    # mandate is always a prerequisite
    prepare_mandate(lineage_root)
    return stage_dir


def prepare_csf_signal_ready(lineage_root: Path) -> Path:
    """Create csf_signal_ready stage by building from data_ready."""
    from runtime.tools.csf_signal_ready_runtime import (
        build_csf_signal_ready_from_data_ready,
        scaffold_csf_signal_ready,
    )

    prepare_csf_data_ready(lineage_root)

    stage_dir = lineage_root / "03_csf_signal_ready"
    stage_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", CSF_SIGNAL_READY_FREEZE_DRAFT)

    build_csf_signal_ready_from_data_ready(lineage_root)
    return stage_dir


def prepare_csf_train_freeze(lineage_root: Path) -> Path:
    """Create csf_train_freeze stage by building from signal_ready."""
    from runtime.tools.csf_train_runtime import build_csf_train_freeze_from_signal_ready

    prepare_csf_signal_ready(lineage_root)

    stage_dir = lineage_root / "04_csf_train_freeze"
    stage_dir.mkdir(parents=True, exist_ok=True)

    draft = _csf_train_freeze_draft_confirmed()
    _write_yaml(stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml", draft)

    build_csf_train_freeze_from_signal_ready(lineage_root)
    return stage_dir


def prepare_csf_test_evidence(lineage_root: Path) -> Path:
    """Create csf_test_evidence stage by building from train_freeze."""
    from runtime.tools.csf_test_evidence_runtime import build_csf_test_evidence_from_train_freeze

    prepare_csf_train_freeze(lineage_root)

    stage_dir = lineage_root / "05_csf_test_evidence"
    stage_dir.mkdir(parents=True, exist_ok=True)

    draft = _csf_test_evidence_draft_confirmed()
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_freeze_draft.yaml", draft)

    build_csf_test_evidence_from_train_freeze(lineage_root)
    return stage_dir


def prepare_csf_backtest_ready(lineage_root: Path) -> Path:
    """Create csf_backtest_ready stage by building from test_evidence."""
    from runtime.tools.csf_backtest_runtime import build_csf_backtest_ready_from_test_evidence

    prepare_csf_test_evidence(lineage_root)

    stage_dir = lineage_root / "06_csf_backtest_ready"
    stage_dir.mkdir(parents=True, exist_ok=True)

    draft = _csf_backtest_ready_draft_confirmed()
    _write_yaml(stage_dir / "author" / "draft" / "csf_backtest_ready_freeze_draft.yaml", draft)

    build_csf_backtest_ready_from_test_evidence(lineage_root)
    return stage_dir


def prepare_csf_holdout_validation(lineage_root: Path) -> Path:
    """Create csf_holdout_validation stage by building from backtest_ready."""
    from runtime.tools.csf_holdout_runtime import build_csf_holdout_validation_from_backtest

    prepare_csf_backtest_ready(lineage_root)

    stage_dir = lineage_root / "07_csf_holdout_validation"
    stage_dir.mkdir(parents=True, exist_ok=True)

    draft = _csf_holdout_validation_draft_confirmed()
    _write_yaml(stage_dir / "author" / "draft" / "csf_holdout_validation_freeze_draft.yaml", draft)

    build_csf_holdout_validation_from_backtest(lineage_root)
    return stage_dir


# ---------------------------------------------------------------------------
# Draft fixtures for stages that need confirmed freeze drafts
# ---------------------------------------------------------------------------

def _csf_train_freeze_draft_confirmed() -> dict[str, Any]:
    return {
        "groups": {
            "train_window": {
                "confirmed": True,
                "draft": {
                    "train_window_start": "2024-01-01",
                    "train_window_end": "2024-06-30",
                    "window_split_logic": "Chronological, no shuffle.",
                },
                "missing_items": [],
            },
            "preprocess_contract": {
                "confirmed": True,
                "draft": {
                    "preprocess_rules": ["z-score within cross-section"],
                    "governable_axes": ["preprocess_rules"],
                    "non_governable_axes": ["factor_panel", "factor_direction"],
                },
                "missing_items": [],
            },
            "quality_filter": {
                "confirmed": True,
                "draft": {
                    "quality_filters": ["drop_null_factor_rows"],
                    "threshold_contract_summary": "No hard threshold in v1.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["csf_train_freeze.yaml", "train_variant_ledger.csv"],
                    "consumer_stage": "csf_test_evidence",
                    "frozen_inputs_note": "Test may only consume frozen train artifacts.",
                },
                "missing_items": [],
            },
        },
    }


def _csf_test_evidence_draft_confirmed() -> dict[str, Any]:
    return {
        "groups": {
            "formal_gate_contract": {
                "confirmed": True,
                "draft": {
                    "core_test_metrics": ["ic_mean", "rank_ic"],
                    "pass_thresholds": {"ic_mean_gt": 0.0},
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["test_evidence_report.yaml"],
                    "consumer_stage": "csf_backtest_ready",
                },
                "missing_items": [],
            },
        },
    }


def _csf_backtest_ready_draft_confirmed() -> dict[str, Any]:
    return {
        "groups": {
            "execution_contract": {
                "confirmed": True,
                "draft": {
                    "execution_policy": "market_on_close",
                    "rebalance_cadence": "daily",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["backtest_result.parquet"],
                    "consumer_stage": "csf_holdout_validation",
                },
                "missing_items": [],
            },
        },
    }


def _csf_holdout_validation_draft_confirmed() -> dict[str, Any]:
    return {
        "groups": {
            "holdout_contract": {
                "confirmed": True,
                "draft": {
                    "holdout_window_start": "2024-07-01",
                    "holdout_window_end": "2024-12-31",
                    "reuse_rule": "single_use_only",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["holdout_result.yaml"],
                    "consumer_stage": "none",
                },
                "missing_items": [],
            },
        },
    }
