from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/idea_intake_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_idea_intake_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["stage"] == "idea_intake"
    assert contract["stage_dir"] == "00_idea_intake"
    assert contract["schema_id"] == "idea-intake-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["unknown_yaml_top_level_fields"] == "forbid"

    assert set(contract["artifacts"]) == {
        "idea_brief.md",
        "intake_interview.md",
        "observation_hypothesis_map.md",
        "research_question_set.md",
        "artifact_catalog.md",
        "scope_canvas.yaml",
        "qualification_scorecard.yaml",
        "idea_gate_decision.yaml",
        "mandate_freeze_draft.yaml",
    }


def test_idea_intake_contract_locks_scope_canvas_shape() -> None:
    contract = _load_contract()
    scope_canvas = _artifact(contract, "scope_canvas.yaml")

    assert scope_canvas["type"] == "yaml"
    assert scope_canvas["unknown_top_level_fields"] == "forbid"
    assert _field_paths(scope_canvas) == {
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
    }


def test_idea_intake_contract_locks_scorecard_dimensions() -> None:
    contract = _load_contract()
    scorecard = _artifact(contract, "qualification_scorecard.yaml")
    paths = _field_paths(scorecard)

    assert {"idea_id", "reviewer_identity", "summary", "dimensions"}.issubset(paths)
    for dimension in (
        "observability",
        "mechanism_plausibility",
        "tradeability",
        "data_feasibility",
        "scoping_clarity",
        "distinctiveness",
    ):
        assert f"dimensions.{dimension}.score" in paths
        assert f"dimensions.{dimension}.evidence" in paths
        assert f"dimensions.{dimension}.uncertainty" in paths
        assert f"dimensions.{dimension}.kill_reason" in paths


def test_idea_intake_contract_locks_gate_decision_and_freeze_draft_enums() -> None:
    contract = _load_contract()
    gate_decision = _artifact(contract, "idea_gate_decision.yaml")
    freeze_draft = _artifact(contract, "mandate_freeze_draft.yaml")

    verdict_field = next(field for field in gate_decision["fields"] if field["path"] == "verdict")
    assert verdict_field["type"] == "enum"
    assert verdict_field["values"] == ["GO_TO_MANDATE", "NEEDS_REFRAME", "DROP"]

    route_field = next(field for field in gate_decision["fields"] if field["path"] == "route_assessment.recommended_route")
    assert route_field["type"] == "string"
    assert route_field["allowed_values_if_nonempty"] == ["time_series_signal", "cross_sectional_factor"]

    assert set(freeze_draft["groups"]) == {
        "research_intent",
        "scope_contract",
        "data_contract",
        "execution_contract",
    }


def test_idea_intake_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
