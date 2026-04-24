from __future__ import annotations

from pathlib import Path

import yaml


FIXTURES = Path("tests/agent_eval/fixtures")


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_evaluate_behavior_case_passes_with_fake_success_transcript(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, load_eval_cases, parse_transcript_jsonl

    case = load_eval_cases(Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml"))[
        "naive_raw_idea_triggers_research_session"
    ]
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    (lineage_root / "00_idea_intake").mkdir(parents=True)
    _write_yaml(lineage_root / "00_idea_intake" / "scope_canvas.yaml", {"market": ""})

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_agent_success.jsonl"),
        lineage_root=lineage_root,
        runtime_status={"current_stage": "idea_intake_confirmation_pending"},
    )

    assert result.passed is True
    assert result.errors == []


def test_evaluate_behavior_case_fails_on_premature_tool_use(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, load_eval_cases, parse_transcript_jsonl

    case = load_eval_cases(Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml"))[
        "explicit_idea_intake_author_skill_first"
    ]
    lineage_root = tmp_path / "outputs" / case["lineage_id"]

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_agent_premature_tool.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "premature tool call before qros-idea-intake-author: exec_command" in result.errors


def test_evaluate_behavior_case_catches_premature_mandate_artifact(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import evaluate_behavior_case, load_eval_cases, parse_transcript_jsonl

    case = load_eval_cases(Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml"))[
        "no_confirmation_no_mandate_formal_artifacts"
    ]
    lineage_root = tmp_path / "outputs" / case["lineage_id"]
    (lineage_root / "01_mandate" / "author" / "formal").mkdir(parents=True)
    (lineage_root / "01_mandate" / "author" / "formal" / "mandate.md").write_text("premature\n", encoding="utf-8")

    result = evaluate_behavior_case(
        case,
        parse_transcript_jsonl(FIXTURES / "fake_agent_success.jsonl"),
        lineage_root=lineage_root,
    )

    assert result.passed is False
    assert "artifact should be absent: 01_mandate/author/formal/mandate.md" in result.errors
