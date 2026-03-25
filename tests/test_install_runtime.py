from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.install_runtime import check_install, install_qros, resolve_install_mode


def test_resolve_install_mode_prefers_repo_local_when_agents_exist(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".agents").mkdir()

    assert resolve_install_mode("auto", project_root) == "repo-local"


def test_repo_local_install_writes_skills_runtime_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    assert result.mode == "repo-local"
    assert (install_root / ".agents" / "skills").exists()
    assert (install_root / ".qros").exists()
    manifest_path = install_root / ".qros" / "install-manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["host"] == "codex"
    assert manifest["install_mode"] == "repo-local"
    assert "qros-mandate-review" in manifest["installed_skills"]
    assert "qros-train-freeze-author" in manifest["installed_skills"]
    assert "qros-test-evidence-author" in manifest["installed_skills"]
    assert "qros-backtest-ready-author" in manifest["installed_skills"]
    assert "qros-holdout-validation-author" in manifest["installed_skills"]
    assert "source_git_commit" in manifest


def test_user_global_install_writes_skills_and_runtime_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(repo_root=repo_root, cwd=cwd, home=home_root, mode="user-global")

    assert result.mode == "user-global"
    assert (home_root / ".codex" / "skills").exists()
    assert (home_root / ".qros").exists()
    assert (home_root / ".qros" / "install-manifest.json").exists()


def test_check_install_reports_missing_assets_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    ok, messages = check_install(repo_root=repo_root, cwd=cwd, home=home_root, mode="repo-local")

    assert ok is False
    assert messages
    assert not (cwd / ".qros" / "install-manifest.json").exists()


def test_manifest_fields_include_install_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    manifest_path = install_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["host"] == "codex"
    assert manifest["install_mode"] == "repo-local"
    assert manifest["installed_skills"]
    assert manifest["installed_runtime_files"]
    assert manifest["source_git_commit"]
