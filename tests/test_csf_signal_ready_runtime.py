from pathlib import Path

import yaml

from tools.csf_signal_ready_runtime import (
    build_csf_signal_ready_from_data_ready,
    scaffold_csf_signal_ready,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


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
    stage_dir.mkdir(parents=True)
    for name in [
        "panel_manifest.json",
        "asset_universe_membership.parquet",
        "cross_section_coverage.parquet",
        "eligibility_base_mask.parquet",
        "asset_taxonomy_snapshot.parquet",
        "csf_data_contract.md",
        "csf_data_ready_gate_decision.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (stage_dir / name).write_text("ok\n", encoding="utf-8")
    (stage_dir / "shared_feature_base").mkdir()
    mandate_dir = lineage_root / "01_mandate"
    mandate_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(
        mandate_dir / "research_route.yaml",
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

    draft = yaml.safe_load((stage_dir / "csf_signal_ready_freeze_draft.yaml").read_text(encoding="utf-8"))
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
    _write_yaml(stage_dir / "csf_signal_ready_freeze_draft.yaml", _csf_signal_ready_draft(confirmed=True))

    built_dir = build_csf_signal_ready_from_data_ready(lineage_root)

    assert built_dir == stage_dir
    assert (stage_dir / "factor_panel.parquet").exists()
    assert (stage_dir / "factor_manifest.yaml").exists()
    assert (stage_dir / "component_factor_manifest.yaml").exists()
    assert (stage_dir / "factor_coverage_report.parquet").exists()
    assert (stage_dir / "factor_group_context.parquet").exists()
    assert (stage_dir / "factor_contract.md").exists()
    assert (stage_dir / "factor_field_dictionary.md").exists()
    assert (stage_dir / "csf_signal_ready_gate_decision.md").exists()
    assert (stage_dir / "artifact_catalog.md").exists()
    assert (stage_dir / "field_dictionary.md").exists()
