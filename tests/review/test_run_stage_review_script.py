import hashlib
import json
from pathlib import Path
import os
from subprocess import run
import sys

import pytest
import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from tests.helpers.repo_paths import REPO_ROOT
from runtime.tools.review_skillgen.adversarial_review_contract import ReviewerRuntimeIdentity
from runtime.tools.review_skillgen.review_engine import ReviewRuntimeConfigurationError, _require_stage_config
from runtime.tools.review_skillgen.review_result_writer import ensure_runtime_review_result
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    write_reviewer_write_scope_baseline,
)


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
        "time_split.json",
        "parameter_grid.yaml",
        "program_execution_manifest.json",
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
        stage_dir / "author" / "formal" / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
            "factor_role": "standalone_alpha",
            "factor_structure": "single_factor",
            "portfolio_expression": "long_short_rank_based",
            "neutralization_policy": "market_beta_neutral",
        },
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
    project_root = str(stage_dir.parent.parent.parent.resolve())
    lineage_root = str(stage_dir.parent.resolve())
    resolved_stage_dir = str(stage_dir.resolve())
    author_formal_dir = str((stage_dir / "author" / "formal").resolve())
    review_request_dir = str((stage_dir / "review" / "request").resolve())
    review_result_dir = str((stage_dir / "review" / "result").resolve())
    handoff_manifest_path = stage_dir / "review" / "request" / "reviewer_handoff_manifest.yaml"
    _write_yaml(
        handoff_manifest_path,
        {
            "review_cycle_id": "cycle-1",
            "lineage_id": "topic_a",
            "stage": "mandate",
            "project_root": project_root,
            "lineage_root": lineage_root,
            "stage_dir": resolved_stage_dir,
            "author_formal_dir": author_formal_dir,
            "review_request_dir": review_request_dir,
            "review_result_dir": review_result_dir,
            "required_program_dir": "program/mandate",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "stage_content_artifact_paths": required_artifact_paths,
            "stage_content_provenance_paths": required_provenance_paths,
            "upstream_binding_artifact_paths": [],
            "upstream_binding_provenance_paths": [],
            "permitted_input_roots": ["review/request", "author/formal"],
            "permitted_output_roots": ["review/result"],
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
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
            "project_root": project_root,
            "lineage_root": lineage_root,
            "stage_dir": resolved_stage_dir,
            "author_formal_dir": author_formal_dir,
            "review_request_dir": review_request_dir,
            "review_result_dir": review_result_dir,
            "author_identity": "author-agent",
            "author_session_id": "author-session",
            "required_program_dir": "program/mandate",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "stage_content_artifact_paths": required_artifact_paths,
            "stage_content_provenance_paths": required_provenance_paths,
            "upstream_binding_artifact_paths": [],
            "upstream_binding_provenance_paths": [],
            "required_reviewer_mode": "adversarial",
            "handoff_manifest_path": "review/request/reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": handoff_manifest_digest,
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
        },
    )
    _write_yaml(
        stage_dir / "review" / "request" / "reviewer_receipt.yaml",
        {
            "review_cycle_id": "cycle-1",
            "project_root": project_root,
            "lineage_root": lineage_root,
            "stage_dir": resolved_stage_dir,
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "execution_mode": "spawned_agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "host": "codex",
            "reviewer_invocation_kind": "codex_spawn_agent",
            "context_isolation_policy": "fork_context_false",
            "handoff_delivery_method": "send_input",
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": handoff_manifest_digest,
            "requested_reviewer_identity": "reviewer-agent",
            "requested_reviewer_session_id": "review-session",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "receipt_written_at": "2026-04-17T03:00:00Z",
        },
    )
    author_digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id="cycle-1",
        review_requested_at="2026-04-17T03:00:00Z",
        review_bound_author_digest=author_digest,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id="cycle-1",
        launcher_thread_id="leader-thread",
        reviewer_agent_id="reviewer-child-agent",
    )
    _write_yaml(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        {
            "review_cycle_id": "cycle-1",
            "reviewer_session_id": "review-session",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "reviewed_project_root": project_root,
            "reviewed_lineage_root": lineage_root,
            "reviewed_stage_dir": resolved_stage_dir,
            "hard_gate_findings_acknowledged": True,
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
    return stage_dir


def _handoff_manifest_digest(stage_dir: Path) -> str:
    return hashlib.sha256(
        (stage_dir / "review" / "request" / "reviewer_handoff_manifest.yaml")
        .read_text(encoding="utf-8")
        .encode("utf-8")
    ).hexdigest()


def _canonicalize_raw_review_findings(stage_dir: Path) -> None:
    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    receipt_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "reviewer_receipt.yaml").read_text(encoding="utf-8")
    )
    ensure_runtime_review_result(
        review_result_dir=stage_dir / "review" / "result",
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=ReviewerRuntimeIdentity(
            reviewer_identity="reviewer-agent",
            reviewer_role="reviewer",
            reviewer_session_id="review-session",
            reviewer_mode="adversarial",
        ),
    )


