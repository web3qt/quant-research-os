from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

from runtime.tools.artifact_contract_runtime import ArtifactContractError, load_artifact_contract
from runtime.tools.lineage_program_runtime import inspect_stage_program, load_provenance_manifest
from runtime.tools.research_session import (
    _author_formal_dir,
    _program_spec_for_session_stage,
    _review_closure_path,
    _review_proof_chain_error,
    detect_session_stage,
)
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
    load_adversarial_review_request,
)
from runtime.tools.review_skillgen.context_inference import build_stage_context, infer_review_context
from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.review_engine import (
    CHECKLIST_PATH as DEFAULT_CHECKLIST_PATH,
    GATES_PATH as DEFAULT_GATES_PATH,
    ReviewRuntimeConfigurationError,
    _require_stage_config,
)
from runtime.tools.lineage_lock_ledger import assert_lineage_locks_intact
from runtime.tools.review_skillgen.review_runtime_state import (
    archive_active_review_cycle,
    compute_author_materialization_digest_fresh,
    load_review_runtime_state,
    review_runtime_state_path,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.stage_contract_context import (
    STAGE_CONTRACT_CONTEXT_MD_FILENAME,
    STAGE_CONTRACT_CONTEXT_YAML_FILENAME,
    build_stage_contract_context,
    render_stage_contract_context_markdown,
)
from runtime.tools.stage_evaluator import StageEvaluatorConfigurationError, evaluate_stage


ROOT = Path(__file__).resolve().parents[2]
GATES_PATH = DEFAULT_GATES_PATH
CHECKLIST_PATH = DEFAULT_CHECKLIST_PATH
SHARED_REVIEW_PROTOCOL_PATH = ROOT / "docs" / "guides" / "qros-review-shared-protocol.md"


def _stage_dir_for_context(*, cwd: Path | None, explicit_context: dict[str, Any] | None) -> dict[str, Any]:
    if explicit_context is not None:
        context = build_stage_context(Path(explicit_context["stage_dir"]).resolve())
        context["lineage_root"] = Path(explicit_context["lineage_root"]).resolve()
        return context
    return infer_review_context(cwd or Path.cwd())


def _current_author_digest(stage_dir: Path, spec) -> str:
    return compute_author_materialization_digest_fresh(
        artifact_root=_author_formal_dir(stage_dir),
        required_outputs=spec.required_outputs,
        required_provenance_paths=("program_execution_manifest.json",),
    )


def _archive_if_stale_or_closed(stage_dir: Path, *, current_digest: str) -> list[str]:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    if not request_path.exists():
        return []

    request_payload = load_adversarial_review_request(request_path)
    state_path = review_runtime_state_path(stage_dir)
    state_payload = load_review_runtime_state(state_path) if state_path.exists() else None
    bound_digests = {
        digest.strip()
        for digest in (
            state_payload.get("review_bound_author_digest") if state_payload else None,
            request_payload.get("bound_author_materialization_digest"),
        )
        if isinstance(digest, str) and digest.strip()
    }
    if not bound_digests:
        bound_digests = {current_digest}

    closure_exists = (_review_closure_path(stage_dir, "stage_completion_certificate.yaml")).exists()
    proof_chain_error = _review_proof_chain_error(stage_dir)
    has_old_bound_digest = any(bound_digest != current_digest for bound_digest in bound_digests)
    # 只要任一绑定 digest 已经落后当前 author materialization，就必须按 stale 处理。
    if has_old_bound_digest or proof_chain_error is not None:
        raise ValueError(
            f"review cycle {request_payload['review_cycle_id']} is stale; "
            "run qros-review-cycle reset --archive-stale-cycle first, then prepare a fresh reviewer run"
        )

    if current_digest in bound_digests and len(bound_digests) == 1 and not closure_exists and proof_chain_error is None:
        raise ValueError(
            f"active review cycle {request_payload['review_cycle_id']} is still in progress; "
            "start a new review only after it closes or the author package changes"
        )

    raise ValueError(
        f"review cycle {request_payload['review_cycle_id']} is superseded; "
        "run qros-review-cycle reset --archive-stale-cycle first, then prepare a fresh reviewer run"
    )


def _preflight_review_runtime_config(*, stage: str, stage_dir: Path, lineage_root: Path) -> None:
    gates = load_gate_schema(GATES_PATH)
    checklist = load_checklist_schema(CHECKLIST_PATH)
    _require_stage_config(
        gates,
        stage,
        schema_path=GATES_PATH,
        missing_label="stage gate",
        stage_dir=stage_dir,
        lineage_root=lineage_root,
    )
    _require_stage_config(
        checklist,
        stage,
        schema_path=CHECKLIST_PATH,
        missing_label="review checklist stage",
        stage_dir=stage_dir,
        lineage_root=lineage_root,
    )

    try:
        load_artifact_contract(stage)
    except ArtifactContractError as exc:
        raise ReviewRuntimeConfigurationError(
            "\n".join(
                [
                    "QROS review runtime configuration error:",
                    f"missing artifact contract stage: {stage}",
                    f"stage_dir: {stage_dir}",
                    f"lineage_root: {lineage_root}",
                    "missing_entry: runtime/tools/artifact_contract_runtime.py -> "
                    f"ARTIFACT_CONTRACTS[{stage!r}]",
                    "fix: add the stage artifact contract under contracts/artifacts/ and register it in ARTIFACT_CONTRACTS.",
                ]
            )
        ) from exc

    try:
        evaluate_stage(stage_dir, lineage_root=lineage_root)
    except StageEvaluatorConfigurationError as exc:
        raise exc

    if not SHARED_REVIEW_PROTOCOL_PATH.exists():
        raise ReviewRuntimeConfigurationError(
            "\n".join(
                [
                    "QROS review runtime configuration error:",
                    "missing shared review protocol doc.",
                    f"stage: {stage}",
                    f"stage_dir: {stage_dir}",
                    f"lineage_root: {lineage_root}",
                    f"missing_entry: {SHARED_REVIEW_PROTOCOL_PATH}",
                    "fix: ensure docs/guides/qros-review-shared-protocol.md is installed; "
                    "for a consumer repo, run qros-update or rerun QROS setup.",
                ]
            )
        )


def _prepare_review_cycle(
    *,
    cwd: Path | None,
    explicit_context: dict[str, Any] | None,
    reviewer_identity: str,
    reviewer_session_id: str,
) -> dict[str, Any]:
    context = _stage_dir_for_context(cwd=cwd, explicit_context=explicit_context)
    stage_dir = Path(context["stage_dir"]).resolve()
    lineage_root = Path(context["lineage_root"]).resolve()
    assert_lineage_locks_intact(lineage_root)
    current_stage = detect_session_stage(lineage_root)
    if not current_stage.endswith("_review_confirmation_pending") and not current_stage.endswith("_review"):
        raise ValueError(
            f"review can only start from a review gate or active review stage; observed current_stage={current_stage}"
        )

    spec = _program_spec_for_session_stage(current_stage)
    if spec is None:
        raise ValueError(f"current_stage {current_stage} is not a reviewable stage")
    _preflight_review_runtime_config(stage=spec.stage_id, stage_dir=stage_dir, lineage_root=lineage_root)
    provenance = load_provenance_manifest(stage_dir)
    if provenance is None:
        raise ValueError(f"{stage_dir}: program_execution_manifest.json provenance is missing")
    inspection = inspect_stage_program(lineage_root, spec.stage_id, spec.route)
    if inspection.error_code is not None or inspection.required_program_entrypoint is None:
        raise ValueError(inspection.error_message)
    author_identity = provenance.get("authored_by_agent_id")
    author_session_id = provenance.get("authoring_session_id")
    if not isinstance(author_identity, str) or not author_identity.strip():
        raise ValueError(f"{stage_dir}: authored_by_agent_id is missing from provenance")
    if not isinstance(author_session_id, str) or not author_session_id.strip():
        raise ValueError(f"{stage_dir}: authoring_session_id is missing from provenance")

    existing_request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    if existing_request_path.exists():
        existing_request = load_adversarial_review_request(existing_request_path)
        current_digest = compute_author_materialization_digest_fresh(
            artifact_root=_author_formal_dir(stage_dir),
            required_outputs=existing_request["required_artifact_paths"],
            required_provenance_paths=existing_request["required_provenance_paths"],
        )
    else:
        current_digest = _current_author_digest(stage_dir, spec)
    archived_paths = _archive_if_stale_or_closed(stage_dir, current_digest=current_digest)

    request_payload = ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage=spec.stage_id,
        author_identity=author_identity.strip(),
        author_session_id=author_session_id.strip(),
        required_program_dir=inspection.required_program_dir,
        required_program_entrypoint=inspection.required_program_entrypoint,
        required_artifact_paths=list(spec.required_outputs),
        required_provenance_paths=["program_execution_manifest.json"],
        program_hash=provenance.get("program_hash") if isinstance(provenance.get("program_hash"), str) else None,
        stage_invoked_at=provenance.get("invoked_at") if isinstance(provenance.get("invoked_at"), str) else None,
    )
    # request payload 会规范化 artifact path 顺序；绑定 digest 必须使用落盘 request 的顺序，
    # 否则同一组文件会因为顺序不同被 protocol validator 误判为 stale。
    current_digest = compute_author_materialization_digest_fresh(
        artifact_root=_author_formal_dir(stage_dir),
        required_outputs=request_payload["required_artifact_paths"],
        required_provenance_paths=request_payload["required_provenance_paths"],
    )
    request_dir = stage_dir / "review" / "request"
    context_payload = build_stage_contract_context(
        stage_id=spec.stage_id,
        lineage_id=lineage_root.name,
        review_cycle_id=request_payload["review_cycle_id"],
        author_materialization_digest=current_digest,
        review_cycle_stage_dir=stage_dir,
    )
    context_yaml_path = request_dir / STAGE_CONTRACT_CONTEXT_YAML_FILENAME
    context_md_path = request_dir / STAGE_CONTRACT_CONTEXT_MD_FILENAME
    context_yaml_text = yaml.safe_dump(context_payload, sort_keys=False, allow_unicode=True)
    context_md_text = render_stage_contract_context_markdown(context_payload)
    context_yaml_path.write_text(context_yaml_text, encoding="utf-8")
    context_md_path.write_text(context_md_text, encoding="utf-8")
    request_payload["bound_author_materialization_digest"] = current_digest
    request_payload["stage_contract_context_yaml_path"] = f"review/request/{STAGE_CONTRACT_CONTEXT_YAML_FILENAME}"
    request_payload["stage_contract_context_md_path"] = f"review/request/{STAGE_CONTRACT_CONTEXT_MD_FILENAME}"
    request_payload["stage_contract_context_digest"] = hashlib.sha256(context_yaml_text.encode("utf-8")).hexdigest()
    (request_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME).write_text(
        yaml.safe_dump(request_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    state_payload = write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=request_payload["review_cycle_id"],
        review_requested_at=datetime.now(timezone.utc).isoformat(),
        review_bound_author_digest=current_digest,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        last_review_verdict=None,
        closure_written_at=None,
    )
    return {
        "stage_dir": stage_dir,
        "lineage_root": lineage_root,
        "current_stage": current_stage,
        "spec": spec,
        "archived_paths": archived_paths,
        "request_payload": request_payload,
        "state_payload": state_payload,
    }


def _build_review_cycle_payload(
    *,
    prepared: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> dict[str, Any]:
    stage_dir = prepared["stage_dir"]
    lineage_root = prepared["lineage_root"]
    spec = prepared["spec"]
    request_payload = prepared["request_payload"]
    return {
        "lineage_id": lineage_root.name,
        "stage": spec.stage_id,
        "stage_dir": str(stage_dir),
        "lineage_root": str(lineage_root),
        "current_stage": prepared["current_stage"],
        "review_cycle_id": request_payload["review_cycle_id"],
        "request_path": str((stage_dir / "review" / "request" / "adversarial_review_request.yaml").relative_to(lineage_root)),
        "receipt_path": str((stage_dir / "review" / "request" / "reviewer_receipt.yaml").relative_to(lineage_root)),
        "archived_paths": prepared["archived_paths"],
        "review_runtime_state": prepared["state_payload"],
        "reviewer_context_source": receipt_payload["reviewer_context_source"],
        "reviewer_history_inheritance": receipt_payload["reviewer_history_inheritance"],
        "reviewer_execution_mode": receipt_payload["execution_mode"],
        "launcher_session_id": receipt_payload["launcher_session_id"],
        "launcher_thread_id": receipt_payload["launcher_thread_id"],
        "request_payload": request_payload,
        "receipt_payload": receipt_payload,
    }


def _display_path(path: Path, *, display_root: Path | None) -> str:
    resolved = path.resolve()
    if display_root is not None:
        try:
            return resolved.relative_to(display_root.resolve()).as_posix()
        except ValueError:
            pass
    return str(resolved)


def _reviewer_handoff_prompt(
    *,
    payload: dict[str, Any],
    reviewer_identity: str,
    reviewer_session_id: str,
    display_root: Path | None,
    host: str = "codex",
) -> str:
    stage_dir = Path(payload["stage_dir"]).resolve()
    request_root = _display_path(stage_dir / "review" / "request", display_root=display_root)
    author_root = _display_path(stage_dir / "author" / "formal", display_root=display_root)
    review_root = _display_path(stage_dir / "review", display_root=display_root)
    final_review_path = _display_path(stage_dir / "review" / "final_review.yaml", display_root=display_root)
    request_payload = payload["request_payload"]
    receipt_payload = payload["receipt_payload"]
    stage_contract_context_yaml_path = request_payload.get("stage_contract_context_yaml_path")
    stage_contract_context_md_path = request_payload.get("stage_contract_context_md_path")
    expected_artifact_digest = request_payload.get("bound_author_materialization_digest", "<artifact digest>")
    expected_program_digest = request_payload.get("author_program_hash", "<program digest>")
    required_program_dir = request_payload.get("required_program_dir")
    required_program_entrypoint = request_payload.get("required_program_entrypoint")
    if isinstance(required_program_dir, str) and isinstance(required_program_entrypoint, str):
        reviewed_program_path = (Path(required_program_dir) / required_program_entrypoint).as_posix()
        program_read_scope = f"{required_program_dir}/{required_program_entrypoint} and any stage program source it imports"
    else:
        reviewed_program_path = "<relative path>"
        program_read_scope = "active request stage program source"
    lines = [
        f"Handoff for QROS {payload['stage']} adversarial review ({host}).",
        "",
        "Launcher boundary:",
        "- The current/main conversation is the launcher, not the reviewer.",
        "- Do not write review/final_review.yaml from the launcher conversation.",
        "- Send this handoff to an independent reviewer/subagent.",
        f"- launcher_session_id: {receipt_payload['launcher_session_id']}",
        f"- launcher_thread_id: {receipt_payload['launcher_thread_id']}",
        f"- reviewer_agent_id: {receipt_payload['reviewer_agent_id']}",
        "- The QROS governance repo is not the active research repo unless the canonical paths in this handoff point there.",
        "",
        "Isolation contract:",
        f"- reviewer_context_source: {receipt_payload['reviewer_context_source']}",
        f"- reviewer_history_inheritance: {receipt_payload['reviewer_history_inheritance']}",
        f"- reviewer_execution_mode: {receipt_payload['execution_mode']}",
        f"- reviewer_invocation_kind: {receipt_payload['reviewer_invocation_kind']}",
        f"- context_isolation_policy: {receipt_payload['context_isolation_policy']}",
        f"- handoff_delivery_method: {receipt_payload['handoff_delivery_method']}",
        "",
        "Canonical review context:",
        f"- Active research repo root: {request_payload['project_root']}",
        f"- Lineage root: {request_payload['lineage_root']}",
        f"- Stage dir: {request_payload['stage_dir']}",
        f"- project_root: {request_payload['project_root']}",
        f"- lineage_root: {request_payload['lineage_root']}",
        f"- stage_dir: {request_payload['stage_dir']}",
        f"- author_formal_dir: {author_root}",
        f"- review_request_dir: {request_root}",
        f"- review_dir: {review_root}",
        "",
        f"Lineage: {payload['lineage_id']}",
        f"Stage: {payload['stage']}",
        f"Review cycle: {payload['review_cycle_id']}",
        f"Host: {host}",
        f"Reviewer identity: {reviewer_identity}",
        f"Reviewer session id / agent id: {reviewer_session_id}",
        "",
        "Hard constraints:",
        "- Do not run qros-review or any closer step.",
        "- Do not write closure artifacts.",
        "- Do not modify author/formal or review/request files.",
        "",
        "Permitted reads only:",
        f"- {request_root}/*",
        f"- {author_root}/*",
        f"- {program_read_scope}",
        "",
        "Read these generated contract context files before evaluating stage truth:",
        f"- {_display_path(stage_dir / stage_contract_context_yaml_path, display_root=display_root) if isinstance(stage_contract_context_yaml_path, str) else request_root + '/' + STAGE_CONTRACT_CONTEXT_YAML_FILENAME}",
        f"- {_display_path(stage_dir / stage_contract_context_md_path, display_root=display_root) if isinstance(stage_contract_context_md_path, str) else request_root + '/' + STAGE_CONTRACT_CONTEXT_MD_FILENAME}",
        "",
        "Permitted write only:",
        f"- {final_review_path}",
        "",
        "Write exactly one canonical machine-readable review artifact.",
        "Required final review schema:",
        f"lineage_id: {payload['lineage_id']}",
        f"stage_id: {payload['stage']}",
        f"reviewer_identity: {reviewer_identity}",
        f"reviewer_agent_id: {payload['receipt_payload']['reviewer_agent_id']}",
        "reviewed_artifact_paths: [<relative paths under author/formal>]",
        f"reviewed_program_path: {reviewed_program_path}",
        f"reviewed_artifact_digest: {expected_artifact_digest}",
        f"reviewed_program_digest: {expected_program_digest}",
        "verdict: one of PASS, CONDITIONAL PASS, FIX_REQUIRED, RETRY, NO-GO, CHILD LINEAGE",
        "review_summary: <single sentence>",
        "blocking_findings: []",
        "reservation_findings: []",
        "info_findings: []",
        "residual_risks: []",
        "allowed_modifications: []",
        "rollback_stage: <stage or null>",
        "downstream_permissions: []",
        "recommended_next_action: <single sentence>",
    ]
    return "\n".join(lines)


def prepare_review_cycle_for_handoff(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_thread_id: str,
    reviewer_agent_id: str,
    host: str = "codex",
) -> dict[str, Any]:
    payload = start_review_cycle(
        cwd=cwd,
        explicit_context=explicit_context,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id=launcher_session_id,
        launcher_thread_id=launcher_thread_id,
        reviewer_agent_id=reviewer_agent_id,
        host=host,
    )
    display_root = cwd.resolve() if cwd is not None else None
    return {
        **payload,
        "reviewer_handoff_prompt": _reviewer_handoff_prompt(
            payload=payload,
            reviewer_identity=reviewer_identity,
            reviewer_session_id=reviewer_session_id,
            display_root=display_root,
            host=host,
        ),
    }


def start_review_cycle(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_thread_id: str,
    reviewer_agent_id: str,
    host: str = "codex",
) -> dict[str, Any]:
    prepared = _prepare_review_cycle(
        cwd=cwd,
        explicit_context=explicit_context,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
    )
    receipt_payload = issue_reviewer_receipt(
        prepared["stage_dir"],
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id=launcher_session_id,
        launcher_thread_id=launcher_thread_id,
        reviewer_agent_id=reviewer_agent_id,
        execution_mode="spawned_agent",
        host=host,
    )
    return _build_review_cycle_payload(
        prepared=prepared,
        receipt_payload=receipt_payload,
    )


def start_review_session(
    *,
    cwd: Path | None = None,
    explicit_context: dict[str, Any] | None = None,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_thread_id: str,
    host: str = "codex",
) -> dict[str, Any]:
    prepared = _prepare_review_cycle(
        cwd=cwd,
        explicit_context=explicit_context,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
    )
    receipt_payload = issue_reviewer_receipt(
        prepared["stage_dir"],
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id=launcher_session_id,
        launcher_thread_id=launcher_thread_id,
        reviewer_agent_id=reviewer_session_id,
        execution_mode="review_session",
        host=host,
    )
    return _build_review_cycle_payload(
        prepared=prepared,
        receipt_payload=receipt_payload,
    )


def reset_review_cycle(
    *,
    stage_dir: Path,
    review_cycle_id: str | None = None,
    reason: str = "stale",
) -> dict[str, Any]:
    stage_dir = stage_dir.resolve()
    if review_cycle_id is None:
        request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
        if not request_path.exists():
            return {
                "stage_dir": str(stage_dir),
                "archived_paths": [],
                "next_action": "run qros-review-cycle prepare and request a fresh reviewer run",
            }
        request_payload = load_adversarial_review_request(request_path)
        review_cycle_id = request_payload["review_cycle_id"]

    archived_paths = archive_active_review_cycle(
        stage_dir,
        review_cycle_id=review_cycle_id,
        reason=reason,
    )
    return {
        "stage_dir": str(stage_dir),
        "review_cycle_id": review_cycle_id,
        "archived_paths": archived_paths,
        "next_action": "run qros-review-cycle prepare and request a fresh reviewer run",
    }
