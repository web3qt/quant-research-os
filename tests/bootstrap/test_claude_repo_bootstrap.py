from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from runtime.tools.install_runtime import (
    InstallError,
    SUPPORTED_HOSTS,
    check_install,
    install_qros,
)
from runtime.tools.update_runtime import global_manifest_path, run_qros_update


# -- helpers (copied from test_qros_update_script.py; private there) --

REPO_ROOT = Path(__file__).resolve().parents[2]


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


# -- tests --


def test_supported_hosts_includes_claude_code() -> None:
    assert "claude-code" in SUPPORTED_HOSTS
    assert "codex" in SUPPORTED_HOSTS


def test_claude_code_repo_local_install_writes_runtime_locally_and_global_skills_under_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root,
        cwd=install_root,
        home=home_root,
        mode="repo-local",
        host="claude-code",
    )

    assert result.mode == "repo-local"
    assert (install_root / ".qros").exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
    assert (install_root / ".qros" / "bin" / "qros-progress").exists()
    assert (install_root / ".qros" / "bin" / "qros-resume").exists()
    assert not (install_root / ".qros" / "tools").exists()

    assert (home_root / ".claude" / "skills").exists()
    assert (home_root / ".claude" / "skills" / "qros-progress" / "SKILL.md").exists()
    assert (home_root / ".claude" / "skills" / "qros-research-session" / "SKILL.md").exists()

    assert not (home_root / ".codex" / "skills").exists()

    manifest_path = install_root / ".qros" / "install-manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["host"] == "claude-code"
    assert manifest["install_mode"] == "repo-local"
    assert "qros-progress" in manifest["installed_skills"]


def test_claude_code_user_global_install_writes_skills_under_claude_and_manifest_under_claude_qros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root,
        cwd=cwd,
        home=home_root,
        mode="user-global",
        host="claude-code",
    )

    assert result.mode == "user-global"
    assert (home_root / ".claude" / "skills").exists()
    assert (home_root / ".claude" / "skills" / "qros-research-session" / "SKILL.md").exists()
    assert (home_root / ".claude" / "qros").exists()
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".codex" / "skills").exists()
    assert not (home_root / ".codex" / "qros").exists()


def test_claude_code_check_install_reports_host_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(
        repo_root=repo_root,
        cwd=install_root,
        home=home_root,
        mode="repo-local",
        host="claude-code",
    )

    ok, messages = check_install(
        repo_root=repo_root,
        cwd=install_root,
        home=home_root,
        mode="repo-local",
        host="codex",
    )
    assert ok is False
    assert any("host mismatch" in m for m in messages)


def test_claude_code_manifest_writes_host_claude_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(
        repo_root=repo_root,
        cwd=install_root,
        home=home_root,
        mode="repo-local",
        host="claude-code",
    )

    manifest = json.loads(
        (install_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["host"] == "claude-code"
    assert manifest["install_mode"] == "repo-local"


def test_codex_install_behavior_unchanged_after_claude_code_host_added(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(
        repo_root=repo_root,
        cwd=install_root,
        home=home_root,
        mode="repo-local",
        host="codex",
    )

    assert result.mode == "repo-local"
    assert (home_root / ".codex" / "skills").exists()
    assert (home_root / ".codex" / "skills" / "qros-progress" / "SKILL.md").exists()
    manifest = json.loads(
        (install_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["host"] == "codex"


def test_global_manifest_path_respects_host() -> None:
    home = Path("/home/user")
    assert global_manifest_path(home, host="codex") == home / ".codex" / "qros" / "install-manifest.json"
    assert global_manifest_path(home, host="claude-code") == home / ".claude" / "qros" / "install-manifest.json"


def test_claude_code_update_refreshes_claude_global_and_repo_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
        host="claude-code",
    )

    assert result.source_repo == managed_repo.resolve()
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".claude" / "skills" / "qros-update" / "SKILL.md").exists()
    assert (target_cwd / ".qros" / "install-manifest.json").exists()
    assert (target_cwd / ".qros" / "bin" / "qros-update").exists()
    assert result.source_git_commit

    local_manifest = json.loads(
        (target_cwd / ".qros" / "install-manifest.json").read_text(encoding="utf-8")
    )
    assert local_manifest["host"] == "claude-code"

    assert not (home_root / ".codex" / "skills").exists()
    assert not (home_root / ".codex" / "qros").exists()


def test_install_runtime_rejects_unknown_host() -> None:
    with pytest.raises(InstallError, match="unsupported host"):
        install_qros(
            repo_root=Path.cwd(),
            cwd=Path.cwd(),
            home=Path.home(),
            mode="repo-local",
            host="gemini-cli",
        )
