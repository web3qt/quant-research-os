from __future__ import annotations

from pathlib import Path
from typing import Any


def infer_review_context(path: Path) -> dict[str, Any]:
    candidate = path.resolve()

    for current in (candidate, *candidate.parents):
        if current.parent.parent.name == "outputs":
            return {
                "lineage_id": current.parent.name,
                "stage": current.name,
                "stage_dir": current,
                "lineage_root": current.parent,
            }

    raise ValueError(f"Could not infer review context from path: {path}")