def test_run_stage_review_script_creates_closure_artifacts(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

    result = run(
        [sys.executable, str(script_path)],
        cwd=stage_dir,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "QROS_REVIEWER_ID": "reviewer-agent",
            "QROS_REVIEWER_ROLE": "reviewer",
            "QROS_REVIEWER_SESSION_ID": "review-session",
            "QROS_REVIEWER_MODE": "adversarial",
        },
    )

    assert result.returncode == 0
    assert "Review loop outcome: CLOSURE_READY_PASS" in result.stdout
    assert "Final verdict: PASS" in result.stdout
    assert "Recommended next skill: qros-research-session" in result.stdout
    assert "qros-session --continue" not in result.stdout
    assert "Run /clear" not in result.stdout
    assert "Clear instruction" not in result.stdout
    assert "qros-resume --lineage-id" not in result.stdout
    assert (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()
    evaluator_current = stage_dir / "evaluation" / "stage_evaluator.json"
    evaluator_ledger = stage_dir / "evaluation" / "stage_evaluator_results.jsonl"
    assert evaluator_current.exists()
    assert evaluator_ledger.exists()
    evaluator_payload = json.loads(evaluator_current.read_text(encoding="utf-8"))
    assert evaluator_payload["status"] == "passed"
    assert evaluator_payload["can_progress"] is True
    assert not (stage_dir / "review" / "governance" / "governance_signal.json").exists()
    ledger = yaml.safe_load((stage_dir.parent / "lineage_lock_ledger.yaml").read_text(encoding="utf-8"))
    locked = ledger["locked_stages"]["mandate"]["files"]
    locked_paths = {item["path"] for item in locked}
    assert "mandate/author/formal/research_route.yaml" in locked_paths
    assert "mandate/author/formal/program_execution_manifest.json" in locked_paths
    assert "mandate/review/closure/stage_gate_review.yaml" in locked_paths


def test_run_stage_review_script_supports_explicit_context_args(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
            "--reviewer-id",
            "reviewer-agent",
            "--reviewer-role",
            "reviewer",
            "--reviewer-session-id",
            "review-session",
            "--reviewer-mode",
            "adversarial",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Stage: mandate" in result.stdout


def test_review_runtime_config_error_names_missing_checklist_stage(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "btc" / "05_tss_test_evidence"
    lineage_root = stage_dir.parent

    with pytest.raises(ReviewRuntimeConfigurationError) as excinfo:
        _require_stage_config(
            {"stages": {}},
            "tss_test_evidence",
            schema_path=REPO_ROOT / "contracts" / "review" / "review_checklist_master.yaml",
            missing_label="review checklist stage",
            stage_dir=stage_dir,
            lineage_root=lineage_root,
        )

    message = str(excinfo.value)
    assert "missing review checklist stage: tss_test_evidence" in message
    assert "contracts/review/review_checklist_master.yaml" in message
    assert "stages.tss_test_evidence" in message


def test_run_stage_review_script_auto_materializes_raw_findings_and_audit(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"
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
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": ["fresh reviewer run"],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": ["mandate_next_stage_confirmation_pending"],
        },
    )

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
            "--reviewer-id",
            "reviewer-agent",
            "--reviewer-role",
            "reviewer",
            "--reviewer-session-id",
            "review-session",
            "--reviewer-mode",
            "adversarial",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (stage_dir / "review" / "result" / "adversarial_review_result.yaml").exists()
    assert (stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml").exists()
    assert not (stage_dir / "review" / "result" / "reviewer_findings.raw.yaml").exists()


def test_issue_reviewer_receipt_script_writes_receipt(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "issue_reviewer_receipt.py"
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    receipt_path.unlink()

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
            "--reviewer-id",
            "reviewer-agent",
            "--reviewer-session-id",
            "review-session",
            "--launcher-session-id",
            "launcher-session",
            "--launcher-thread-id",
            "leader-thread",
            "--reviewer-agent-id",
            "reviewer-child-agent",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert receipt_path.exists()
    receipt_payload = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
    assert receipt_payload["requested_reviewer_identity"] == "reviewer-agent"
    assert receipt_payload["requested_reviewer_session_id"] == "review-session"
    assert receipt_payload["reviewer_agent_id"] == "reviewer-child-agent"


def test_audit_reviewer_write_scope_script_writes_pass_artifact(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "audit_reviewer_write_scope.py"
    audit_path = stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml"
    _canonicalize_raw_review_findings(stage_dir)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert audit_path.exists()
    audit_payload = yaml.safe_load(audit_path.read_text(encoding="utf-8"))
    assert audit_payload["audit_status"] == "PASS"


def test_audit_reviewer_write_scope_script_fails_on_protected_author_change(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "audit_reviewer_write_scope.py"
    _canonicalize_raw_review_findings(stage_dir)
    (stage_dir / "author" / "formal" / "mandate.md").write_text("tampered\n", encoding="utf-8")

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Audit status: FAIL" in result.stdout


def test_run_stage_review_script_rejects_stale_canonical_result_projection(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

    (stage_dir / "review" / "result" / "reviewer_findings.raw.yaml").unlink()
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "cycle-1",
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "reviewer",
            "reviewer_session_id": "review-session",
            "reviewer_mode": "adversarial",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": _handoff_manifest_digest(stage_dir),
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "reviewed_program_dir": "program/unapproved_scope",
            "reviewed_program_entrypoint": "alternate.py",
            "reviewed_project_root": str(stage_dir.parent.parent.parent.resolve()),
            "reviewed_lineage_root": str(stage_dir.parent.resolve()),
            "reviewed_stage_dir": str(stage_dir.resolve()),
            "hard_gate_findings_acknowledged": True,
            "reviewed_artifact_paths": ["mandate.md", "review_notes.md"],
            "reviewed_provenance_paths": ["program_execution_manifest.json"],
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
            "--reviewer-id",
            "reviewer-agent",
            "--reviewer-role",
            "reviewer",
            "--reviewer-session-id",
            "review-session",
            "--reviewer-mode",
            "adversarial",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "PROTECTED_STATE_DRIFT" in result.stderr
    assert "reviewer_findings.raw.yaml is required" in result.stderr


def test_run_stage_review_script_rejects_review_cycle_mismatch(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

    _write_yaml(
        stage_dir / "review" / "result" / "reviewer_findings.raw.yaml",
        {
            "review_cycle_id": "stale-cycle",
            "reviewer_session_id": "review-session",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "reviewed_project_root": str(stage_dir.parent.parent.parent.resolve()),
            "reviewed_lineage_root": str(stage_dir.parent.resolve()),
            "reviewed_stage_dir": str(stage_dir.resolve()),
            "hard_gate_findings_acknowledged": True,
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-dir",
            str(stage_dir),
            "--lineage-root",
            str(stage_dir.parent),
            "--reviewer-id",
            "reviewer-agent",
            "--reviewer-role",
            "reviewer",
            "--reviewer-session-id",
            "review-session",
            "--reviewer-mode",
            "adversarial",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "review_cycle_id" in result.stderr
