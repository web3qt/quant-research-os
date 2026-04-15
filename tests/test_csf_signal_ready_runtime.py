from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_signal_ready_runtime import (
    build_csf_signal_ready_from_data_ready,
    scaffold_csf_signal_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict]) -> None:
    import pyarrow as pa

    path.parent.mkdir(parents=True, exist_ok=True)
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _csf_signal_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "factor_identity": {
                "confirmed": confirmed,
                "draft": {
                    "factor_id": "btc_lead_alt_follow",
                    "factor_version": "v1",
                    "factor_direction": "high_better",
                    "factor_structure": "single_factor",
                },
                "missing_items": [],
            },
            "panel_contract": {
                "confirmed": confirmed,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "as_of_semantics": "Factor values are frozen at the cross-section close.",
                    "coverage_contract": "Require at least 95% asset coverage per cross-section.",
                },
                "missing_items": [],
            },
            "factor_expression": {
                "confirmed": confirmed,
                "draft": {
                    "raw_factor_fields": ["btc_move", "alt_residual"],
                    "derived_factor_fields": ["lead_follow_score"],
                    "final_score_field": "factor_value",
                    "missing_value_policy": "Preserve nulls and report eligibility separately.",
                },
                "missing_items": [],
            },
            "context_contract": {
                "confirmed": confirmed,
                "draft": {
                    "group_context_fields": ["sector_bucket"],
                    "component_factor_ids": [],
                    "score_combination_formula": "single_factor_passthrough",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
                "draft": {
                    "machine_artifacts": ["factor_panel.parquet", "factor_manifest.yaml"],
                    "consumer_stage": "csf_train_freeze",
                    "frozen_inputs_note": "Train may set preprocessing rules but not redefine the factor.",
                },
                "missing_items": [],
            },
        }
    }


def _prepare_csf_data_ready_stage(lineage_root: Path) -> None:
    stage_dir = lineage_root / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    _write_yaml(
        formal_dir / "panel_manifest.json",
        {
            "panel_primary_key": ["date", "asset"],
            "cross_section_time_key": "date",
            "asset_key": "asset",
            "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
            "coverage_floor_min_ratio": 0.95,
        },
    )
    _write_parquet_rows(
        formal_dir / "asset_universe_membership.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "in_universe": True},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "in_universe": True},
        ],
    )
    _write_parquet_rows(
        formal_dir / "cross_section_coverage.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 1.0, "asset_count": 2}],
    )
    _write_parquet_rows(
        formal_dir / "eligibility_base_mask.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "eligible": True},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "eligible": True},
        ],
    )
    _write_parquet_rows(
        formal_dir / "asset_taxonomy_snapshot.parquet",
        [
            {"asset": "SOLUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "majors"},
            {"asset": "DOGEUSDT", "group_taxonomy_reference": "sector_bucket_v1", "group_bucket": "memes"},
        ],
    )
    for name in [
        "csf_data_contract.md",
        "csf_data_ready_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
    shared_dir = formal_dir / "shared_feature_base"
    shared_dir.mkdir()
    _write_parquet_rows(
        shared_dir / "returns_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "return_1d": 0.02},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "return_1d": -0.01},
        ],
    )
    _write_parquet_rows(
        shared_dir / "liquidity_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "dollar_volume": 1000.0},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "dollar_volume": 500.0},
        ],
    )
    _write_parquet_rows(
        shared_dir / "beta_inputs.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "beta_proxy": 1.0},
            {"date": "2024-01-01", "asset": "DOGEUSDT", "beta_proxy": 1.2},
        ],
    )
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )


def test_scaffold_csf_signal_ready_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)

    stage_dir = scaffold_csf_signal_ready(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "03_csf_signal_ready"
    assert set(draft["groups"]) == {
        "factor_identity",
        "panel_contract",
        "factor_expression",
        "context_contract",
        "delivery_contract",
    }


def test_build_csf_signal_ready_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)
    stage_dir = lineage_root / "03_csf_signal_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", _csf_signal_ready_draft(confirmed=True))

    built_dir = build_csf_signal_ready_from_data_ready(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "factor_panel.parquet").exists()
    assert (formal_dir / "factor_manifest.yaml").exists()
    assert (formal_dir / "component_factor_manifest.yaml").exists()
    assert (formal_dir / "factor_coverage_report.parquet").exists()
    assert (formal_dir / "factor_group_context.parquet").exists()
    assert (formal_dir / "factor_contract.md").exists()
    assert (formal_dir / "factor_field_dictionary.md").exists()
    assert (formal_dir / "csf_signal_ready_gate_decision.md").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()

    factor_panel = pq.read_table(formal_dir / "factor_panel.parquet").to_pylist()
    factor_coverage = pq.read_table(formal_dir / "factor_coverage_report.parquet").to_pylist()
    factor_group_context = pq.read_table(formal_dir / "factor_group_context.parquet").to_pylist()
    assert len(factor_panel) > 0
    assert len(factor_coverage) > 0
    assert len(factor_group_context) > 0
    assert len({(row["date"], row["asset"]) for row in factor_panel}) == len(factor_panel)
    assert {row["asset"] for row in factor_panel} == {"SOLUSDT", "DOGEUSDT"}
    assert {row["asset"] for row in factor_panel} == {row["asset"] for row in factor_group_context}
