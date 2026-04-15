from pathlib import Path

import yaml

from tests.lineage_program_support import write_fake_stage_provenance
from runtime.tools.lineage_program_runtime import inspect_stage_program, validate_stage_program
from runtime.tools.research_session import run_research_session
from runtime.tools.stage_program_scaffold import materialize_stage_program


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_ready_for_csf(lineage_root: Path) -> None:
    mandate_dir = lineage_root / "01_mandate"
    mandate_formal_dir = mandate_dir / "author" / "formal"
    mandate_review_closure_dir = mandate_dir / "review" / "closure"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    mandate_review_closure_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "latest_review_pack.yaml",
        "stage_gate_review.yaml",
        "stage_completion_certificate.yaml",
    ]:
        target_dir = mandate_review_closure_dir if name in {
            "latest_review_pack.yaml",
            "stage_gate_review.yaml",
            "stage_completion_certificate.yaml",
        } else mandate_formal_dir
        (target_dir / name).write_text("ok\n", encoding="utf-8")
    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_only_rank",
            "neutralization_policy": "group_neutral",
            "target_strategy_reference": "post_shock_weakness_v1",
            "group_taxonomy_reference": "sector_bucket_v1",
        },
    )
    _write_yaml(
        mandate_review_closure_dir / "stage_completion_certificate.yaml",
        {
            "stage_status": "PASS",
            "final_verdict": "PASS",
        },
    )
    _write_yaml(
        mandate_dir / "author" / "draft" / "next_stage_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-07T08:05:00Z",
            "source_stage": "mandate_next_stage_confirmation_pending",
        },
    )
    write_fake_stage_provenance(lineage_root, "mandate")


def _confirmed_csf_data_ready_draft() -> dict:
    return {
        "groups": {
            "panel_contract": {
                "confirmed": True,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "cross_section_time_key": "date",
                    "asset_key": "asset",
                    "universe_membership_rule": "Use the frozen mandate universe snapshot per date.",
                },
            },
            "taxonomy_contract": {
                "confirmed": True,
                "draft": {
                    "group_taxonomy_reference": "sector_bucket_v1",
                    "group_mapping_rule": "Map every asset into one stable research bucket.",
                    "taxonomy_note": "Group taxonomy stays frozen for downstream group-neutral analysis.",
                },
            },
            "eligibility_contract": {
                "confirmed": True,
                "draft": {
                    "eligibility_base_rule": "Drop dates and assets failing minimum liquidity and coverage.",
                    "coverage_floor_rule": "Require 95% panel coverage before downstream factor computation.",
                    "mask_audit_note": "Eligibility stays separate from factor-specific missingness.",
                },
            },
            "shared_feature_base": {
                "confirmed": True,
                "draft": {
                    "shared_feature_outputs": ["returns_panel", "liquidity_panel", "beta_inputs"],
                    "shared_feature_note": "Shared base stops before thesis-specific factor logic.",
                },
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
            },
        }
    }


def test_materialize_stage_program_for_csf_data_ready_is_valid(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"

    program_dir = materialize_stage_program(lineage_root, "csf_data_ready")

    assert program_dir == lineage_root / "program/cross_sectional_factor/data_ready"
    inspection = inspect_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
    assert inspection.program_contract_status == "valid"
    validated = validate_stage_program(lineage_root, "data_ready", "cross_sectional_factor")
    assert validated.entrypoint == "run_stage.py"
    assert validated.route == "cross_sectional_factor"
    assert validated.stage_id == "data_ready"


def test_run_research_session_auto_generates_and_runs_csf_data_ready_program(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt"
    _prepare_mandate_ready_for_csf(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    (stage_dir / "author" / "draft").mkdir(parents=True, exist_ok=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _confirmed_csf_data_ready_draft())
    _write_yaml(
        stage_dir / "author" / "draft" / "data_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_alt",
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-04-07T08:10:00Z",
            "source_stage": "mandate_review_complete",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt")

    assert (lineage_root / "program/cross_sectional_factor/data_ready/stage_program.yaml").exists()
    assert (lineage_root / "program/cross_sectional_factor/data_ready/run_stage.py").exists()
    assert (stage_dir / "author" / "formal" / "panel_manifest.json").exists()
    assert (stage_dir / "author" / "formal" / "run_manifest.json").exists()
    assert status.current_stage == "csf_data_ready_review_confirmation_pending"


def test_run_research_session_does_not_autogenerate_csf_program_before_freeze_groups_confirmed(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt"
    _prepare_mandate_ready_for_csf(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt")

    assert status.current_stage == "csf_data_ready_confirmation_pending"
    assert not (lineage_root / "program/cross_sectional_factor/data_ready").exists()


def test_run_research_session_surfaces_invalid_generated_csf_program_without_advancing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import runtime.tools.research_session as research_session

    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt"
    _prepare_mandate_ready_for_csf(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    (stage_dir / "author" / "draft").mkdir(parents=True, exist_ok=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _confirmed_csf_data_ready_draft())
    _write_yaml(
        stage_dir / "author" / "draft" / "data_ready_transition_approval.yaml",
        {
            "lineage_id": "btc_alt",
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-04-07T08:10:00Z",
            "source_stage": "mandate_review_complete",
        },
    )

    def _broken_generator(*args, **kwargs):  # type: ignore[no-untyped-def]
        program_dir = lineage_root / "program/cross_sectional_factor/data_ready"
        program_dir.mkdir(parents=True, exist_ok=True)
        (program_dir / "stage_program.yaml").write_text("stage_id: wrong\n", encoding="utf-8")
        return program_dir

    monkeypatch.setattr(research_session, "materialize_stage_program", _broken_generator)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt")

    assert status.current_stage == "csf_data_ready_author"
    assert status.blocking_reason_code == "STAGE_PROGRAM_INVALID"
