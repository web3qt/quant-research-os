"""Normalize parsed raw final_review.yaml payloads before legacy validation.

This boundary intentionally accepts reviewer-authored raw YAML before
``load_final_review()`` applies its legacy semantic shape checks, so allowed
non-semantic differences such as mapping finding objects can be normalized.
Task 4 callers that need mapping findings must use this normalizer directly on
raw YAML payloads instead of pre-validating through ``load_final_review()``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import ALLOWED_FINAL_REVIEW_VERDICTS
from runtime.tools.review_skillgen.review_scope import normalize_review_path, normalize_review_paths


NORMALIZED_FINAL_REVIEW_FILENAME = "final_review.normalized.yaml"
FORBIDDEN_FINAL_REVIEW_NORMALIZATION = "FORBIDDEN_FINAL_REVIEW_NORMALIZATION"


def _string_list(value: Any, *, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} must be a list")

    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            normalized.append(item)
        elif isinstance(item, Mapping):
            normalized.append(
                json.dumps(
                    item,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        else:
            raise ValueError(
                f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} items must be strings or mappings"
            )
    return normalized


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: {key} must be provided by reviewer")
    return value.strip()


def _required_runtime_string(payload: dict[str, Any], key: str, *, source_name: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source_name} {key} must be a non-empty string")
    return value.strip()


def _expected_stage_content_paths(request_payload: dict[str, Any]) -> tuple[str, ...]:
    paths = request_payload.get("stage_content_artifact_paths")
    if paths is None:
        paths = request_payload.get("required_artifact_paths", [])
    if not isinstance(paths, list):
        raise ValueError("active request scope artifact paths must be a list")
    return normalize_review_paths(paths)


def _expected_program_path(request_payload: dict[str, Any]) -> str:
    program_dir = normalize_review_path(
        _required_runtime_string(
            request_payload,
            "required_program_dir",
            source_name="adversarial_review_request.yaml",
        )
    )
    entrypoint = normalize_review_path(
        _required_runtime_string(
            request_payload,
            "required_program_entrypoint",
            source_name="adversarial_review_request.yaml",
        )
    )
    return normalize_review_path(f"{program_dir}/{entrypoint}")


def _optional_rollback_stage(payload: dict[str, Any]) -> str | None:
    value = payload.get("rollback_stage")
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: rollback_stage must be a string when provided")


def _required_verdict(payload: dict[str, Any]) -> str:
    verdict = _required_string(payload, "verdict")
    if verdict not in ALLOWED_FINAL_REVIEW_VERDICTS:
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: unsupported verdict {verdict!r}")
    return verdict


def normalize_final_review_payload(
    final_review_payload: dict[str, Any],
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> dict[str, Any]:
    request_review_cycle_id = _required_runtime_string(
        request_payload,
        "review_cycle_id",
        source_name="adversarial_review_request.yaml",
    )
    receipt_review_cycle_id = _required_runtime_string(
        receipt_payload,
        "review_cycle_id",
        source_name="reviewer_receipt.yaml",
    )
    if receipt_review_cycle_id != request_review_cycle_id:
        raise ValueError("review_cycle_id does not match reviewer_receipt.yaml")

    request_lineage_id = _required_runtime_string(
        request_payload,
        "lineage_id",
        source_name="adversarial_review_request.yaml",
    )
    request_stage = _required_runtime_string(
        request_payload,
        "stage",
        source_name="adversarial_review_request.yaml",
    )
    reviewer_identity = _required_runtime_string(
        receipt_payload,
        "requested_reviewer_identity",
        source_name="reviewer_receipt.yaml",
    )
    reviewer_agent_id = _required_runtime_string(
        receipt_payload,
        "reviewer_agent_id",
        source_name="reviewer_receipt.yaml",
    )

    if final_review_payload.get("lineage_id") != request_lineage_id:
        raise ValueError("lineage_id does not match adversarial_review_request.yaml")
    if final_review_payload.get("stage_id") != request_stage:
        raise ValueError("stage_id does not match adversarial_review_request.yaml")
    if final_review_payload.get("reviewer_identity") != reviewer_identity:
        raise ValueError("reviewer_identity does not match reviewer_receipt.yaml")
    if final_review_payload.get("reviewer_agent_id") != reviewer_agent_id:
        raise ValueError("reviewer_agent_id does not match reviewer_receipt.yaml")

    expected_program_path = _expected_program_path(request_payload)
    reviewed_program_path = normalize_review_path(_required_string(final_review_payload, "reviewed_program_path"))
    if reviewed_program_path != expected_program_path:
        raise ValueError("reviewed_program_path does not match active request program")

    expected_artifact_paths = _expected_stage_content_paths(request_payload)
    reviewed_artifact_value = final_review_payload.get("reviewed_artifact_paths")
    if not isinstance(reviewed_artifact_value, list):
        raise ValueError(f"{FORBIDDEN_FINAL_REVIEW_NORMALIZATION}: reviewed_artifact_paths must be a list")
    reviewed_artifact_paths = normalize_review_paths(reviewed_artifact_value)
    if reviewed_artifact_paths != expected_artifact_paths:
        raise ValueError("reviewed_artifact_paths do not match active request scope")

    return {
        "review_cycle_id": request_review_cycle_id,
        "lineage_id": request_lineage_id,
        "stage_id": request_stage,
        "author_identity": _required_runtime_string(
            request_payload,
            "author_identity",
            source_name="adversarial_review_request.yaml",
        ),
        "reviewer_identity": reviewer_identity,
        "reviewer_session_id": _required_runtime_string(
            receipt_payload,
            "requested_reviewer_session_id",
            source_name="reviewer_receipt.yaml",
        ),
        "reviewer_agent_id": reviewer_agent_id,
        "reviewer_execution_mode": _required_runtime_string(
            receipt_payload,
            "execution_mode",
            source_name="reviewer_receipt.yaml",
        ),
        "reviewer_context_source": _required_runtime_string(
            receipt_payload,
            "reviewer_context_source",
            source_name="reviewer_receipt.yaml",
        ),
        "reviewer_history_inheritance": _required_runtime_string(
            receipt_payload,
            "reviewer_history_inheritance",
            source_name="reviewer_receipt.yaml",
        ),
        "reviewed_artifact_paths": list(reviewed_artifact_paths),
        "reviewed_program_path": expected_program_path,
        "reviewed_artifact_digest": _required_string(final_review_payload, "reviewed_artifact_digest"),
        "reviewed_program_digest": _required_string(final_review_payload, "reviewed_program_digest"),
        "verdict": _required_verdict(final_review_payload),
        "review_summary": _required_string(final_review_payload, "review_summary"),
        "blocking_findings": _string_list(final_review_payload.get("blocking_findings"), key="blocking_findings"),
        "reservation_findings": _string_list(final_review_payload.get("reservation_findings"), key="reservation_findings"),
        "info_findings": _string_list(final_review_payload.get("info_findings"), key="info_findings"),
        "residual_risks": _string_list(final_review_payload.get("residual_risks"), key="residual_risks"),
        "allowed_modifications": _string_list(
            final_review_payload.get("allowed_modifications"),
            key="allowed_modifications",
        ),
        "rollback_stage": _optional_rollback_stage(final_review_payload),
        "downstream_permissions": _string_list(
            final_review_payload.get("downstream_permissions"),
            key="downstream_permissions",
        ),
        "recommended_next_action": _required_string(final_review_payload, "recommended_next_action"),
    }


def validate_final_review_digest_bindings(
    *,
    normalized_final_review: dict[str, Any],
    request_payload: dict[str, Any],
) -> None:
    bound_author_digest = request_payload.get("bound_author_materialization_digest")
    if not isinstance(bound_author_digest, str) or not bound_author_digest.strip():
        raise ValueError(
            "REVIEW_CONTRACT_CONTEXT_STALE: active request is missing "
            "bound_author_materialization_digest; rerun qros-review-cycle prepare"
        )
    if normalized_final_review.get("reviewed_artifact_digest") != bound_author_digest:
        raise ValueError(
            "REVIEW_CONTRACT_CONTEXT_STALE: reviewed_artifact_digest does not match "
            "bound_author_materialization_digest"
        )

    author_program_hash = request_payload.get("author_program_hash")
    if not isinstance(author_program_hash, str) or not author_program_hash.strip():
        raise ValueError(
            "REVIEW_CONTRACT_CONTEXT_STALE: active request is missing author_program_hash; "
            "rerun qros-review-cycle prepare"
        )
    if normalized_final_review.get("reviewed_program_digest") != author_program_hash:
        raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: reviewed_program_digest does not match author_program_hash")


def write_normalized_final_review(
    stage_dir: str | Path,
    final_review_payload: dict[str, Any],
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> Path:
    normalized = normalize_final_review_payload(final_review_payload, request_payload, receipt_payload)
    output_path = Path(stage_dir) / "review" / "result" / NORMALIZED_FINAL_REVIEW_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output_path
