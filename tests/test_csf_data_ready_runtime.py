from pathlib import Path

import yaml

from runtime.tools.csf_data_ready_runtime import (
    build_csf_data_ready_from_mandate,
    scaffold_csf_data_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _csf_data_ready_draft(*, confirmed: bool) -> dict:
    return {
        "groups": {
            "panel_contract": {
                "confirmed": confirmed,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "cross_section_time_key": "date",
                    "asset_key": "asset",
                    "universe_membership_rule": "Use the frozen mandate universe snapshot per date.",
                },
                "missing_items": [],
            },
            "taxonomy_contract": {
                "confirmed": confirmed,
                "draft": {
                    "group_taxonomy_reference": "sector_bucket_v1",
                    "group_mapping_rule": "Map every asset into one stable research bucket.",
                    "taxonomy_note": "Group taxonomy stays frozen for downstream group-neutral analysis.",
                },
                "missing_items": [],
            },
            "eligibility_contract": {
                "confirmed": confirmed,
                "draft": {
                    "eligibility_base_rule": "Drop dates and assets failing minimum liquidity and coverage.",
                    "coverage_floor_rule": "Require 95% panel coverage before downstream factor computation.",
                    "mask_audit_note": "Eligibility stays separate from factor-specific missingness.",
                },
                "missing_items": [],
            },
            "shared_feature_base": {
                "confirmed": confirmed,
                "draft": {
                    "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
                    "shared_feature_note": "Shared base stops before thesis-specific factor logic.",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": confirmed,
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
        }
    }


def _prepare_mandate_stage(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    formal_dir = mandate_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (formal_dir / name).write_text("ok\n", encoding="utf-8")
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


def test_scaffold_csf_data_ready_creates_grouped_draft(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_stage(lineage_root)

    stage_dir = scaffold_csf_data_ready(lineage_root)

    draft = yaml.safe_load((stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml").read_text(encoding="utf-8"))
    assert stage_dir == lineage_root / "02_csf_data_ready"
    assert set(draft["groups"]) == {
        "panel_contract",
        "taxonomy_contract",
        "eligibility_contract",
        "shared_feature_base",
        "delivery_contract",
    }


def test_build_csf_data_ready_writes_required_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))

    built_dir = build_csf_data_ready_from_mandate(lineage_root)

    assert built_dir == stage_dir
    formal_dir = stage_dir / "author" / "formal"
    assert (formal_dir / "panel_manifest.json").exists()
    assert (formal_dir / "asset_universe_membership.parquet").exists()
    assert (formal_dir / "cross_section_coverage.parquet").exists()
    assert (formal_dir / "eligibility_base_mask.parquet").exists()
    assert (formal_dir / "shared_feature_base").exists()
    assert (formal_dir / "asset_taxonomy_snapshot.parquet").exists()
    assert (formal_dir / "csf_data_contract.md").exists()
    assert (formal_dir / "csf_data_ready_gate_decision.md").exists()
    assert (formal_dir / "run_manifest.json").exists()
    assert (formal_dir / "rebuild_csf_data_ready.py").exists()
    assert (formal_dir / "artifact_catalog.md").exists()
    assert (formal_dir / "field_dictionary.md").exists()
