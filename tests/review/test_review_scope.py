from __future__ import annotations

import pytest

from runtime.tools.review_skillgen.review_scope import (
    ReviewScope,
    normalize_review_path,
    normalize_review_paths,
)


def test_normalize_review_path_removes_trailing_slash() -> None:
    assert normalize_review_path("shared_feature_base/") == "shared_feature_base"


def test_normalize_review_paths_sorts_and_deduplicates() -> None:
    assert normalize_review_paths(["run_manifest.json", "panel_manifest.json", "run_manifest.json"]) == (
        "panel_manifest.json",
        "run_manifest.json",
    )


def test_normalize_review_path_rejects_parent_escape() -> None:
    with pytest.raises(ValueError, match="review path must not contain parent traversal"):
        normalize_review_path("../author/formal/run_manifest.json")


def test_normalize_review_path_rejects_non_string_input() -> None:
    with pytest.raises(ValueError, match="review path must be a string"):
        normalize_review_path(123)  # type: ignore[arg-type]


@pytest.mark.parametrize("path", ["", "   "])
def test_normalize_review_path_rejects_empty_path(path: str) -> None:
    with pytest.raises(ValueError, match="review path must be non-empty"):
        normalize_review_path(path)


def test_normalize_review_path_rejects_dot_path() -> None:
    with pytest.raises(ValueError, match="review path must identify a file or directory"):
        normalize_review_path(".")


def test_normalize_review_path_rejects_absolute_posix_path() -> None:
    with pytest.raises(ValueError, match="review path must be relative"):
        normalize_review_path("/tmp/artifact.yaml")


def test_normalize_review_path_rejects_backslash_parent_traversal() -> None:
    with pytest.raises(ValueError, match="review path must not contain parent traversal"):
        normalize_review_path(r"author\..\formal\run_manifest.json")


@pytest.mark.parametrize("path", [r"C:\tmp\artifact.yaml", "C:/tmp/artifact.yaml"])
def test_normalize_review_path_rejects_windows_absolute_path(path: str) -> None:
    with pytest.raises(ValueError, match="review path must be relative"):
        normalize_review_path(path)


def test_review_scope_compares_paths_as_sets() -> None:
    left = ReviewScope(
        stage_id="csf_data_ready",
        required_artifact_paths=("shared_feature_base/", "panel_manifest.json"),
        required_provenance_paths=("program_execution_manifest.json",),
        stage_content_artifact_paths=("panel_manifest.json", "shared_feature_base"),
        stage_content_provenance_paths=("program_execution_manifest.json",),
        upstream_binding_artifact_paths=(),
        upstream_binding_provenance_paths=(),
        required_program_dir="program/cross_sectional_factor/data_ready",
        required_program_entrypoint="run_stage.py",
    )
    right = ReviewScope(
        stage_id="csf_data_ready",
        required_artifact_paths=("panel_manifest.json", "shared_feature_base"),
        required_provenance_paths=("program_execution_manifest.json",),
        stage_content_artifact_paths=("shared_feature_base/", "panel_manifest.json"),
        stage_content_provenance_paths=("program_execution_manifest.json",),
        upstream_binding_artifact_paths=(),
        upstream_binding_provenance_paths=(),
        required_program_dir="program/cross_sectional_factor/data_ready",
        required_program_entrypoint="run_stage.py",
    )

    assert left.normalized() == right.normalized()


def test_required_digest_paths_preserves_artifacts_then_provenance_order() -> None:
    scope = ReviewScope(
        stage_id="csf_data_ready",
        required_artifact_paths=("z_artifact.json", "a_artifact.json", "z_artifact.json"),
        required_provenance_paths=("b_provenance.json", "a_provenance.json"),
        stage_content_artifact_paths=(),
        stage_content_provenance_paths=(),
        upstream_binding_artifact_paths=(),
        upstream_binding_provenance_paths=(),
        required_program_dir="program/cross_sectional_factor/data_ready",
        required_program_entrypoint="run_stage.py",
    )

    assert scope.required_digest_paths() == (
        "a_artifact.json",
        "z_artifact.json",
        "a_provenance.json",
        "b_provenance.json",
    )
