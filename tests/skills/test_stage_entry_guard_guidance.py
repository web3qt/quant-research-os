from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _stage_skill_paths(lane: str) -> list[Path]:
    return sorted(
        path
        for path in ROOT.glob(f"skills/*/qros-*-{lane}/SKILL.md")
        if "failure" not in path.parts
    )


def test_stage_author_skills_require_runtime_entry_guard() -> None:
    for path in _stage_skill_paths("author"):
        content = path.read_text(encoding="utf-8")
        assert "## Runtime Stage Admission" in content, path
        assert "./.qros/bin/qros-check-stage-entry" in content, path
        assert "--lane author" in content, path
        assert "不得继续 authoring" in content, path


def test_stage_review_skills_require_runtime_entry_guard() -> None:
    for path in _stage_skill_paths("review"):
        content = path.read_text(encoding="utf-8")
        assert "## Runtime Stage Admission" in content, path
        assert "./.qros/bin/qros-check-stage-entry" in content, path
        assert "--lane review" in content, path
        assert "不得继续 review" in content, path
