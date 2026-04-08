from __future__ import annotations

import os
import shutil
from pathlib import Path
from subprocess import run


def _copy_repo_fixture(tmp_path: Path) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_root = tmp_path / "fixture-repo"
    shutil.copytree(
        repo_root,
        fixture_root,
        ignore=shutil.ignore_patterns(".git", ".worktrees", ".pytest_cache", "__pycache__", "*.pyc"),
    )
    return fixture_root


def test_setup_repo_local_installs_into_current_repo(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    result = run(
        ["./setup", "--host", "codex", "--mode", "repo-local"],
        check=False,
        capture_output=True,
        text=True,
        cwd=fixture_root,
    )

    assert result.returncode == 0
    assert (fixture_root / ".qros" / "install-manifest.json").exists()
    assert (fixture_root / ".qros" / "bin" / "qros-session").exists()
    assert (fixture_root / ".qros" / "skills" / "qros-mandate-review" / "SKILL.md").exists()


def test_setup_user_global_installs_into_home(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = os.environ.copy()
    env["HOME"] = str(home_root)

    result = run(
        ["./setup", "--host", "codex", "--mode", "user-global"],
        check=False,
        capture_output=True,
        text=True,
        cwd=fixture_root,
        env=env,
    )

    assert result.returncode == 0
    assert (home_root / ".qros" / "install-manifest.json").exists()
    assert (home_root / ".qros" / "bin" / "qros-session").exists()
    assert (home_root / ".qros" / "skills" / "qros-mandate-review" / "SKILL.md").exists()


def test_setup_check_reports_incomplete_install(tmp_path: Path) -> None:
    fixture_root = _copy_repo_fixture(tmp_path)
    result = run(
        ["./setup", "--host", "codex", "--mode", "repo-local", "--check"],
        check=False,
        capture_output=True,
        text=True,
        cwd=fixture_root,
    )

    assert result.returncode != 0
    assert "missing manifest" in result.stdout or "missing manifest" in result.stderr
