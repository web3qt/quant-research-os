import hashlib
import json
from pathlib import Path

import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.review_skillgen.adversarial_review_contract import issue_reviewer_receipt
from runtime.tools.review_skillgen.review_engine import run_stage_review
from runtime.tools.review_skillgen.review_cycle_trace import load_review_cycle_trace
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import write_reviewer_write_scope_baseline


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> Path:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    (stage_dir / "author" / "formal").mkdir(parents=True)
    (stage_dir / "review" / "request").mkdir(parents=True)
    (stage_dir / "review" / "result").mkdir(parents=True)

    for name in [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "run_manifest.json",
    ]:
        (stage_dir / "author" / "formal" / name).write_text("ok\n", encoding="utf-8")
    (stage_dir / "author" / "formal" / "time_split.json").write_text(
        json.dumps(
            {
                "train": "2024-01-01/2024-03-31",
                "test": "2024-04-01/2024-06-30",
                "backtest": "2024-07-01/2024-09-30",
                "holdout": "2024-10-01/2024-12-31",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_yaml(
        stage_dir / "author" / "formal" / "parameter_grid.yaml",
        {
            "parameters": [
                {
                    "param_id": "shock_threshold_bp",
                    "values": [30, 50],
                }
            ]
        },
    )

    return stage_dir


def _write_review_request(stage_dir: Path, *, author_identity: str = "author-agent") -> None:
    required_artifact_paths = [
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]
    required_provenance_paths = ["program_execution_manifest.json"]
    launcher_handoff_context_paths = ["artifact_catalog.md", "field_dictionary.md"]
    handoff_manifest_path = stage_dir / "review" / "request" / "reviewer_handoff_manifest.yaml"
    review_context = {
        "project_root": str(stage_dir.parent.parent.parent.resolve()),
        "lineage_root": str(stage_dir.parent.resolve()),
        "stage_dir": str(stage_dir.resolve()),
        "author_formal_dir": str((stage_dir / "author" / "formal").resolve()),
        "review_request_dir": str((stage_dir / "review" / "request").resolve()),
        "review_result_dir": str((stage_dir / "review" / "result").resolve()),
    }
    _write_yaml(
        handoff_manifest_path,
        {
            "review_cycle_id": "cycle-1",
            "lineage_id": "topic_a",
            "stage": "mandate",
            "required_program_dir": "program/mandate",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "permitted_input_roots": ["review/request", "author/formal"],
            "permitted_output_roots": ["review/result"],
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
            **review_context,
        },
    )
    handoff_manifest_digest = hashlib.sha256(
        handoff_manifest_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    _write_yaml(
        stage_dir / "review" / "request" / "adversarial_review_request.yaml",
        {
            "review_cycle_id": "cycle-1",
            "lineage_id": "topic_a",
            "stage": "mandate",
            "author_identity": author_identity,
            "author_session_id": "author-session",
            "required_program_dir": "program/mandate",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "required_reviewer_mode": "adversarial",
            "handoff_manifest_path": "review/request/reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": handoff_manifest_digest,
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
            **review_context,
        },
    )


def _handoff_manifest_digest(stage_dir: Path) -> str:
    return hashlib.sha256(
        (stage_dir / "review" / "request" / "reviewer_handoff_manifest.yaml")
        .read_text(encoding="utf-8")
        .encode("utf-8")
    ).hexdigest()


def _write_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str = "reviewer-agent",
    reviewer_session_id: str = "review-session",
    reviewer_agent_id: str = "reviewer-child-agent",
) -> None:
    receipt = issue_reviewer_receipt(
        stage_dir,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
        launcher_session_id="launcher-session",
        launcher_thread_id="leader-thread",
        reviewer_agent_id=reviewer_agent_id,
    )
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    author_digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=request_payload["required_artifact_paths"],
        required_provenance_paths=request_payload["required_provenance_paths"],
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=request_payload["review_cycle_id"],
        review_requested_at=receipt["receipt_written_at"],
        review_bound_author_digest=author_digest,
        reviewer_identity=reviewer_identity,
        reviewer_session_id=reviewer_session_id,
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=receipt["review_cycle_id"],
        launcher_thread_id=receipt["launcher_thread_id"],
        reviewer_agent_id=receipt["reviewer_agent_id"],
    )


def _write_final_review(
    stage_dir: Path,
    *,
    verdict: str = "PASS",
    reviewer_identity: str = "reviewer-agent",
    reviewer_agent_id: str = "reviewer-child-agent",
) -> None:
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    reviewed_artifact_paths = sorted(request_payload["required_artifact_paths"], reverse=True)
    reviewed_program_path = (
        Path(request_payload["required_program_dir"]) / request_payload["required_program_entrypoint"]
    ).as_posix()
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": request_payload["lineage_id"],
            "stage_id": request_payload["stage"],
            "reviewer_identity": reviewer_identity,
            "reviewer_agent_id": reviewer_agent_id,
            "reviewed_artifact_paths": reviewed_artifact_paths,
            "reviewed_program_path": reviewed_program_path,
            "reviewed_artifact_digest": "dummy-reviewed-artifact-digest",
            "reviewed_program_digest": "dummy-reviewed-program-digest",
            "verdict": verdict,
            "review_summary": "Final review projected from reviewer-authored closure.",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "advance",
        },
    )


