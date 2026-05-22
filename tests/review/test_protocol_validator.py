from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ReviewerRuntimeIdentity,
    load_adversarial_review_request,
    load_reviewer_receipt,
)
from runtime.tools.review_skillgen.protocol_validator import load_and_validate_protocol
from runtime.tools.review_session_runtime import prepare_review_cycle_for_handoff
from runtime.tools.review_skillgen.review_runtime_state import compute_author_materialization_digest_fresh
from tests.review.test_start_review_session import _prepare_mandate_stage


def _rewrite_active_request_to_old_subset(stage_dir: Path, *, required_artifact_paths: list[str]) -> None:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    manifest_path = stage_dir / request_payload["handoff_manifest_path"]
    manifest_payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    for payload in (request_payload, manifest_payload):
        payload["required_artifact_paths"] = list(required_artifact_paths)
        payload["required_provenance_paths"] = ["program_execution_manifest.json"]
        payload["launcher_checked_artifact_paths"] = list(required_artifact_paths)
        payload["launcher_checked_provenance_paths"] = ["program_execution_manifest.json"]
        payload["launcher_handoff_context_paths"] = [
            path for path in ("artifact_catalog.md", "field_dictionary.md", "run_manifest.json") if path in required_artifact_paths
        ]
        payload["stage_content_artifact_paths"] = []
        payload["stage_content_provenance_paths"] = []
        payload["upstream_binding_artifact_paths"] = []
        payload["upstream_binding_provenance_paths"] = []

    manifest_text = yaml.safe_dump(manifest_payload, sort_keys=False, allow_unicode=True)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    request_payload["handoff_manifest_digest"] = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    request_payload["bound_author_materialization_digest"] = compute_author_materialization_digest_fresh(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_artifact_paths,
        required_provenance_paths=("program_execution_manifest.json",),
    )
    request_path.write_text(yaml.safe_dump(request_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_protocol_validator_rejects_stale_stage_contract_context(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_payload = load_adversarial_review_request(request_dir / "adversarial_review_request.yaml")

    context_path = request_dir / "stage_contract_context.yaml"
    context_payload = yaml.safe_load(context_path.read_text(encoding="utf-8"))
    context_payload["author_materialization_digest"] = "different-digest"
    context_path.write_text(yaml.safe_dump(context_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    final_review_payload = {
        "lineage_id": request_payload["lineage_id"],
        "stage_id": request_payload["stage"],
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewed_artifact_paths": request_payload["stage_content_artifact_paths"],
        "reviewed_program_path": (
            f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
        ),
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "PASS",
        "review_summary": "looks good",
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": None,
        "downstream_permissions": [],
        "recommended_next_action": "advance",
    }
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(final_review_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REVIEW_CONTRACT_CONTEXT_STALE"):
        load_and_validate_protocol(
            review_request_dir=request_dir,
            review_result_dir=result_dir,
            request_loader=load_adversarial_review_request,
            receipt_loader=load_reviewer_receipt,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )


def test_protocol_validator_rejects_stale_cycle_when_current_author_digest_drifted(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_payload = load_adversarial_review_request(request_dir / "adversarial_review_request.yaml")

    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after prepare\n", encoding="utf-8")

    final_review_payload = {
        "lineage_id": request_payload["lineage_id"],
        "stage_id": request_payload["stage"],
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewed_artifact_paths": request_payload["stage_content_artifact_paths"],
        "reviewed_program_path": (
            f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
        ),
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "PASS",
        "review_summary": "looks good",
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": None,
        "downstream_permissions": [],
        "recommended_next_action": "advance",
    }
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(final_review_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REVIEW_CONTRACT_CONTEXT_STALE"):
        load_and_validate_protocol(
            review_request_dir=request_dir,
            review_result_dir=result_dir,
            request_loader=load_adversarial_review_request,
            receipt_loader=load_reviewer_receipt,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )


def test_protocol_validator_rejects_digest_drift_even_without_stage_contract_context_path(
    tmp_path: Path,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_path = request_dir / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    request_payload.pop("stage_contract_context_yaml_path", None)
    request_payload.pop("stage_contract_context_md_path", None)
    request_payload.pop("stage_contract_context_digest", None)
    request_path.write_text(yaml.safe_dump(request_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    (stage_dir / "author" / "formal" / "mandate.md").write_text("changed after prepare\n", encoding="utf-8")

    final_review_payload = {
        "lineage_id": request_payload["lineage_id"],
        "stage_id": request_payload["stage"],
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewed_artifact_paths": request_payload["stage_content_artifact_paths"],
        "reviewed_program_path": (
            f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
        ),
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "PASS",
        "review_summary": "looks good",
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": None,
        "downstream_permissions": [],
        "recommended_next_action": "advance",
    }
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(final_review_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REVIEW_CONTRACT_CONTEXT_STALE"):
        load_and_validate_protocol(
            review_request_dir=request_dir,
            review_result_dir=result_dir,
            request_loader=load_adversarial_review_request,
            receipt_loader=load_reviewer_receipt,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )


def test_protocol_validator_rejects_digest_drift_in_now_required_output_omitted_by_old_request(
    tmp_path: Path,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    prepare_review_cycle_for_handoff(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        },
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child-agent",
        host="codex",
    )
    _rewrite_active_request_to_old_subset(
        stage_dir,
        required_artifact_paths=[
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
        ],
    )

    request_dir = stage_dir / "review" / "request"
    result_dir = stage_dir / "review" / "result"
    request_payload = load_adversarial_review_request(request_dir / "adversarial_review_request.yaml")
    (stage_dir / "author" / "formal" / "field_dictionary.md").write_text("changed later-added truth\n", encoding="utf-8")

    final_review_payload = {
        "lineage_id": request_payload["lineage_id"],
        "stage_id": request_payload["stage"],
        "reviewer_identity": "reviewer-agent",
        "reviewer_agent_id": "reviewer-child-agent",
        "reviewed_artifact_paths": request_payload["stage_content_artifact_paths"],
        "reviewed_program_path": (
            f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
        ),
        "reviewed_artifact_digest": "artifact-digest",
        "reviewed_program_digest": "program-digest",
        "verdict": "PASS",
        "review_summary": "looks good",
        "blocking_findings": [],
        "reservation_findings": [],
        "info_findings": [],
        "residual_risks": [],
        "allowed_modifications": [],
        "rollback_stage": None,
        "downstream_permissions": [],
        "recommended_next_action": "advance",
    }
    (stage_dir / "review" / "final_review.yaml").write_text(
        yaml.safe_dump(final_review_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="REVIEW_CONTRACT_CONTEXT_STALE"):
        load_and_validate_protocol(
            review_request_dir=request_dir,
            review_result_dir=result_dir,
            request_loader=load_adversarial_review_request,
            receipt_loader=load_reviewer_receipt,
            runtime_identity=ReviewerRuntimeIdentity(
                reviewer_identity="reviewer-agent",
                reviewer_role="reviewer",
                reviewer_session_id="review-session",
                reviewer_mode="adversarial",
            ),
        )
