from pathlib import Path

import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.research_session import run_research_session
from tests.helpers.lineage_program_support import write_fake_stage_provenance


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_csf_stage_without_program(lineage_root: Path) -> None:
    mandate_formal_dir = lineage_root / "01_mandate" / "author" / "formal"
    mandate_closure_dir = lineage_root / "01_mandate" / "review" / "closure"
    mandate_formal_dir.mkdir(parents=True, exist_ok=True)
    mandate_closure_dir.mkdir(parents=True, exist_ok=True)

    for name in [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]:
        (mandate_formal_dir / name).write_text("ok\n", encoding="utf-8")

    _write_yaml(
        mandate_formal_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "short_only_rank",
            "neutralization_policy": "none",
        },
    )
    _write_yaml(
        mandate_closure_dir / "stage_completion_certificate.yaml",
        {"stage_status": "PASS", "final_verdict": "PASS"},
    )
    _write_yaml(
        lineage_root / "01_mandate" / "author" / "draft" / "next_stage_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "decision": "CONFIRM_NEXT_STAGE",
            "approved_by": "tester",
            "approved_at": "2026-04-22T09:00:00Z",
            "source_stage": "mandate_next_stage_confirmation_pending",
        },
    )
    _write_yaml(
        lineage_root / "02_csf_data_ready" / "author" / "draft" / "csf_data_ready_freeze_draft.yaml",
        {
            "groups": {
                "panel_contract": {
                    "confirmed": True,
                    "draft": {
                        "panel_primary_key": ["date", "asset"],
                        "cross_section_time_key": "date",
                        "asset_key": "asset",
                        "universe_membership_rule": "use frozen universe",
                    },
                    "missing_items": [],
                },
                "taxonomy_contract": {
                    "confirmed": True,
                    "draft": {
                        "group_taxonomy_reference": "",
                        "group_mapping_rule": "not_applicable",
                        "taxonomy_note": "not_applicable",
                    },
                    "missing_items": [],
                },
                "eligibility_contract": {
                    "confirmed": True,
                    "draft": {
                        "eligibility_base_rule": "min liquidity",
                        "coverage_floor_rule": "0.95",
                        "mask_audit_note": "keep separate",
                    },
                    "missing_items": [],
                },
                "shared_feature_base": {
                    "confirmed": True,
                    "draft": {
                        "shared_feature_outputs": ["returns_panel"],
                        "shared_feature_note": "shared only",
                    },
                    "missing_items": [],
                },
                "delivery_contract": {
                    "confirmed": True,
                    "draft": {
                        "machine_artifacts": ["panel_manifest.json"],
                        "consumer_stage": "csf_signal_ready",
                        "frozen_inputs_note": "downstream reads frozen outputs",
                    },
                    "missing_items": [],
                },
            }
        },
    )
    _write_yaml(
        lineage_root / "02_csf_data_ready" / "author" / "draft" / "data_ready_transition_approval.yaml",
        {
            "lineage_id": lineage_root.name,
            "decision": "CONFIRM_DATA_READY",
            "approved_by": "tester",
            "approved_at": "2026-04-22T09:01:00Z",
            "source_stage": "mandate_review_complete",
        },
    )
    write_fake_stage_provenance(lineage_root, "mandate")


def test_run_research_session_stops_at_stage_program_missing_for_csf_data_ready(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_alt_k"
    _prepare_csf_stage_without_program(lineage_root)

    status = run_research_session(outputs_root=outputs_root, lineage_id="btc_alt_k")

    assert status.current_stage == "csf_data_ready_author"
    assert status.blocking_reason_code == "STAGE_PROGRAM_MISSING"
    assert status.required_program_dir == "program/cross_sectional_factor/data_ready"
    assert "program/cross_sectional_factor/data_ready" in status.next_action
    assert not (lineage_root / "program" / "cross_sectional_factor" / "data_ready").exists()
