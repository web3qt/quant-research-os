from pathlib import Path


def test_readme_foregrounds_summary_role_priorities() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    readme_en = Path("README_EN.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, readme_en])

    assert "00_idea_intake -> 00_mandate" in combined
    assert "cross_sectional_factor" in combined
    assert "framework repo" in readme_en
    assert "框架仓" in readme
    assert "qros-research-session" in combined
