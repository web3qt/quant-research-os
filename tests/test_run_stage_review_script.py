from pathlib import Path
from subprocess import run
import sys

import yaml


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

    _write_yaml(stage_dir / "review_findings.yaml", {"reviewer_identity": "codex"})
    return stage_dir


def test_run_stage_review_script_creates_closure_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "scripts" / "run_stage_review.py"

    result = run(
        [sys.executable, str(script_path)],
        cwd=stage_dir,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Final verdict: PASS" in result.stdout
    assert (stage_dir / "stage_completion_certificate.yaml").exists()


def test_run_stage_review_script_supports_explicit_context_args(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    stage_dir = _prepare_mandate_stage(tmp_path)
    script_path = repo_root / "scripts" / "run_stage_review.py"

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
    assert "Stage: mandate" in result.stdout
