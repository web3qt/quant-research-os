import hashlib
from pathlib import Path
import os
from subprocess import run
import sys

import yaml

from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    run_reviewer_write_scope_audit,
    write_reviewer_write_scope_baseline,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
        "run_manifest.json",
    ]:
        (stage_dir / "author" / "formal" / name).write_text("ok\n", encoding="utf-8")

    required_artifact_paths = [
        "mandate.md",
        "research_scope.md",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    ]
    required_provenance_paths = ["program_execution_manifest.json"]
    launcher_handoff_context_paths = ["artifact_catalog.md", "field_dictionary.md"]
    handoff_manifest_path = stage_dir / "review" / "request" / "spawned_reviewer_handoff_manifest.yaml"
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
            "author_identity": "author-agent",
            "author_session_id": "author-session",
            "required_program_dir": "program/mandate",
            "required_program_entrypoint": "run_stage.py",
            "required_artifact_paths": required_artifact_paths,
            "required_provenance_paths": required_provenance_paths,
            "required_reviewer_mode": "adversarial",
            "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": handoff_manifest_digest,
            "required_result_write_root": "review/result",
            "launcher_review_ready_status": "complete",
            "launcher_checked_artifact_paths": required_artifact_paths,
            "launcher_checked_provenance_paths": required_provenance_paths,
            "launcher_handoff_context_paths": launcher_handoff_context_paths,
        },
    )
    _write_yaml(
        stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml",
        {
            "review_cycle_id": "cycle-1",
            "launcher_owner": "qros-runtime-launcher",
            "launcher_session_id": "launcher-session",
            "launcher_thread_id": "leader-thread",
            "spawn_mode": "spawned_agent",
            "spawned_agent_id": "reviewer-child-agent",
            "fork_context": False,
            "write_root": "review/result",
            "handoff_manifest_path": "review/request/spawned_reviewer_handoff_manifest.yaml",
            "handoff_manifest_digest": handoff_manifest_digest,
            "requested_reviewer_identity": "reviewer-agent",
            "requested_reviewer_session_id": "review-session",
            "receipt_written_at": "2026-04-17T03:00:00Z",
        },
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id="cycle-1",
        launcher_thread_id="leader-thread",
        spawned_agent_id="reviewer-child-agent",
    )
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
            "handoff_manifest_digest": handoff_manifest_digest,
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "reviewed_program_dir": "program/mandate",
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": required_artifact_paths,
            "reviewed_provenance_paths": required_provenance_paths,
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
    run_reviewer_write_scope_audit(stage_dir)
    return stage_dir


def _handoff_manifest_digest(stage_dir: Path) -> str:
    return hashlib.sha256(
        (stage_dir / "review" / "request" / "spawned_reviewer_handoff_manifest.yaml")
        .read_text(encoding="utf-8")
        .encode("utf-8")
    ).hexdigest()


def test_run_stage_review_script_creates_closure_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
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
    assert (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()
    assert not (stage_dir / "review" / "governance" / "governance_signal.json").exists()


def test_run_stage_review_script_supports_explicit_context_args(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
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


def test_issue_spawned_reviewer_receipt_script_writes_receipt(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "issue_spawned_reviewer_receipt.py"
    receipt_path = stage_dir / "review" / "request" / "spawned_reviewer_receipt.yaml"
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
            "--spawned-agent-id",
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
    assert receipt_payload["spawned_agent_id"] == "reviewer-child-agent"


def test_audit_reviewer_write_scope_script_writes_pass_artifact(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "audit_reviewer_write_scope.py"
    audit_path = stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml"
    audit_path.unlink()

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
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "audit_reviewer_write_scope.py"
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


def test_run_stage_review_script_rewrites_stale_result_to_match_active_request(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

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

    assert result.returncode == 0
    result_payload = yaml.safe_load(
        (stage_dir / "review" / "result" / "adversarial_review_result.yaml").read_text(encoding="utf-8")
    )
    assert result_payload["review_cycle_id"] == "cycle-1"
    assert result_payload["reviewed_program_dir"] == "program/mandate"
    assert result_payload["reviewed_program_entrypoint"] == "run_stage.py"
    assert sorted(result_payload["reviewed_artifact_paths"]) == sorted(
        [
            "mandate.md",
            "research_scope.md",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
    )


def test_run_stage_review_script_rejects_review_cycle_mismatch(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "runtime" / "scripts" / "run_stage_review.py"

    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "stale-cycle",
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
            "reviewed_program_dir": "program/mandate",
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": [
                "mandate.md",
                "research_scope.md",
                "time_split.json",
                "parameter_grid.yaml",
                "run_config.toml",
                "artifact_catalog.md",
                "field_dictionary.md",
            ],
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
    assert "review_cycle_id" in result.stderr
