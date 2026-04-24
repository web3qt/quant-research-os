from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.idea_runtime import scaffold_idea_intake


def _yaml_top_level_keys(path: Path) -> list[str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(payload)


def test_idea_intake_scaffold_file_tree_matches_artifact_contract(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    contract = load_artifact_contract("idea_intake")

    assert sorted(path.name for path in intake_dir.iterdir()) == sorted(contract["artifacts"])


def test_idea_intake_scaffold_yaml_shape_matches_artifact_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)

    assert _yaml_top_level_keys(intake_dir / "scope_canvas.yaml") == [
        "market",
        "data_source",
        "instrument_type",
        "universe",
        "bar_size",
        "holding_horizons",
        "target_task",
        "excluded_scope",
        "budget_days",
        "max_iterations",
    ]
    assert _yaml_top_level_keys(intake_dir / "qualification_scorecard.yaml") == [
        "idea_id",
        "reviewer_identity",
        "summary",
        "dimensions",
    ]
    assert _yaml_top_level_keys(intake_dir / "idea_gate_decision.yaml") == [
        "idea_id",
        "verdict",
        "why",
        "route_assessment",
        "approved_scope",
        "required_reframe_actions",
        "rollback_target",
    ]
    assert _yaml_top_level_keys(intake_dir / "mandate_freeze_draft.yaml") == ["groups"]


def test_idea_intake_scaffold_passes_artifact_shape_validator(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is True
