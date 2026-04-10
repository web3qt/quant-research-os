from pathlib import Path

import yaml

from tools.review_skillgen.review_engine import run_stage_review


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

    return stage_dir


def _write_review_request(stage_dir: Path, *, author_identity: str = "author-agent") -> None:
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


def _write_review_result(stage_dir: Path, *, outcome: str = "CLOSURE_READY_PASS", reviewer_identity: str = "reviewer-agent") -> None:
    _write_yaml(
        stage_dir / "review" / "result" / "adversarial_review_result.yaml",
        {
            "review_cycle_id": "cycle-1",
            "reviewer_identity": reviewer_identity,
            "reviewer_role": "reviewer",
            "reviewer_session_id": "review-session",
            "reviewer_mode": "adversarial",
            "review_loop_outcome": outcome,
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


def test_run_stage_review_pass_path(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_review_request(stage_dir)
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
    assert (stage_dir / "review" / "governance" / "governance_signal.json").exists()
    assert payload["governance"]["appended_entries"]


def test_run_stage_review_downgrades_to_retry_when_required_output_missing(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    (stage_dir / "author" / "formal" / "parameter_grid.yaml").unlink()
    _write_review_request(stage_dir)
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
    assert (stage_dir / "review" / "governance" / "governance_signal.json").exists()
    assert payload["governance"]["appended_entries"]
