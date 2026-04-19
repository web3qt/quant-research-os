from __future__ import annotations

from pathlib import Path


def skill_bundle_dir(skill_name: str, *, root: Path | None = None) -> Path:
    search_root = root or Path("skills")
    matches = sorted(
        {
            skill_md.parent
            for skill_md in search_root.rglob("SKILL.md")
            if skill_md.parent.name == skill_name
        }
    )
    if not matches:
        raise AssertionError(f"missing skill bundle: {skill_name}")
    if len(matches) != 1:
        joined = ", ".join(str(path) for path in matches)
        raise AssertionError(f"ambiguous skill bundle {skill_name}: {joined}")
    return matches[0]


def skill_path(skill_name: str, *, root: Path | None = None) -> Path:
    return skill_bundle_dir(skill_name, root=root) / "SKILL.md"


def skill_text(skill_name: str, *, root: Path | None = None) -> str:
    return skill_path(skill_name, root=root).read_text(encoding="utf-8")
