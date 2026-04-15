from pathlib import Path
import os
from subprocess import run
import sys

import yaml


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
            "required_artifact_paths": [
                "mandate.md",
                "research_scope.md",
                "time_split.json",
                "parameter_grid.yaml",
                "run_config.toml",
                "artifact_catalog.md",
                "field_dictionary.md",
            ],
            "required_provenance_paths": ["program_execution_manifest.json"],
            "required_reviewer_mode": "adversarial",
        },
    )
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "cycle-1",
            "reviewer_identity": "reviewer-agent",
            "reviewer_role": "reviewer",
            "reviewer_session_id": "review-session",
            "reviewer_mode": "adversarial",
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
    return stage_dir


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
    assert (stage_dir / "review" / "governance" / "governance_signal.json").exists()


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


def test_run_stage_review_script_rewrites_stale_result_to_match_active_request(tmp_path: Path) -> None:
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
