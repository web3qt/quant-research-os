from pathlib import Path


def test_readme_foregrounds_summary_role_priorities() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    combined = readme

    assert "00_idea_intake -> 01_mandate" in combined
    assert "cross_sectional_factor" in combined
    assert "框架仓" in readme
    assert "qros-research-session" in combined
