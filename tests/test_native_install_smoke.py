from pathlib import Path
from subprocess import run

import yaml


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _prepare_mandate_stage(tmp_path: Path) -> Path:
    stage_dir = tmp_path / "project" / "outputs" / "topic_a" / "mandate"
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


def test_qros_session_wrapper_writes_outputs_to_current_working_dir(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    project_root = tmp_path / "project"
    project_root.mkdir()
    nested_dir = project_root / "research" / "notes"
    nested_dir.mkdir(parents=True)

    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [str(repo_root / "bin" / "qros-session"), "--raw-idea", "BTC leads high-liquidity alts"],
        cwd=nested_dir,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (nested_dir / "outputs").exists()
    assert not (project_root / "outputs").exists()


def test_qros_session_wrapper_honors_explicit_cwd_for_outputs_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    project_root = tmp_path / "project"
    project_root.mkdir()
    nested_dir = project_root / "research" / "notes"
    nested_dir.mkdir(parents=True)

    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [
            str(repo_root / "bin" / "qros-session"),
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
    repo_root = Path(__file__).resolve().parents[1]
    project_root = tmp_path / "project"
    project_root.mkdir()
    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
    stage_dir = _prepare_mandate_stage(tmp_path)

    result = run(
        [str(repo_root / "bin" / "qros-review")],
        cwd=stage_dir,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert (stage_dir / "stage_completion_certificate.yaml").exists()


def test_qros_session_wrapper_delegates_usage_errors_to_python_entrypoint(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    project_root = tmp_path / "project"
    project_root.mkdir()
    run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)

    result = run(
        [str(repo_root / "bin" / "qros-session")],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "unbound variable" not in result.stderr
    assert "Either --lineage-id or --raw-idea must be provided" in result.stderr
