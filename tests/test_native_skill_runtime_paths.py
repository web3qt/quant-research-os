from pathlib import Path


def test_public_skills_reference_repo_local_wrappers() -> None:
    session_skill = Path("skills/qros-research-session/SKILL.md").read_text(encoding="utf-8")
    review_skill = Path("skills/qros-mandate-review/SKILL.md").read_text(encoding="utf-8")

    assert "~/.qros/bin/qros-session" in session_skill
    assert "~/.qros/bin/qros-review" in review_skill
    assert "python scripts/run_research_session.py" not in session_skill
    assert "python scripts/run_stage_review.py" not in review_skill


def test_repo_local_wrappers_exist() -> None:
    assert Path("bin/qros-session").exists()
    assert Path("bin/qros-review").exists()
