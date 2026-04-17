from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from runtime.tools.install_runtime import InstallError, check_install, install_qros, list_skill_dirs, resolve_install_mode


def test_resolve_install_mode_prefers_repo_local_when_skill_tree_exists(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "skills").mkdir()

    assert resolve_install_mode("auto", project_root) == "repo-local"


def test_repo_local_install_writes_skills_globally_and_runtime_locally(
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
    assert (install_root / ".qros").exists()
    assert (home_root / ".codex" / "skills").exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
    assert not (install_root / ".qros" / "tools").exists()
    assert not (install_root / ".qros" / "scripts").exists()
    assert not (install_root / ".qros" / "docs").exists()
    assert not (install_root / ".qros" / "contracts").exists()
    manifest_path = install_root / ".qros" / "install-manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["host"] == "codex"
    assert manifest["install_mode"] == "repo-local"
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "agents" / "openai.yaml").exists()
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()
    assert "qros-mandate-review" in manifest["installed_skills"]
    assert "qros-train-freeze-author" in manifest["installed_skills"]
    assert "qros-test-evidence-author" in manifest["installed_skills"]
    assert "qros-backtest-ready-author" in manifest["installed_skills"]
    assert "qros-holdout-validation-author" in manifest["installed_skills"]
    assert "source_git_commit" in manifest
    assert manifest["installed_runtime_files"] == [
        "bin/qros-review",
        "bin/qros-session",
        "bin/qros-spawn-reviewer",
        "bin/qros-update",
        "bin/qros-verify",
    ]


def test_user_global_install_writes_skills_and_install_manifest_under_home(
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
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-research-session" / "SKILL.md").exists()
    assert (home_root / ".codex" / "qros").exists()
    assert (home_root / ".codex" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".qros").exists()


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


def test_list_skill_dirs_rejects_duplicate_flattened_skill_names(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    source_root = repo_root / "skills"
    source_root.mkdir(parents=True)
    first = source_root / "mandate" / "qros-mandate-review"
    second = source_root / "archive" / "qros-mandate-review"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / "SKILL.md").write_text("name: qros-mandate-review\n", encoding="utf-8")
    (second / "SKILL.md").write_text("name: qros-mandate-review\n", encoding="utf-8")

    with pytest.raises(InstallError, match="duplicate skill bundle names"):
        list_skill_dirs(repo_root)


def test_repo_local_install_flattens_grouped_skill_bundles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    shutil.copytree(Path.cwd() / "skills", repo_root / "skills")
    for name in (
        "runtime/bin",
        "runtime/scripts",
        "runtime/tools",
        "runtime/hooks",
        "templates",
        "docs/guides",
        "docs/README.codex.md",
        "contracts",
    ):
        source = Path.cwd() / name
        destination = repo_root / name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    install_root = tmp_path / "install"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    result = install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    assert "qros-research-session" in result.skills_written
    assert result.skills_written.count("qros-stage-display") == 1
    assert (home_root / ".codex" / "skills" / "qros-research-session" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "SKILL.md").exists()
    assert not (home_root / ".codex" / "skills" / "mandate").exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
    assert not (install_root / ".qros" / "tools").exists()


def test_repo_local_reinstall_prunes_stale_runtime_mirror_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    stale_tools = install_root / ".qros" / "tools"
    stale_docs = install_root / ".qros" / "docs"
    stale_tools.mkdir(parents=True)
    stale_docs.mkdir(parents=True)
    (stale_tools / "old.py").write_text("print('stale')\n", encoding="utf-8")
    (stale_docs / "old.md").write_text("stale\n", encoding="utf-8")

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    assert not stale_tools.exists()
    assert not stale_docs.exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
