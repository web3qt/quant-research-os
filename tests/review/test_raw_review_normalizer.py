from __future__ import annotations

import pytest

from runtime.tools.review_skillgen.raw_review_normalizer import normalize_raw_review_payload


def test_normalize_raw_review_payload_converts_pass_alias_to_canonical_outcome() -> None:
    payload = normalize_raw_review_payload({"review_loop_outcome": "PASS"})

    assert payload["review_loop_outcome"] == "CLOSURE_READY_PASS"


def test_normalize_raw_review_payload_converts_approve_alias_to_canonical_outcome() -> None:
    payload = normalize_raw_review_payload({"review_loop_outcome": "APPROVE"})

    assert payload["review_loop_outcome"] == "CLOSURE_READY_PASS"


def test_normalize_raw_review_payload_converts_pass_with_reservations_alias_to_canonical_outcome() -> None:
    payload = normalize_raw_review_payload({"review_loop_outcome": "PASS_WITH_RESERVATIONS"})

    assert payload["review_loop_outcome"] == "CLOSURE_READY_CONDITIONAL_PASS"


def test_normalize_raw_review_payload_normalizes_string_and_empty_findings_fields() -> None:
    payload = normalize_raw_review_payload(
        {
            "review_loop_outcome": "PASS",
            "blocking_findings": "",
            "reservation_findings": "watch liquidity drift",
            "info_findings": ["shape ok"],
            "residual_risks": None,
            "allowed_modifications": "",
            "downstream_permissions": ["mandate_next_stage_confirmation_pending"],
        }
    )

    assert payload["blocking_findings"] == []
    assert payload["reservation_findings"] == ["watch liquidity drift"]
    assert payload["info_findings"] == ["shape ok"]
    assert payload["residual_risks"] == []
    assert payload["allowed_modifications"] == []
    assert payload["downstream_permissions"] == ["mandate_next_stage_confirmation_pending"]


def test_normalize_raw_review_payload_rejects_missing_core_outcome() -> None:
    with pytest.raises(ValueError, match="review_loop_outcome"):
        normalize_raw_review_payload({"blocking_findings": []})


def test_normalize_raw_review_payload_rejects_mixed_type_findings_lists() -> None:
    with pytest.raises(ValueError, match="blocking_findings"):
        normalize_raw_review_payload(
            {
                "review_loop_outcome": "PASS",
                "blocking_findings": [123, True, None],
            }
        )
