from pathlib import Path

import yaml

from tools.review_skillgen.review_engine import run_stage_review


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> Path:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

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
        (stage_dir / name).write_text("ok\n", encoding="utf-8")

    return stage_dir


def test_run_stage_review_pass_path(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_yaml(stage_dir / "review_findings.yaml", {"reviewer_identity": "codex"})

    payload = run_stage_review(cwd=stage_dir)

    assert payload["stage"] == "mandate"
    assert payload["final_verdict"] == "PASS"
    assert payload["blocking_findings"] == []
    assert (stage_dir / "stage_completion_certificate.yaml").exists()


def test_run_stage_review_downgrades_to_retry_when_required_output_missing(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    (stage_dir / "parameter_grid.yaml").unlink()
    _write_yaml(stage_dir / "review_findings.yaml", {"recommended_verdict": "PASS"})

    payload = run_stage_review(cwd=stage_dir)

    assert payload["final_verdict"] == "RETRY"
    assert any("parameter_grid.yaml" in item for item in payload["blocking_findings"])


def test_run_stage_review_accepts_pass_for_retry_with_rollback_metadata(tmp_path: Path) -> None:
    stage_dir = _prepare_mandate_stage(tmp_path)
    _write_yaml(
        stage_dir / "review_findings.yaml",
        {
            "reviewer_identity": "codex",
            "recommended_verdict": "PASS FOR RETRY",
            "rollback_stage": "mandate",
            "allowed_modifications": ["clarify wording only"],
            "reservation_findings": ["needs controlled rerun log"],
        },
    )

    payload = run_stage_review(cwd=stage_dir)

    assert payload["final_verdict"] == "PASS FOR RETRY"
    assert payload["rollback_stage"] == "mandate"
    assert payload["allowed_modifications"] == ["clarify wording only"]
