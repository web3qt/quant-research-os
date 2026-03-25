from pathlib import Path


def test_research_session_skill_exists_and_covers_first_wave_flow() -> None:
    skill_path = Path(".agents/skills/qros-research-session/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "idea_intake" in content
    assert "mandate" in content
    assert "mandate review" in content.lower()
    assert "mandate_confirmation_pending" in content
    assert "CONFIRM_MANDATE" in content
    assert "是否确认进入 mandate" in content
    assert "run_research_session.py" in content


def test_research_session_usage_doc_mentions_single_entry_flow() -> None:
    usage_path = Path("docs/experience/qros-research-session-usage.md")
    content = usage_path.read_text(encoding="utf-8")

    assert usage_path.exists()
    assert "python scripts/run_research_session.py" in content
    assert "qros-research-session" in content
    assert "data_ready" in content
    assert "mandate_confirmation_pending" in content
    assert "用户不需要记住内部命令" in content
    assert "是否确认进入 mandate" in content
