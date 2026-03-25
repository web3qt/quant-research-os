from pathlib import Path

import pytest

from tools.review_skillgen.context_inference import infer_review_context


def test_infer_review_context_from_outputs_tree() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = repo_root / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    try:
        ctx = infer_review_context(stage_dir)

        assert ctx["lineage_id"] == "topic_a"
        assert ctx["stage"] == "mandate"
        assert ctx["stage_dir"] == stage_dir
        assert ctx["lineage_root"] == repo_root / "outputs" / "topic_a"
    finally:
        stage_dir.rmdir()
        stage_dir.parent.rmdir()
        stage_dir.parent.parent.rmdir()


def test_infer_review_context_rejects_non_outputs_path(tmp_path: Path) -> None:
    outside_dir = tmp_path / "scratch" / "topic_a"
    outside_dir.mkdir(parents=True)

    with pytest.raises(ValueError, match="Could not infer review context"):
        infer_review_context(outside_dir)


def test_infer_review_context_rejects_lineage_root_without_stage(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    lineage_root.mkdir(parents=True)

    with pytest.raises(ValueError, match="Could not infer review context"):
        infer_review_context(lineage_root)
