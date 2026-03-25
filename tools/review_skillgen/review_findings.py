from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tools.review_skillgen.closure_models import ALLOWED_VERDICTS


def _normalize_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return [str(item) for item in value]


def load_review_findings(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must load to a mapping")

    recommended_verdict = data.get("recommended_verdict")
    if recommended_verdict is not None and recommended_verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"Unsupported verdict: {recommended_verdict}")

    return {
        "reviewer_identity": str(data.get("reviewer_identity", "codex")),
        "recommended_verdict": recommended_verdict,
        "blocking_findings": _normalize_list(data, "blocking_findings"),
        "reservation_findings": _normalize_list(data, "reservation_findings"),
        "info_findings": _normalize_list(data, "info_findings"),
        "residual_risks": _normalize_list(data, "residual_risks"),
        "allowed_modifications": _normalize_list(data, "allowed_modifications"),
        "downstream_permissions": _normalize_list(data, "downstream_permissions"),
        "rollback_stage": data.get("rollback_stage"),
    }
