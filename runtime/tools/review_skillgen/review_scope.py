from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


def normalize_review_path(path: str) -> str:
    raw = str(path).strip().replace("\\", "/")
    if not raw:
        raise ValueError("review path must be non-empty")
    if raw.startswith("/"):
        raise ValueError("review path must be relative")
    normalized = PurePosixPath(raw).as_posix().rstrip("/")
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ValueError("review path must not contain parent traversal")
    if normalized in {"", "."}:
        raise ValueError("review path must identify a file or directory")
    return normalized


def normalize_review_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({normalize_review_path(path) for path in paths}))


@dataclass(frozen=True)
class ReviewScope:
    stage_id: str
    required_artifact_paths: tuple[str, ...]
    required_provenance_paths: tuple[str, ...]
    stage_content_artifact_paths: tuple[str, ...]
    stage_content_provenance_paths: tuple[str, ...]
    upstream_binding_artifact_paths: tuple[str, ...]
    upstream_binding_provenance_paths: tuple[str, ...]
    required_program_dir: str
    required_program_entrypoint: str

    def normalized(self) -> "ReviewScope":
        return ReviewScope(
            stage_id=self.stage_id,
            required_artifact_paths=normalize_review_paths(self.required_artifact_paths),
            required_provenance_paths=normalize_review_paths(self.required_provenance_paths),
            stage_content_artifact_paths=normalize_review_paths(self.stage_content_artifact_paths),
            stage_content_provenance_paths=normalize_review_paths(self.stage_content_provenance_paths),
            upstream_binding_artifact_paths=normalize_review_paths(self.upstream_binding_artifact_paths),
            upstream_binding_provenance_paths=normalize_review_paths(self.upstream_binding_provenance_paths),
            required_program_dir=normalize_review_path(self.required_program_dir),
            required_program_entrypoint=normalize_review_path(self.required_program_entrypoint),
        )

    def required_digest_paths(self) -> tuple[str, ...]:
        normalized = self.normalized()
        return normalized.required_artifact_paths + normalized.required_provenance_paths
