from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from subprocess import run
import sys

from tests.helpers.repo_paths import REPO_ROOT


def _copy_repo_fixture(tmp_path: Path) -> Path:
    repo_root = REPO_ROOT
    fixture_root = tmp_path / "fixture-repo"
    shutil.copytree(
        repo_root,
        fixture_root,
        ignore=shutil.ignore_patterns(
            ".git",
            ".worktrees",
            ".pytest_cache",
            ".qros",
            ".venv",
            ".omx",
            "__pycache__",
            "*.pyc",
        ),
    )
    return fixture_root


def _combined_output(result) -> str:
    return f"{result.stdout}\n{result.stderr}"


def _seed_repo_local_python(env: dict[str, str]) -> None:
    python312 = shutil.which("python3.12", path=env.get("PATH"))
    if python312:
        env["QROS_PYTHON"] = python312


def test_setup_repo_local_installs_into_current_repo(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    _seed_repo_local_python(env)

    result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result.returncode == 0
    assert (project_root / ".qros" / "install-manifest.json").exists()
    assert (project_root / ".qros" / "bin" / "qros-session").exists()
    assert (project_root / ".qros" / "bin" / "qros-update").exists()
    assert (project_root / "AGENTS.md").exists()
    assert "QROS Research Repo Agent Contract" in (project_root / "AGENTS.md").read_text(encoding="utf-8")
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()

    session_result = run(
        [str(project_root / ".qros" / "bin" / "qros-session"), "--raw-idea", "BTC leads high-liquidity alts"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert session_result.returncode == 0, session_result.stderr
    assert (project_root / "outputs").exists()


def test_setup_user_global_installs_into_home(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"

    result = run(
        ["./setup", "--host", "codex", "--mode", "user-global"],
        check=False,
        capture_output=True,
        text=True,
        cwd=fixture_root,
        env=env,
    )

    assert result.returncode == 0
    assert (home_root / ".codex" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()
    assert not (home_root / ".qros").exists()


def test_setup_check_reports_incomplete_install(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    _seed_repo_local_python(env)
    result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local", "--check"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    assert result.returncode != 0
    assert "missing manifest" in result.stdout or "missing manifest" in result.stderr


def test_repo_local_wrapper_blocks_missing_source_repo_path_drift(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    _seed_repo_local_python(env)

    setup_result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )
    assert setup_result.returncode == 0

    manifest_path = project_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_repo_path"] = "/tmp/not-the-active-qros-source"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = run(
        [str(project_root / ".qros" / "bin" / "qros-session"), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    output = _combined_output(result)
    assert result.returncode != 0
    assert "QROS source repo path drift detected:" in output
    assert "QROS_ALLOW_PROVENANCE_DRIFT=1" in output


def test_repo_local_wrapper_blocks_expected_source_repo_mismatch_with_override(
    tmp_path: Path,
) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    expected_source = tmp_path / "expected-source"
    expected_source.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    _seed_repo_local_python(env)

    setup_result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )
    assert setup_result.returncode == 0

    mismatch_env = env | {"QROS_EXPECTED_SOURCE_REPO": str(expected_source)}
    blocked = run(
        [str(project_root / ".qros" / "bin" / "qros-session"), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=mismatch_env,
    )

    blocked_output = _combined_output(blocked)
    assert blocked.returncode != 0
    assert "QROS source repo path drift detected:" in blocked_output
    assert "expected source_repo_path from QROS_EXPECTED_SOURCE_REPO:" in blocked_output
    assert "QROS_ALLOW_PROVENANCE_DRIFT=1" in blocked_output

    override_env = mismatch_env | {"QROS_ALLOW_PROVENANCE_DRIFT": "1"}
    allowed = run(
        [str(project_root / ".qros" / "bin" / "qros-session"), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=override_env,
    )

    allowed_output = _combined_output(allowed)
    assert allowed.returncode == 0, allowed_output
    assert "QROS provenance drift override active via QROS_ALLOW_PROVENANCE_DRIFT=1" in allowed_output


def test_qros_update_emits_recovery_diagnostics_instead_of_guard_block(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    project_root = tmp_path / "research-project"
    project_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"
    _seed_repo_local_python(env)

    setup_result = run(
        [str(fixture_root / "setup"), "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )
    assert setup_result.returncode == 0

    manifest_path = project_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_repo_path"] = "/tmp/not-the-active-qros-source"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = run(
        [str(project_root / ".qros" / "bin" / "qros-update"), "--help"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_root,
        env=env,
    )

    output = _combined_output(result)
    assert "QROS source repo path drift detected:" in output
    assert "fix: run qros-update from the active research repo" in output
    assert "Unable to locate QROS runtime root" in output
