from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
import sys

import pytest

import runtime.tools.install_runtime as install_runtime
from tests.helpers.repo_paths import REPO_ROOT
from runtime.tools.update_runtime import resolve_source_repo, resolve_update_host, run_qros_update
from runtime.tools.uv_runtime_env import RuntimeEnvMetadata


def _write_fake_uv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fake_python = path.parent / "fake-python-3.12"
    fake_python.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "if [ \"${1:-}\" = \"-\" ] && [ \"$#\" -eq 1 ]; then exit 0; fi",
                f'exec "{sys.executable}" "$@"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "if [ \"${1:-}\" = \"python\" ] && [ \"${2:-}\" = \"find\" ]; then",
                f'  printf "%s\\n" "{fake_python}"',
                "  exit 0",
                "fi",
                "if [ \"${1:-}\" = \"python\" ] && [ \"${2:-}\" = \"install\" ]; then exit 0; fi",
                "if [ \"${1:-}\" = \"venv\" ]; then",
                "  if [[ \" $* \" != *\" --allow-existing \"* ]]; then",
                "    echo \"fake uv venv requires --allow-existing\" >&2",
                "    exit 1",
                "  fi",
                "  venv_path=\"${@: -1}\"",
                "  mkdir -p \"$venv_path/bin\"",
                "  cat > \"$venv_path/bin/python\" <<'PY'",
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "if [ \"${1:-}\" = \"-c\" ]; then echo '3.12.9'; exit 0; fi",
                "if [ \"${1:-}\" = \"-\" ]; then exit 0; fi",
                f'exec "{sys.executable}" "$@"',
                "PY",
                "  chmod +x \"$venv_path/bin/python\"",
                "  exit 0",
                "fi",
                "if [ \"${1:-}\" = \"pip\" ] && [ \"${2:-}\" = \"compile\" ]; then",
                "  if [[ \" $* \" != *\" --no-header \"* ]]; then",
                "    echo \"fake uv compile requires --no-header\" >&2",
                "    exit 1",
                "  fi",
                "  lock_path=''",
                "  requirements_path=\"${@: -1}\"",
                "  while [ \"$#\" -gt 0 ]; do",
                "    if [ \"$1\" = \"-o\" ]; then lock_path=\"$2\"; shift 2; continue; fi",
                "    shift",
                "  done",
                "  if [ -z \"$lock_path\" ]; then echo 'missing -o lock path' >&2; exit 1; fi",
                "  if grep -q 'PyYAML' \"$requirements_path\" 2>/dev/null; then",
                "    printf '%s\\n' 'PyYAML==6.0.2' 'pyarrow==20.0.0' > \"$lock_path\"",
                "  else",
                "    printf '%s\\n' '# empty pinned runtime lock' > \"$lock_path\"",
                "  fi",
                "  exit 0",
                "fi",
                "if [ \"${1:-}\" = \"pip\" ] && [ \"${2:-}\" = \"sync\" ]; then exit 0; fi",
                "echo \"unexpected fake uv args: $*\" >&2",
                "exit 1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


@pytest.fixture(autouse=True)
def fake_uv_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    _write_fake_uv(fake_bin / "uv")
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("QROS_TEST_FAKE_UV_BIN", str(fake_bin))

    def fake_runtime_env(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
        python_bin = runtime_root / ".venv" / "bin" / "python"
        python_bin.parent.mkdir(parents=True, exist_ok=True)
        python_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        lock_path = runtime_root / "uv.lock"
        lock_text = "PyYAML==6.0.2\npyarrow==20.0.0\n"
        lock_path.write_text(lock_text, encoding="utf-8")
        return RuntimeEnvMetadata(
            python_executable=str(python_bin.resolve()),
            python_version="3.12.9",
            lock_path=str(lock_path.resolve()),
            lock_digest=install_runtime._file_sha256(lock_path),
        )

    monkeypatch.setattr(install_runtime, "ensure_repo_local_uv_runtime", fake_runtime_env)


def _assert_fake_uv_first(env: dict[str, str]) -> None:
    fake_bin = Path(env["QROS_TEST_FAKE_UV_BIN"]).resolve()
    uv_path = shutil.which("uv", path=env["PATH"])
    assert uv_path is not None
    assert Path(uv_path).resolve().parent == fake_bin


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


def test_resolve_update_host_prefers_explicit_qros_host_env(tmp_path: Path) -> None:
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()

    assert resolve_update_host(
        "auto",
        target_cwd=target_cwd,
        environ={"QROS_HOST": "claude-code", "CODEX_THREAD_ID": "codex-thread"},
    ) == "claude-code"


def test_resolve_update_host_reinterprets_legacy_codex_default_as_auto(tmp_path: Path) -> None:
    target_cwd = tmp_path / "research-project"
    manifest_path = target_cwd / ".qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"host": "claude-code"}, ensure_ascii=False),
        encoding="utf-8",
    )

    assert resolve_update_host(
        "codex",
        target_cwd=target_cwd,
        environ={},
        legacy_default_host=True,
    ) == "claude-code"


