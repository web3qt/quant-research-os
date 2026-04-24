from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.idea_runtime import scaffold_idea_intake


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_validate_stage_artifacts_accepts_scaffolded_idea_intake(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is True
    assert result.errors == []


def test_validate_stage_artifacts_reports_missing_required_artifact(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    (intake_dir / "scope_canvas.yaml").unlink()

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "scope_canvas.yaml: missing required artifact" in result.errors


def test_validate_stage_artifacts_reports_yaml_type_mismatch(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "scope_canvas.yaml").read_text(encoding="utf-8"))
    payload["budget_days"] = "ten"
    _write_yaml(intake_dir / "scope_canvas.yaml", payload)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "scope_canvas.yaml: budget_days expected integer, found str" in result.errors


def test_validate_stage_artifacts_reports_unknown_top_level_yaml_field(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    payload = yaml.safe_load((intake_dir / "idea_gate_decision.yaml").read_text(encoding="utf-8"))
    payload["uncontracted_field"] = "leak"
    _write_yaml(intake_dir / "idea_gate_decision.yaml", payload)

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "idea_gate_decision.yaml: unknown top-level field uncontracted_field" in result.errors


def test_validate_stage_artifacts_reports_missing_markdown_section(tmp_path: Path) -> None:
    from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts

    lineage_root = tmp_path / "outputs" / "btc_alt_transmission_v1"
    intake_dir = scaffold_idea_intake(lineage_root)
    (intake_dir / "observation_hypothesis_map.md").write_text("# Observation Hypothesis Map\n", encoding="utf-8")

    result = validate_stage_artifacts(intake_dir, load_artifact_contract("idea_intake"))

    assert result.valid is False
    assert "observation_hypothesis_map.md: missing markdown section 观察" in result.errors
