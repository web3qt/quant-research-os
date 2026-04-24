from __future__ import annotations

from pathlib import Path

import pytest
import yaml


FIXTURES = Path("tests/agent_eval/fixtures")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_assert_skill_triggered_accepts_expected_skill() -> None:
    from runtime.tools.agent_behavior_eval import assert_skill_triggered, parse_transcript_jsonl

    events = parse_transcript_jsonl(FIXTURES / "fake_agent_success.jsonl")

    assert_skill_triggered(events, "qros-research-session")


def test_assert_skill_triggered_rejects_missing_skill() -> None:
    from runtime.tools.agent_behavior_eval import assert_skill_triggered, parse_transcript_jsonl

    events = parse_transcript_jsonl(FIXTURES / "fake_agent_missing_skill.jsonl")

    with pytest.raises(AssertionError, match="expected skill was not triggered: qros-research-session"):
        assert_skill_triggered(events, "qros-research-session")


def test_assert_no_premature_tool_use_rejects_tools_before_skill() -> None:
    from runtime.tools.agent_behavior_eval import assert_no_premature_tool_use, parse_transcript_jsonl

    events = parse_transcript_jsonl(FIXTURES / "fake_agent_premature_tool.jsonl")

    with pytest.raises(AssertionError, match="premature tool call before qros-idea-intake-author: exec_command"):
        assert_no_premature_tool_use(events, before_skill="qros-idea-intake-author")


def test_runtime_and_artifact_assertions_use_stable_behavior_signals(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import (
        assert_artifacts_absent,
        assert_artifacts_present,
        assert_runtime_status,
    )

    lineage_root = tmp_path / "outputs" / "btc_alt"
    (lineage_root / "00_idea_intake").mkdir(parents=True)
    _write_yaml(lineage_root / "00_idea_intake" / "scope_canvas.yaml", {"market": ""})

    assert_runtime_status({"current_stage": "idea_intake_confirmation_pending"}, current_stage="idea_intake_confirmation_pending")
    assert_artifacts_present(lineage_root, ["00_idea_intake/scope_canvas.yaml"])
    assert_artifacts_absent(lineage_root, ["01_mandate/author/formal/mandate.md"])

    with pytest.raises(AssertionError, match="artifact should be absent"):
        assert_artifacts_absent(lineage_root, ["00_idea_intake/scope_canvas.yaml"])
