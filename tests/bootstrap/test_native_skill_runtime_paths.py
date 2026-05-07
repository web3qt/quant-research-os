from pathlib import Path

from tests.helpers.skill_test_utils import skill_text


def test_public_skills_reference_repo_local_wrappers() -> None:
    session_skill = skill_text("qros-research-session")
    review_skill = skill_text("qros-mandate-review")
    progress_skill = skill_text("qros-progress")
    diagnostics_skill = skill_text("qros-factor-diagnostics")

    assert "./.qros/bin/qros-session" in session_skill
    assert "./.qros/bin/qros-review" in review_skill
    assert "./.qros/bin/qros-progress" in progress_skill
    assert "./.qros/bin/qros-factor-diagnostics" in diagnostics_skill
    assert "python scripts/run_research_session.py" not in session_skill
    assert "python scripts/run_stage_review.py" not in review_skill
    assert "python runtime/scripts/run_progress.py" not in progress_skill
    assert "python runtime/scripts/run_factor_diagnostics.py" not in diagnostics_skill


def test_repo_local_wrappers_exist() -> None:
    assert Path("runtime/bin/qros-session").exists()
    assert Path("runtime/bin/qros-progress").exists()
    assert Path("runtime/bin/qros-factor-diagnostics").exists()
    assert Path("runtime/bin/qros-audit-reviewer").exists()
    assert Path("runtime/bin/qros-check-stage-entry").exists()
    assert Path("runtime/bin/qros-review-cycle").exists()
    assert Path("runtime/bin/qros-start-review").exists()
    assert Path("runtime/bin/qros-review").exists()
