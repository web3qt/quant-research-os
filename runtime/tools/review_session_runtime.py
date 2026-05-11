from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    compute_author_materialization_digest,
    load_review_runtime_state,
    review_runtime_state_path,
    write_review_runtime_state,
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
    return compute_author_materialization_digest(
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
    bound_digest = state_payload.get("review_bound_author_digest") if state_payload else None
    if bound_digest is None:
        bound_digest = current_digest

    closure_exists = (_review_closure_path(stage_dir, "stage_completion_certificate.yaml")).exists()
    proof_chain_error = _review_proof_chain_error(stage_dir)
    if bound_digest == current_digest and not closure_exists and proof_chain_error is None:
        raise ValueError(
            f"active review cycle {request_payload['review_cycle_id']} is still in progress; "
            "start a new review only after it closes or the author package changes"
        )

    reason = "stale" if bound_digest != current_digest or proof_chain_error is not None else "superseded"
    return archive_active_review_cycle(
        stage_dir,
        review_cycle_id=request_payload["review_cycle_id"],
        reason=reason,
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
        existing_request_payload = load_adversarial_review_request(existing_request_path)
        current_digest = compute_author_materialization_digest(
            artifact_root=_author_formal_dir(stage_dir),
            required_outputs=existing_request_payload["required_artifact_paths"],
            required_provenance_paths=existing_request_payload["required_provenance_paths"],
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
    current_digest = compute_author_materialization_digest(
        artifact_root=_author_formal_dir(stage_dir),
        required_outputs=request_payload["required_artifact_paths"],
        required_provenance_paths=request_payload["required_provenance_paths"],
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
    result_path = _display_path(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        display_root=display_root,
    )
    lines = [
        f"Handoff for QROS {payload['stage']} adversarial review ({host}).",
        "",
        f"Lineage: {payload['lineage_id']}",
        f"Stage: {payload['stage']}",
        f"Review cycle: {payload['review_cycle_id']}",
        f"Host: {host}",
        f"Reviewer identity: {reviewer_identity}",
        f"Reviewer session id / agent id: {reviewer_session_id}",
        "",
        "Hard constraints:",
        "- Do not run qros-review.",
        "- Do not write closure artifacts.",
        "- Do not modify author/formal or review/request files.",
        "",
        "Permitted reads only:",
        f"- {request_root}/*",
        f"- {author_root}/*",
        "",
        "Permitted write only:",
        f"- {result_path}",
        "",
        "Write reviewer_findings.raw.yaml with top-level fields:",
        f"review_cycle_id: {payload['review_cycle_id']}",
        f"reviewer_agent_id: {payload['receipt_payload']['reviewer_agent_id']}",
        "review_loop_outcome",
        "blocking_findings",
        "reservation_findings",
        "info_findings",
        "residual_risks",
    ]
    return "\n".join(lines)


def _closer_command(
    *,
    payload: dict[str, Any],
    reviewer_identity: str,
    reviewer_session_id: str,
    display_root: Path | None,
) -> str:
    stage_dir = _display_path(Path(payload["stage_dir"]), display_root=display_root)
    lineage_root = _display_path(Path(payload["lineage_root"]), display_root=display_root)
    return (
        "./.qros/bin/qros-review "
        f"--stage-dir {stage_dir} "
        f"--lineage-root {lineage_root} "
        f"--reviewer-id {reviewer_identity} "
        "--reviewer-role reviewer "
        f"--reviewer-session-id {reviewer_session_id} "
        "--reviewer-mode adversarial"
    )


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
        "closer_command": _closer_command(
            payload=payload,
            reviewer_identity=reviewer_identity,
            reviewer_session_id=reviewer_session_id,
            display_root=display_root,
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
