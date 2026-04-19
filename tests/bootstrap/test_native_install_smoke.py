import hashlib
from pathlib import Path
from subprocess import run

import yaml

from tests.helpers.repo_paths import REPO_ROOT
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    run_reviewer_write_scope_audit,
    write_reviewer_write_scope_baseline,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> Path:
    stage_dir = tmp_path / "project" / "outputs" / "topic_a" / "mandate"
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
            "requested_reviewer_identity": "codex-reviewer",
            "requested_reviewer_session_id": "local-review-session",
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
            "reviewer_identity": "codex-reviewer",
            "reviewer_role": "reviewer",
            "reviewer_session_id": "local-review-session",
            "reviewer_mode": "adversarial",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewer_execution_mode": "spawned_agent",
            "reviewer_context_source": "explicit_handoff_only",
            "reviewer_history_inheritance": "none",
            "handoff_manifest_digest": handoff_manifest_digest,
            "reviewed_program_dir": "program/mandate",
            "reviewed_program_entrypoint": "run_stage.py",
            "reviewed_artifact_paths": required_artifact_paths,
            "reviewed_provenance_paths": required_provenance_paths,
            "review_loop_outcome": "CLOSURE_READY_PASS",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "downstream_permissions": [],
        },
    )
    run_reviewer_write_scope_audit(stage_dir)
    (stage_dir / "program_execution_manifest.json").write_text("ok\n", encoding="utf-8")
    return stage_dir


def test_qros_session_wrapper_writes_outputs_to_current_working_dir(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    project_root = tmp_path / "project"
    project_root.mkdir()
    nested_dir = project_root / "research" / "notes"
    nested_dir.mkdir(parents=True)

    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [str(repo_root / "runtime" / "bin" / "qros-session"), "--raw-idea", "BTC leads high-liquidity alts"],
        cwd=nested_dir,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (nested_dir / "outputs").exists()
    assert not (project_root / "outputs").exists()


def test_qros_session_wrapper_honors_explicit_cwd_for_outputs_root(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    project_root = tmp_path / "project"
    project_root.mkdir()
    nested_dir = project_root / "research" / "notes"
    nested_dir.mkdir(parents=True)

    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [
            str(repo_root / "runtime" / "bin" / "qros-session"),
            "--cwd",
            str(nested_dir),
            "--raw-idea",
            "BTC leads high-liquidity alts",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (nested_dir / "outputs").exists()
    assert not (project_root / "outputs").exists()


def test_qros_review_wrapper_runs_in_current_stage_dir(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    project_root = tmp_path / "project"
    project_root.mkdir()
    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    stage_dir = _prepare_mandate_stage(tmp_path)

    result = run(
        [str(repo_root / "runtime" / "bin" / "qros-review")],
        cwd=stage_dir,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (stage_dir / "review" / "closure" / "stage_completion_certificate.yaml").exists()


def test_qros_session_wrapper_delegates_usage_errors_to_python_entrypoint(tmp_path: Path) -> None:
    repo_root = REPO_ROOT
    project_root = tmp_path / "project"
    project_root.mkdir()
    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [str(repo_root / "runtime" / "bin" / "qros-session")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "unbound variable" not in result.stderr
    assert "Either --lineage-id or --raw-idea must be provided" in result.stderr
