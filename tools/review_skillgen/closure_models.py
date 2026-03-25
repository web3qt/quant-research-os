from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ALLOWED_VERDICTS = {
    "PASS",
    "CONDITIONAL PASS",
    "PASS FOR RETRY",
    "RETRY",
    "NO-GO",
    "GO",
    "CHILD LINEAGE",
}


def _normalize_list(items: list[str] | None) -> list[str]:
    if not items:
        return []
    return list(items)


def build_review_payload(
    *,
    lineage_id: str,
    stage: str,
    final_verdict: str,
    stage_status: str,
    blocking_findings: list[str] | None = None,
    reservation_findings: list[str] | None = None,
    info_findings: list[str] | None = None,
    residual_risks: list[str] | None = None,
    review_timestamp_utc: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    if final_verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"Unsupported verdict: {final_verdict}")

    payload: dict[str, Any] = {
        "lineage_id": lineage_id,
        "stage": stage,
        "final_verdict": final_verdict,
        "stage_status": stage_status,
        "blocking_findings": _normalize_list(blocking_findings),
        "reservation_findings": _normalize_list(reservation_findings),
        "info_findings": _normalize_list(info_findings),
        "residual_risks": _normalize_list(residual_risks),
        "review_timestamp_utc": review_timestamp_utc or datetime.now(timezone.utc).isoformat(),
    }
    payload.update(extra)
    return payload
