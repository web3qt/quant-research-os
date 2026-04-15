import pytest

from runtime.tools.review_skillgen.closure_models import ALLOWED_VERDICTS, build_review_payload


def test_build_review_payload_requires_stage_and_verdict() -> None:
    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    assert payload["lineage_id"] == "topic_a"
    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
    assert payload["stage_status"] == "PASS"
    assert payload["blocking_findings"] == []
    assert payload["reservation_findings"] == []
    assert payload["info_findings"] == []
    assert payload["residual_risks"] == []
    assert isinstance(payload["review_timestamp_utc"], str)


def test_build_review_payload_rejects_unknown_verdict() -> None:
    with pytest.raises(ValueError, match="Unsupported verdict"):
        build_review_payload(
            lineage_id="topic_a",
            stage="mandate",
            final_verdict="MAYBE",
            stage_status="PASS",
        )


def test_allowed_verdicts_include_current_shared_vocabulary() -> None:
    assert ALLOWED_VERDICTS == {
        "PASS",
        "CONDITIONAL PASS",
        "PASS FOR RETRY",
        "RETRY",
        "NO-GO",
        "GO",
        "CHILD LINEAGE",
    }
