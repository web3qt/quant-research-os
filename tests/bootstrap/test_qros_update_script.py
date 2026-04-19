from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
import sys

from tests.helpers.repo_paths import REPO_ROOT
from runtime.tools.update_runtime import resolve_source_repo, run_qros_update


def _copy_repo_fixture(tmp_path: Path) -> Path:
    repo_root = REPO_ROOT
    fixture_root = tmp_path / "fixture-repo"
    shutil.copytree(
        repo_root,
        fixture_root,
        ignore=shutil.ignore_patterns(".git", ".worktrees", ".pytest_cache", "__pycache__", "*.pyc"),
    )
    return fixture_root


def _git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout.strip()


def _init_origin_repo(tmp_path: Path) -> tuple[Path, Path]:
    source_repo = _copy_repo_fixture(tmp_path)
    _git(["init", "-b", "main"], cwd=source_repo)
    _git(["config", "user.name", "QROS Test"], cwd=source_repo)
    _git(["config", "user.email", "qros-test@example.com"], cwd=source_repo)
    _git(["add", "-A"], cwd=source_repo)
    _git(["commit", "-m", "initial"], cwd=source_repo)

    origin_repo = tmp_path / "origin.git"
    _git(["init", "--bare", str(origin_repo)], cwd=tmp_path)
    _git(["remote", "add", "origin", str(origin_repo)], cwd=source_repo)
    _git(["push", "-u", "origin", "main"], cwd=source_repo)
    return source_repo, origin_repo


def _clone_managed_repo(origin_repo: Path, managed_repo: Path) -> None:
    subprocess.run(
        ["git", "clone", "--branch", "main", str(origin_repo), str(managed_repo)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_resolve_source_repo_prefers_global_manifest(tmp_path: Path, monkeypatch) -> None:
    home_root = tmp_path / "home"
    home_root.mkdir()
    managed_repo = tmp_path / "managed-repo"
    managed_repo.mkdir()
    manifest_path = home_root / ".codex" / "qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"source_repo_path": str(managed_repo)}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home_root))

    resolved = resolve_source_repo(
        explicit_source_repo=None,
        home=home_root,
        repo_root_fallback=tmp_path / "fallback-repo",
    )

    assert resolved == managed_repo.resolve()


def test_run_qros_update_refreshes_user_global_and_repo_local(tmp_path: Path, monkeypatch) -> None:
    _, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = run_qros_update(
        target_cwd=target_cwd,
        home=home_root,
        explicit_source_repo=managed_repo,
        repo_root_fallback=managed_repo,
        repo_url=str(origin_repo),
    )

    assert result.source_repo == managed_repo.resolve()
    assert (home_root / ".codex" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".codex" / "skills" / "qros-update" / "SKILL.md").exists()
    assert (target_cwd / ".qros" / "install-manifest.json").exists()
    assert (target_cwd / ".qros" / "bin" / "qros-update").exists()
    assert result.source_git_commit


def test_run_qros_update_self_heals_dirty_managed_repo(tmp_path: Path, monkeypatch) -> None:
    source_repo, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    # Advance origin/main so the updater must both clean local drift and fast-forward.
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "QROS Test"
    env["GIT_AUTHOR_EMAIL"] = "qros-test@example.com"
    env["GIT_COMMITTER_NAME"] = "QROS Test"
    env["GIT_COMMITTER_EMAIL"] = "qros-test@example.com"
    (source_repo / "README.md").write_text("updated\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=source_repo, env=env)
    _git(["commit", "-m", "advance origin"], cwd=source_repo, env=env)
    _git(["push", "origin", "main"], cwd=source_repo)
    expected_head = _git(["rev-parse", "HEAD"], cwd=source_repo)

    (managed_repo / "README.md").write_text("dirty local change\n", encoding="utf-8")
    (managed_repo / "local.tmp").write_text("untracked\n", encoding="utf-8")

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = run_qros_update(
        target_cwd=target_cwd,
        home=home_root,
        explicit_source_repo=managed_repo,
        repo_root_fallback=managed_repo,
        repo_url=str(origin_repo),
    )

    assert result.source_git_commit == expected_head
    assert _git(["rev-parse", "HEAD"], cwd=managed_repo) == expected_head
    assert _git(["status", "--short"], cwd=managed_repo) == ""


def test_qros_update_wrapper_refreshes_current_repo(tmp_path: Path, monkeypatch) -> None:
    _, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    monkeypatch.setenv("HOME", str(home_root))
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env['PATH']}"

    completed = subprocess.run(
        [
            str(managed_repo / "runtime" / "bin" / "qros-update"),
            "--cwd",
            str(target_cwd),
            "--source-repo",
            str(managed_repo),
            "--repo-url",
            str(origin_repo),
        ],
        cwd=target_cwd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr
    assert "QROS updated to" in completed.stdout
    assert (target_cwd / ".qros" / "bin" / "qros-update").exists()
