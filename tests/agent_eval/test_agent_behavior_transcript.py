from __future__ import annotations

from pathlib import Path


FIXTURES = Path("tests/agent_eval/fixtures")


def test_parse_transcript_normalizes_skill_and_tool_events() -> None:
    from runtime.tools.agent_behavior_eval import parse_transcript_jsonl

    events = parse_transcript_jsonl(FIXTURES / "fake_agent_success.jsonl")

    assert [(event.event_type, event.name) for event in events] == [
        ("assistant_text", "assistant"),
        ("skill_call", "qros-research-session"),
        ("tool_call", "exec_command"),
    ]


def test_parse_transcript_ignores_unknown_jsonl_lines_with_warning(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import parse_transcript_jsonl

    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            [
                '{"type":"unknown","payload":{"x":1}}',
                "not-json",
                '{"type":"tool_use","name":"Skill","input":{"skill":"qros-progress"}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    events = parse_transcript_jsonl(transcript)

    assert [(event.event_type, event.name) for event in events] == [("skill_call", "qros-progress")]


def test_parse_transcript_normalizes_codex_json_items(tmp_path: Path) -> None:
    from runtime.tools.agent_behavior_eval import parse_transcript_jsonl

    transcript = tmp_path / "codex_transcript.jsonl"
    transcript.write_text(
        "\n".join(
            [
                '{"type":"item.completed","item":{"type":"agent_message","text":"使用 qros-idea-intake-author"}}',
                '{"type":"item.started","item":{"type":"command_execution","command":"/bin/zsh -lc \\"sed -n \'1,240p\' /Users/mac08/.codex/skills/qros-idea-intake-author/SKILL.md\\""}}',
                '{"type":"item.started","item":{"type":"command_execution","command":"ls"}}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    events = parse_transcript_jsonl(transcript)

    assert [(event.event_type, event.name) for event in events] == [
        ("assistant_text", "assistant"),
        ("skill_call", "qros-idea-intake-author"),
        ("tool_call", "command_execution"),
    ]
