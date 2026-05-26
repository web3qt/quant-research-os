from pathlib import Path

from runtime.tools.review_operations import (
    OP_AWAITING_REVIEWER_COMPLETION,
    OP_REQUEST_REFRESH_REQUIRED,
    OP_REVIEW_NOT_STARTED,
    ReviewOperationSnapshot,
    build_review_operations_snapshot,
)


def test_review_operations_snapshot_for_missing_stage_dir_reports_not_started(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    snapshot = build_review_operations_snapshot(
        lineage_root=lineage_root,
        stage_id="mandate",
        stage_dir=lineage_root / "01_mandate",
        reviewable=True,
    )

    assert isinstance(snapshot, ReviewOperationSnapshot)
    assert snapshot.stage_id == "mandate"
    assert snapshot.review_operation_state == OP_REVIEW_NOT_STARTED
    assert snapshot.request_present is False
    assert snapshot.receipt_present is False
    assert snapshot.final_review_present is False
    assert snapshot.recommended_next_operation is None


def test_review_operation_constants_are_stable() -> None:
    assert OP_REVIEW_NOT_STARTED == "REVIEW_NOT_STARTED"
    assert OP_AWAITING_REVIEWER_COMPLETION == "AWAITING_REVIEWER_COMPLETION"
    assert OP_REQUEST_REFRESH_REQUIRED == "REQUEST_REFRESH_REQUIRED"
