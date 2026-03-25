from pathlib import Path


def test_project_bootstrap_files_exist() -> None:
    assert Path("pyproject.toml").exists()
    assert Path("tools/review_skillgen/__init__.py").exists()


def test_usage_doc_exists() -> None:
    assert Path("docs/experience/codex-stage-review-skill-usage.md").exists()