def _write_review_result(
    stage_dir: Path,
    *,
    outcome: str = "CLOSURE_READY_PASS",
    reviewer_identity: str = "reviewer-agent",
) -> None:
    rollback_payload = {}
    if outcome == "CLOSURE_READY_PASS_FOR_RETRY":
        rollback_payload = {
            "rollback_stage": "mandate",
            "allowed_modifications": ["clarify wording only"],
            "reservation_findings": ["needs controlled rerun log"],
        }
    _write_yaml(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        {
            "review_cycle_id": "cycle-1",
            "reviewer_session_id": "review-session",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "reviewed_project_root": str(stage_dir.parent.parent.parent.resolve()),
            "reviewed_lineage_root": str(stage_dir.parent.resolve()),
            "reviewed_stage_dir": str(stage_dir.resolve()),
            "hard_gate_findings_acknowledged": True,
            "review_loop_outcome": outcome,
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
            **rollback_payload,
        },
    )


def test_run_stage_review_pass_path(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
    assert payload["review_loop_outcome"] == "CLOSURE_READY_PASS"
    assert payload["blocking_findings"] == []
    assert (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()
    assert not (stage_dir / "review" / "governance" / "governance_signal.json").exists()
    assert "governance" not in payload
    assert "governance_signal_path" not in payload
    assert "governance_candidate_summary" not in payload
    trace_events = load_review_cycle_trace(stage_dir / "review" / "review_cycle_trace.jsonl")
    assert trace_events[0]["event_type"] == "receipt_issued"
    assert trace_events[-1]["event_type"] == "review_evaluated"
    assert [event["event_type"] for event in trace_events].count("write_scope_audit_completed") >= 1
    assert trace_events[-1]["final_verdict"] == "PASS"
    assert trace_events[-1]["closure_written"] is True


def test_run_stage_review_projects_final_review_and_runs_audit(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_final_review(stage_dir)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    normalized_path = stage_dir / "review" / "result" / "final_review.normalized.yaml"
    assert normalized_path.exists()
    normalized_payload = yaml.safe_load(normalized_path.read_text(encoding="utf-8"))
    audit_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").read_text(encoding="utf-8")
    )

    assert payload["final_verdict"] == "PASS"
    assert result_payload["reviewer_execution_mode"] == "spawned_agent"
    assert "review_summary" in normalized_payload
    assert audit_payload["audit_status"] == "PASS"
    assert audit_payload["unexpected_result_files"] == []
    assert payload["reviewer_write_scope_audit"]["audit_status"] == "PASS"


def test_run_stage_review_downgrades_to_retry_when_required_output_missing(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    (stage_dir / "author" / "formal" / "parameter_grid.yaml").unlink()
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir)

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "RETRY"
    assert any("parameter_grid.yaml" in item for item in payload["blocking_findings"])


def test_run_stage_review_accepts_pass_for_retry_with_rollback_metadata(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir, outcome="CLOSURE_READY_PASS_FOR_RETRY")
    _write_yaml(
        stage_dir / "review" / "result" / "review_findings.yaml",
        {
            "recommended_verdict": "PASS FOR RETRY",
            "rollback_stage": "mandate",
            "allowed_modifications": ["clarify wording only"],
            "reservation_findings": ["needs controlled rerun log"],
        },
    )

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["final_verdict"] == "PASS FOR RETRY"
    assert payload["rollback_stage"] == "mandate"
    assert payload["allowed_modifications"] == ["clarify wording only"]


def test_run_stage_review_rejects_self_review(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir, author_identity="same-agent")
    _write_reviewer_receipt(stage_dir, reviewer_identity="same-agent")
    _write_review_result(stage_dir, reviewer_identity="same-agent")

    try:
        run_stage_review(
            cwd=stage_dir,
            reviewer_identity="same-agent",
            reviewer_role="reviewer",
            reviewer_session_id="review-session",
            reviewer_mode="adversarial",
        )
    except ValueError as exc:
        assert "reviewer identity must differ" in str(exc)
    else:
        raise AssertionError("expected self-review rejection")


def test_run_stage_review_fix_required_skips_closure_artifacts(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
    _write_reviewer_receipt(stage_dir)
    _write_review_result(stage_dir, outcome="FIX_REQUIRED")

    payload = run_stage_review(
        cwd=stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_role="reviewer",
        reviewer_session_id="review-session",
        reviewer_mode="adversarial",
    )

    assert payload["review_loop_outcome"] == "FIX_REQUIRED"
    assert payload["final_verdict"] is None
    assert not (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()
    assert not (stage_dir / "review" / "governance" / "governance_signal.json").exists()
    assert "governance" not in payload
    trace_events = load_review_cycle_trace(stage_dir / "review" / "review_cycle_trace.jsonl")
    assert trace_events[-1]["event_type"] == "review_evaluated"
    assert trace_events[-1]["review_loop_outcome"] == "FIX_REQUIRED"
    assert trace_events[-1]["closure_written"] is False
