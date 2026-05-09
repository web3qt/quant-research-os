from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import runtime.tools.install_runtime as install_runtime
from runtime.tools.install_runtime import InstallError, check_install, install_qros, list_skill_dirs, resolve_install_mode
from runtime.tools.uv_runtime_env import RuntimeEnvMetadata, UvRuntimeError


@pytest.fixture(autouse=True)
def fake_repo_local_uv_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_runtime_env(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
        python_bin = runtime_root / ".venv" / "bin" / "python"
        python_bin.parent.mkdir(parents=True, exist_ok=True)
        python_bin.write_text("#!/bin/sh\n", encoding="utf-8")

        lock_path = runtime_root / "uv.lock"
        lock_text = "PyYAML==6.0.2\npyarrow==20.0.0\n"
        lock_path.write_text(lock_text, encoding="utf-8")

        return RuntimeEnvMetadata(
            python_executable=str(python_bin.resolve()),
            python_version="3.12.9",
            lock_path=str(lock_path.resolve()),
            lock_digest=hashlib.sha256(lock_text.encode("utf-8")).hexdigest(),
        )

    monkeypatch.setattr(install_runtime, "ensure_repo_local_uv_runtime", fake_runtime_env)


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
    assert (install_root / ".qros" / ".venv" / "bin" / "python").exists()
    assert (install_root / ".qros" / "uv.lock").exists()
    assert not (install_root / ".qros" / "tools").exists()
    assert not (install_root / ".qros" / "scripts").exists()
    assert not (install_root / ".qros" / "docs").exists()
    assert not (install_root / ".qros" / "contracts").exists()
    manifest_path = install_root / ".qros" / "install-manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["host"] == "codex"
    assert manifest["install_mode"] == "repo-local"
    assert (home_root / ".codex" / "skills" / "qros-progress" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-progress" / "agents" / "openai.yaml").exists()
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "agents" / "openai.yaml").exists()
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()
    assert "qros-mandate-review" in manifest["installed_skills"]
    assert "qros-progress" in manifest["installed_skills"]
    assert "qros-train-freeze-author" in manifest["installed_skills"]
    assert "qros-test-evidence-author" in manifest["installed_skills"]
    assert "qros-backtest-ready-author" in manifest["installed_skills"]
    assert "qros-holdout-validation-author" in manifest["installed_skills"]
    assert "source_git_commit" in manifest
    assert "source_repo_path" in manifest
    assert "source_git_dirty" in manifest
    assert "source_git_status_short" in manifest
    assert "python_executable" in manifest
    assert "python_version" in manifest
    assert manifest["source_repo_path"] == str(repo_root.resolve())
    assert isinstance(manifest["source_git_dirty"], bool)
    assert isinstance(manifest["source_git_status_short"], list)
    assert manifest["python_executable"] == str(Path(sys.executable).resolve())
    assert manifest["python_version"].startswith(f"{sys.version_info.major}.{sys.version_info.minor}")
    assert manifest["runtime_python_executable"] == str(
        (install_root / ".qros" / ".venv" / "bin" / "python").resolve()
    )
    assert manifest["runtime_python_version"] == "3.12.9"
    assert manifest["runtime_lock_path"] == str((install_root / ".qros" / "uv.lock").resolve())
    assert manifest["runtime_lock_digest"] == hashlib.sha256(
        (install_root / ".qros" / "uv.lock").read_bytes()
    ).hexdigest()
    assert ".qros.tmp-" not in (install_root / ".qros" / "uv.lock").read_text(encoding="utf-8")
    assert manifest["installed_runtime_files"] == [
        "bin/qros-agent-eval",
        "bin/qros-audit-reviewer",
        "bin/qros-check-stage-entry",
        "bin/qros-factor-diagnostics",
        "bin/qros-progress",
        "bin/qros-review",
        "bin/qros-review-cycle",
        "bin/qros-review-preflight",
        "bin/qros-session",
        "bin/qros-signal-diagnostics",
        "bin/qros-start-review",
        "bin/qros-update",
        "bin/qros-validate-stage",
        "bin/qros-verify",
        "bin/qros-wrapper-lib",
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
    assert (home_root / ".codex" / "skills" / "qros-progress" / "SKILL.md").exists()
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
    assert manifest["source_repo_path"] == str(repo_root.resolve())
    assert isinstance(manifest["source_git_dirty"], bool)
    assert isinstance(manifest["source_git_status_short"], list)
    assert manifest["python_executable"] == str(Path(sys.executable).resolve())
    assert manifest["python_version"].startswith(f"{sys.version_info.major}.{sys.version_info.minor}")
    assert manifest["runtime_python_executable"] == str(
        (install_root / ".qros" / ".venv" / "bin" / "python").resolve()
    )
    assert manifest["runtime_python_version"] == "3.12.9"
    assert manifest["runtime_lock_path"] == str((install_root / ".qros" / "uv.lock").resolve())
    assert manifest["runtime_lock_digest"] == hashlib.sha256(
        (install_root / ".qros" / "uv.lock").read_bytes()
    ).hexdigest()


def test_repo_local_install_manifest_ignores_staging_dir_when_repo_root_is_install_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    home_root = tmp_path / "home"
    repo_root.mkdir()
    home_root.mkdir()
    shutil.copytree(Path.cwd() / "skills", repo_root / "skills")
    shutil.copytree(Path.cwd() / "runtime" / "bin", repo_root / "runtime" / "bin")
    (repo_root / ".gitignore").write_text(".qros/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QROS Test"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "qros-test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_root, check=True, capture_output=True, text=True)
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=repo_root, home=home_root, mode="repo-local")

    manifest = json.loads((repo_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_git_dirty"] is False
    assert not any(".qros.tmp-" in line for line in manifest["source_git_status_short"])
    assert ".qros.tmp-" not in (repo_root / ".qros" / "uv.lock").read_text(encoding="utf-8")


def test_repo_local_install_manifest_keeps_tracked_changes_under_qros_tmp_like_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    home_root = tmp_path / "home"
    repo_root.mkdir()
    home_root.mkdir()
    shutil.copytree(Path.cwd() / "skills", repo_root / "skills")
    shutil.copytree(Path.cwd() / "runtime" / "bin", repo_root / "runtime" / "bin")
    tracked_file = repo_root / "experiments" / ".qros.tmp-real" / "config.py"
    tracked_file.parent.mkdir(parents=True)
    tracked_file.write_text("VALUE = 'clean'\n", encoding="utf-8")
    (repo_root / ".gitignore").write_text(".qros/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QROS Test"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "qros-test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo_root, check=True, capture_output=True, text=True)
    tracked_file.write_text("VALUE = 'dirty'\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=repo_root, home=home_root, mode="repo-local")

    manifest = json.loads((repo_root / ".qros" / "install-manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_git_dirty"] is True
    assert any(".qros.tmp-real/config.py" in line for line in manifest["source_git_status_short"])


def test_check_install_reports_source_commit_drift_with_update_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")
    manifest_path = install_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_git_commit"] = "stale-installed-revision"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok, messages = check_install(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    message = "\n".join(messages)
    assert ok is False
    assert "QROS install drift detected" in message
    assert "installed source_git_commit: stale-installed-revision" in message
    assert "current source_git_commit:" in message
    assert "qros-update" in message
    assert "Restart Codex" in message


def test_check_install_reports_runtime_lock_drift_with_update_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")
    (install_root / ".qros" / "uv.lock").write_text("mutated lock\n", encoding="utf-8")

    ok, messages = check_install(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    message = "\n".join(messages)
    assert ok is False
    assert "QROS runtime lock drift detected" in message
    assert "installed runtime_lock_digest:" in message
    assert "current runtime_lock_digest:" in message
    assert "qros-update" in message


def test_check_install_reports_missing_runtime_lock_with_update_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")
    (install_root / ".qros" / "uv.lock").unlink()

    ok, messages = check_install(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    message = "\n".join(messages)
    assert ok is False
    assert "missing runtime lock:" in message
    assert str(install_root / ".qros" / "uv.lock") in message
    assert "qros-update" in message


def test_check_install_reports_source_repo_path_drift_with_installed_and_current_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")
    manifest_path = install_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_repo_path"] = "/tmp/not-the-active-qros-source"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ok, messages = check_install(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    message = "\n".join(messages)
    assert ok is False
    assert "QROS source repo path drift detected:" in message
    assert "installed source_repo_path:" in message
    assert "current source_repo_path:" in message
    assert "fix: run qros-update from the active research repo" in message


def test_check_install_reports_source_git_dirty_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    install_root.mkdir()
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")
    manifest_path = install_root / ".qros" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_git_dirty"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(install_runtime, "_git_status_short", lambda repo_root: " M runtime/tools/install_runtime.py\n")

    ok, messages = check_install(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    message = "\n".join(messages)
    assert ok is False
    assert "QROS source_git_dirty drift detected:" in message
    assert "installed source_git_dirty: false" in message
    assert "current source_git_dirty: true" in message
    assert "fix: commit, stash, or reinstall QROS from the intended source checkout" in message


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
    assert result.skills_written.count("qros-progress") == 1
    assert result.skills_written.count("qros-stage-display") == 1
    assert (home_root / ".codex" / "skills" / "qros-progress" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-research-session" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-mandate-review" / "SKILL.md").exists()
    assert (home_root / ".codex" / "skills" / "qros-stage-display" / "SKILL.md").exists()
    assert not (home_root / ".codex" / "skills" / "mandate").exists()
    assert (install_root / ".qros" / "bin" / "qros-session").exists()
    assert (install_root / ".qros" / "bin" / "qros-progress").exists()
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


def test_repo_local_install_preserves_existing_runtime_when_uv_provisioning_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = Path.cwd()
    install_root = tmp_path / "installed-repo"
    runtime_root = install_root / ".qros"
    old_update = runtime_root / "bin" / "qros-update"
    old_manifest = runtime_root / "install-manifest.json"
    install_root.mkdir()
    old_update.parent.mkdir(parents=True)
    old_update.write_text("old update\n", encoding="utf-8")
    old_manifest.write_text('{"old": true}\n', encoding="utf-8")
    home_root = tmp_path / "home"
    home_root.mkdir()
    monkeypatch.setenv("HOME", str(home_root))

    def fail_runtime_env(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
        raise UvRuntimeError("boom")

    monkeypatch.setattr(install_runtime, "ensure_repo_local_uv_runtime", fail_runtime_env)

    with pytest.raises(InstallError, match="boom"):
        install_qros(repo_root=repo_root, cwd=install_root, home=home_root, mode="repo-local")

    assert old_update.read_text(encoding="utf-8") == "old update\n"
    assert old_manifest.read_text(encoding="utf-8") == '{"old": true}\n'
