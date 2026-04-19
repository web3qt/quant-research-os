from pathlib import Path

import pytest

from runtime.tools.review_skillgen.context_inference import infer_review_context


def test_infer_review_context_from_outputs_tree(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    ctx = infer_review_context(stage_dir)

    assert ctx["lineage_id"] == "topic_a"
    assert ctx["stage"] == "mandate"
    assert ctx["stage_dir"] == stage_dir
    assert ctx["lineage_root"] == tmp_path / "outputs" / "topic_a"


def test_infer_review_context_normalizes_numbered_stage_dirs(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "04_train_freeze"
    stage_dir.mkdir(parents=True)

    ctx = infer_review_context(stage_dir)

    assert ctx["lineage_id"] == "topic_a"
    assert ctx["stage"] == "train_calibration"
    assert ctx["stage_dir"] == stage_dir
    assert ctx["lineage_root"] == tmp_path / "outputs" / "topic_a"


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
