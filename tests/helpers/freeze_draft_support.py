from __future__ import annotations

from typing import Any

from runtime.tools.freeze_contract_runtime import freeze_draft_digest


def with_freeze_digests(payload: dict[str, Any]) -> dict[str, Any]:
    groups = payload.get("groups")
    if not isinstance(groups, dict):
        return payload
    for group in groups.values():
        if not isinstance(group, dict) or not bool(group.get("confirmed")):
            continue
        if group.get("freeze_digest_sha256"):
            continue
        draft = group.get("draft")
        if isinstance(draft, dict):
            group["freeze_digest_sha256"] = freeze_draft_digest(draft)
    return payload
