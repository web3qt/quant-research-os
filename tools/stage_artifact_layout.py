from __future__ import annotations

from pathlib import Path


def stage_author_layout(stage_root: Path) -> dict[str, Path]:
    root = stage_root.resolve()
    author_dir = root / "author"
    return {
        "stage_root": root,
        "author_dir": author_dir,
        "author_draft_dir": author_dir / "draft",
        "author_formal_dir": author_dir / "formal",
    }


def ensure_stage_author_layout(stage_root: Path) -> dict[str, Path]:
    layout = stage_author_layout(stage_root)
    layout["stage_root"].mkdir(parents=True, exist_ok=True)
    layout["author_dir"].mkdir(parents=True, exist_ok=True)
    layout["author_draft_dir"].mkdir(parents=True, exist_ok=True)
    layout["author_formal_dir"].mkdir(parents=True, exist_ok=True)
    return layout
