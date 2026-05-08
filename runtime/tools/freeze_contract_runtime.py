from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


OPTIONAL_EMPTY_DRAFT_KEYS = {
    "target_strategy_reference",
    "group_taxonomy_reference",
    "success_criteria",
    "failure_criteria",
    "excluded_scope",
    "excluded_topics",
    "rejected_param_ids",
    "rejected_variant_ids",
    "component_factor_ids",
}


def freeze_draft_digest(draft: dict[str, Any]) -> str:
    canonical = json.dumps(draft, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_freeze_draft_payload(draft_path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def freeze_group_invalid_reason(group_payload: dict[str, Any]) -> str | None:
    draft = group_payload.get("draft")
    if not isinstance(draft, dict):
        return "freeze draft incomplete: draft mapping missing"
    incomplete_paths = _incomplete_draft_paths(draft, ())
    if incomplete_paths:
        return f"freeze draft incomplete: {', '.join(incomplete_paths)}"

    missing_items = group_payload.get("missing_items", [])
    if isinstance(missing_items, list) and missing_items:
        return "freeze draft incomplete: missing_items not resolved"
    if missing_items not in (None, []) and not isinstance(missing_items, list):
        return "freeze draft incomplete: missing_items must be a list"

    if bool(group_payload.get("confirmed")):
        expected_digest = str(group_payload.get("freeze_digest_sha256", "")).strip()
        if not expected_digest:
            return "freeze draft missing freeze digest"
        current_digest = freeze_draft_digest(draft)
        if expected_digest != current_digest:
            return "freeze draft changed after confirmation"
    return None


def first_unconfirmed_or_invalid_group(
    draft_path: Path,
    group_order: list[str] | tuple[str, ...],
) -> str | None:
    if not draft_path.exists():
        return group_order[0] if group_order else None

    payload = read_freeze_draft_payload(draft_path)
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return group_order[0] if group_order else None

    for name in group_order:
        group_payload = groups.get(name)
        if not isinstance(group_payload, dict):
            return name
        if not bool(group_payload.get("confirmed")):
            return name
        if freeze_group_invalid_reason(group_payload) is not None:
            return name
    return None


def confirm_all_freeze_groups(
    draft_path: Path,
    group_order: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    payload = read_freeze_draft_payload(draft_path)
    groups = payload.get("groups")
    if not isinstance(groups, dict):
        raise ValueError(f"{draft_path.name} must contain a groups mapping")

    missing_groups = [name for name in group_order if not isinstance(groups.get(name), dict)]
    if missing_groups:
        raise ValueError(f"{draft_path.name} missing freeze groups: {', '.join(missing_groups)}")

    for name in group_order:
        group_payload = groups[name]
        reason = freeze_group_invalid_reason(group_payload)
        if reason is not None and (
            "missing freeze digest" not in reason
            and "changed after confirmation" not in reason
        ):
            raise ValueError(f"{draft_path.name} {name}: {reason}")
        draft = group_payload["draft"]
        group_payload["confirmed"] = True
        group_payload["freeze_digest_sha256"] = freeze_draft_digest(draft)

    return payload


def require_confirmed_freeze_groups(
    draft_path: Path,
    group_order: list[str] | tuple[str, ...],
    *,
    stage_label: str,
) -> dict[str, Any]:
    if not draft_path.exists():
        raise ValueError(f"{draft_path.name} is required before {stage_label} build")

    payload = read_freeze_draft_payload(draft_path)
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        raise ValueError(f"{draft_path.name} must contain a groups mapping")

    for name in group_order:
        group_payload = groups.get(name)
        if not isinstance(group_payload, dict):
            raise ValueError(f"{draft_path.name} missing freeze group: {name}")
        if not bool(group_payload.get("confirmed")):
            raise ValueError(f"{draft_path.name} has unconfirmed groups: {name}")
        reason = freeze_group_invalid_reason(group_payload)
        if reason is not None:
            raise ValueError(f"{draft_path.name} {name}: {reason}")
    return groups


def validate_confirmed_freeze_groups(
    draft_path: Path,
    group_order: list[str] | tuple[str, ...],
) -> None:
    require_confirmed_freeze_groups(draft_path, group_order, stage_label="stage")


def _incomplete_draft_paths(value: Any, path: tuple[str, ...]) -> list[str]:
    key = path[-1] if path else ""
    path_label = ".".join(path) if path else "draft"
    if key in OPTIONAL_EMPTY_DRAFT_KEYS and _is_empty(value):
        return []
    if isinstance(value, dict):
        if not value:
            return [path_label]
        missing: list[str] = []
        for child_key, child_value in value.items():
            missing.extend(_incomplete_draft_paths(child_value, (*path, str(child_key))))
        return missing
    if isinstance(value, list):
        if not value:
            return [path_label]
        missing = []
        for index, item in enumerate(value):
            missing.extend(_incomplete_draft_paths(item, (*path, str(index))))
        return missing
    if value is None:
        return [path_label]
    if isinstance(value, str) and not value.strip():
        return [path_label]
    return []


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False
