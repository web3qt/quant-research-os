from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_agent_behavior_eval_case_contract_exists_and_declares_mvp_cases() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "qros-agent-behavior-eval-cases-v1"
    assert contract["schema_version"] == "v1"
    case_ids = {case["id"] for case in contract["cases"]}
    assert case_ids == {
        "naive_raw_idea_triggers_research_session",
        "explicit_idea_intake_author_skill_first",
        "partial_intake_does_not_go_to_mandate",
        "no_confirmation_no_mandate_formal_artifacts",
        "raw_idea_scaffold_passes_artifact_shape_validator",
    }


def test_agent_behavior_eval_cases_have_stable_behavior_assertions() -> None:
    contract = _load_contract()

    for case in contract["cases"]:
        assert case["prompt"].strip(), case["id"]
        assert case["expected_skill"].startswith("qros-"), case["id"]
        assert case["premature_tool_policy"] == "forbid_before_expected_skill", case["id"]
        assert "lineage_id" in case, case["id"]
        assert isinstance(case.get("expected_artifacts", {}).get("present", []), list), case["id"]
        assert isinstance(case.get("expected_artifacts", {}).get("absent", []), list), case["id"]


def test_agent_behavior_eval_contract_keeps_live_agent_eval_out_of_default_ci() -> None:
    contract = _load_contract()

    assert contract["execution_mode"] == "manual_or_nightly"
    assert contract["default_pytest_behavior"] == "fake_transcripts_only"
    assert contract["requires_agent_command_template"] is True
