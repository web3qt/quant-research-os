from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ReviewBlockingSurface = Literal["semantic_gate", "failure_package"]


@dataclass(frozen=True)
class ReviewEligibilityStatus:
    eligible_for_review: bool
    blocking_reason_code: str | None
    blocking_reason: str | None
    review_blocking_surface: ReviewBlockingSurface | None
    authorized_review_skill: str | None
    requires_failure_handling: bool
    failure_stage: str | None
    failure_reason_summary: str | None


def compute_review_eligibility(
    *,
    lineage_root: Path,
    current_stage: str,
    review_skill: str,
) -> ReviewEligibilityStatus:
    truth_path = lineage_root / "review_eligibility.json"
    if not truth_path.exists():
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="REVIEW_ELIGIBILITY_UNDECLARED",
            blocking_reason=f"Missing canonical review eligibility truth: {truth_path}",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )

    try:
        payload = json.loads(truth_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="MALFORMED_REVIEW_ELIGIBILITY_JSON",
            blocking_reason=f"Invalid JSON in canonical review eligibility truth: {truth_path}",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )
    if not isinstance(payload, dict):
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="MALFORMED_REVIEW_ELIGIBILITY_PAYLOAD",
            blocking_reason="Canonical review eligibility truth must be a JSON object.",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )

    failure_package = payload.get("failure_package")
    if failure_package is not None:
        if not isinstance(failure_package, dict):
            return ReviewEligibilityStatus(
                eligible_for_review=False,
                blocking_reason_code="MALFORMED_FAILURE_PACKAGE",
                blocking_reason="failure_package must be an object.",
                review_blocking_surface="failure_package",
                authorized_review_skill=None,
                requires_failure_handling=True,
                failure_stage=current_stage,
                failure_reason_summary="failure_package must be an object.",
            )
        reason_code_value = failure_package.get("reason_code")
        reason_value = failure_package.get("reason")
        if reason_code_value is None or reason_value is None:
            return ReviewEligibilityStatus(
                eligible_for_review=False,
                blocking_reason_code="MALFORMED_FAILURE_PACKAGE",
                blocking_reason="failure_package must include reason_code and reason.",
                review_blocking_surface="failure_package",
                authorized_review_skill=None,
                requires_failure_handling=True,
                failure_stage=str(failure_package.get("stage") or current_stage),
                failure_reason_summary=str(
                    failure_package.get("failure_reason_summary")
                    or failure_package.get("reason")
                    or "failure_package must include reason_code and reason."
                ),
            )
        reason_code = str(reason_code_value)
        reason = str(reason_value)
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code=reason_code,
            blocking_reason=reason,
            review_blocking_surface="failure_package",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage=str(failure_package.get("stage") or current_stage),
            failure_reason_summary=str(
                failure_package.get("failure_reason_summary") or reason
            ),
        )

    semantic_gate = payload.get("semantic_gate")
    if not isinstance(semantic_gate, dict):
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code="REVIEW_ELIGIBILITY_UNDECLARED",
            blocking_reason="Missing semantic_gate review eligibility truth.",
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=False,
            failure_stage=None,
            failure_reason_summary=None,
        )

    semantic_status = str(semantic_gate.get("status"))
    semantic_reason_code = semantic_gate.get("reason_code")
    semantic_reason = semantic_gate.get("reason")
    if semantic_status != "pass":
        reason_code = str(semantic_reason_code or "REVIEW_SEMANTIC_GATE_FAIL")
        reason = str(semantic_reason or "Semantic gate failed.")
        return ReviewEligibilityStatus(
            eligible_for_review=False,
            blocking_reason_code=reason_code,
            blocking_reason=reason,
            review_blocking_surface="semantic_gate",
            authorized_review_skill=None,
            requires_failure_handling=True,
            failure_stage=current_stage,
            failure_reason_summary=reason,
        )

    return ReviewEligibilityStatus(
        eligible_for_review=True,
        blocking_reason_code=None,
        blocking_reason=None,
        review_blocking_surface=None,
        authorized_review_skill=review_skill,
        requires_failure_handling=False,
        failure_stage=None,
        failure_reason_summary=None,
    )
