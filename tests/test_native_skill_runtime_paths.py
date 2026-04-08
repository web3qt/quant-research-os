from pathlib import Path

from tests.skill_test_utils import skill_text


def test_public_skills_reference_repo_local_wrappers() -> None:
    session_skill = skill_text("qros-research-session")
    review_skill = skill_text("qros-mandate-review")

    assert "~/.qros/bin/qros-session" in session_skill
    assert "~/.qros/bin/qros-review" in review_skill
    assert "python scripts/run_research_session.py" not in session_skill
    assert "python scripts/run_stage_review.py" not in review_skill


def test_repo_local_wrappers_exist() -> None:
    assert Path("bin/qros-session").exists()
    assert Path("bin/qros-review").exists()
