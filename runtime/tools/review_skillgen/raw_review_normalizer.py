from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.review_skillgen.review_findings import normalize_string_list_field


RAW_OUTCOME_ALIASES = {
    "PASS": "CLOSURE_READY_PASS",
    "APPROVE": "CLOSURE_READY_PASS",
    "PASS_WITH_RESERVATIONS": "CLOSURE_READY_CONDITIONAL_PASS",
}


def normalize_raw_review_payload(
    payload: dict[str, Any],
    *,
    source: str | Path | None = None,
) -> dict[str, Any]:
    outcome = str(payload.get("review_loop_outcome", "")).strip()
    if not outcome:
        location = f"{source}: " if source is not None else ""
        raise ValueError(f"{location}review_loop_outcome must be present")

    normalized_payload = dict(payload)
    normalized_payload["review_loop_outcome"] = RAW_OUTCOME_ALIASES.get(outcome, outcome)

    for key in (
        "blocking_findings",
        "reservation_findings",
        "info_findings",
        "residual_risks",
        "allowed_modifications",
        "downstream_permissions",
    ):
        normalized_payload[key] = normalize_string_list_field(
            normalized_payload.get(key),
            key=key,
            allow_single_string=True,
            source=source,
        )

    return normalized_payload