def test_resolve_update_host_uses_current_runtime_environment_before_repo_local_manifest(tmp_path: Path) -> None:
    target_cwd = tmp_path / "research-project"
    manifest_path = target_cwd / ".qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"host": "codex"}, ensure_ascii=False),
        encoding="utf-8",
    )

    assert resolve_update_host(
        "auto",
        target_cwd=target_cwd,
        environ={"CLAUDE_CODE_ENTRYPOINT": "cli"},
    ) == "claude-code"


def test_resolve_update_host_uses_repo_local_manifest_when_runtime_environment_is_ambiguous(tmp_path: Path) -> None:
    target_cwd = tmp_path / "research-project"
    manifest_path = target_cwd / ".qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"host": "claude-code"}, ensure_ascii=False),
        encoding="utf-8",
    )

    assert resolve_update_host(
        "auto",
        target_cwd=target_cwd,
        environ={},
    ) == "claude-code"


def test_resolve_update_host_detects_codex_runtime_environment(tmp_path: Path) -> None:
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()

    assert resolve_update_host(
        "auto",
        target_cwd=target_cwd,
        environ={"CODEX_SANDBOX": "seatbelt", "CODEX_THREAD_ID": "codex-thread"},
    ) == "codex"


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
        environ={},
    )

    assert result.source_repo == managed_repo.resolve()
    assert (home_root / ".codex" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".codex" / "skills" / "qros-update" / "SKILL.md").exists()
    assert (target_cwd / ".qros" / "install-manifest.json").exists()
    assert (target_cwd / ".qros" / "bin" / "qros-update").exists()
    assert result.source_git_commit


def test_run_qros_update_auto_host_uses_repo_local_manifest(tmp_path: Path, monkeypatch) -> None:
    _, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    manifest_path = target_cwd / ".qros" / "install-manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"host": "claude-code"}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home_root))

    result = run_qros_update(
        target_cwd=target_cwd,
        home=home_root,
        explicit_source_repo=managed_repo,
        repo_root_fallback=managed_repo,
        repo_url=str(origin_repo),
        environ={},
    )

    assert result.source_repo == managed_repo.resolve()
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert (home_root / ".claude" / "skills" / "qros-update" / "SKILL.md").exists()
    assert not (home_root / ".codex" / "qros").exists()
    local_manifest = json.loads((target_cwd / ".qros" / "install-manifest.json").read_text(encoding="utf-8"))
    assert local_manifest["host"] == "claude-code"


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
    env["PATH"] = f"{env['PATH']}{os.pathsep}{Path(sys.executable).parent}"
    _assert_fake_uv_first(env)

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


def test_qros_update_wrapper_auto_host_respects_qros_host_env(tmp_path: Path, monkeypatch) -> None:
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
    env["QROS_HOST"] = "claude-code"
    env["PATH"] = f"{env['PATH']}{os.pathsep}{Path(sys.executable).parent}"
    _assert_fake_uv_first(env)

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
    assert "Host: claude-code" in completed.stdout
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".codex" / "qros").exists()


def test_qros_update_wrapper_explicit_codex_host_wins_over_qros_host_env(tmp_path: Path, monkeypatch) -> None:
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
    env["QROS_HOST"] = "claude-code"
    env["PATH"] = f"{env['PATH']}{os.pathsep}{Path(sys.executable).parent}"
    _assert_fake_uv_first(env)

    completed = subprocess.run(
        [
            str(managed_repo / "runtime" / "bin" / "qros-update"),
            "--host",
            "codex",
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
    assert "Host: codex" in completed.stdout
    assert (home_root / ".codex" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".claude" / "qros").exists()


def test_qros_update_wrapper_legacy_codex_default_still_respects_qros_host_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _, origin_repo = _init_origin_repo(tmp_path)
    managed_repo = tmp_path / "managed-repo"
    _clone_managed_repo(origin_repo, managed_repo)

    home_root = tmp_path / "home"
    home_root.mkdir()
    target_cwd = tmp_path / "research-project"
    target_cwd.mkdir()
    legacy_bin = tmp_path / "legacy-qros-update"
    legacy_bin.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'TARGET_CWD="$PWD"',
                "ARGS=()",
                'while [ "$#" -gt 0 ]; do',
                '  case "$1" in',
                "    --cwd)",
                '      TARGET_CWD="$2"',
                "      shift 2",
                "      ;;",
                "    *)",
                '      ARGS+=("$1")',
                "      shift",
                "      ;;",
                "  esac",
                "done",
                f'exec "{sys.executable}" "{managed_repo / "runtime" / "scripts" / "run_qros_update.py"}" --cwd "$TARGET_CWD" --host codex "${{ARGS[@]}}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    legacy_bin.chmod(0o755)
    monkeypatch.setenv("HOME", str(home_root))
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    env["QROS_HOST"] = "claude-code"
    env["PATH"] = f"{env['PATH']}{os.pathsep}{Path(sys.executable).parent}"
    _assert_fake_uv_first(env)

    completed = subprocess.run(
        [
            str(legacy_bin),
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
    assert "Host: claude-code" in completed.stdout
    assert (home_root / ".claude" / "qros" / "install-manifest.json").exists()
    assert not (home_root / ".codex" / "qros").exists()
