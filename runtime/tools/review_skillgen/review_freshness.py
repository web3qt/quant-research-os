from __future__ import annotations

from pathlib import Path
from typing import Sequence

from runtime.tools.review_skillgen.adversarial_review_contract import ADVERSARIAL_REVIEW_REQUEST_FILENAME


def review_cycle_stale_reason(
    stage_dir: Path,
    *,
    artifact_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str] = ("program_execution_manifest.json",),
) -> str | None:
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    if not request_path.exists():
        return None

    tracked_paths: list[Path] = []
    for name in required_outputs:
        candidate = artifact_root / name
        if candidate.exists():
            tracked_paths.append(candidate)
    for name in required_provenance_paths:
        candidate = artifact_root / name
        if candidate.exists():
            tracked_paths.append(candidate)

    if not tracked_paths:
        return None

    latest_materialized = max(path.stat().st_mtime for path in tracked_paths)
    request_mtime = request_path.stat().st_mtime
    if latest_materialized > request_mtime:
        return (
            "author/formal outputs or provenance changed after adversarial_review_request.yaml was issued; "
            "review cycle is stale"
        )
    return None
