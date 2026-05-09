from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.tools.uv_runtime_env import UvRuntimeError, ensure_repo_local_uv_runtime


def _write_fake_uv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
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
                "exit 0",
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
                "  if grep -q 'PyYAML' \"$requirements_path\"; then",
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


def test_ensure_repo_local_uv_runtime_creates_python312_venv_and_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    _write_fake_uv(fake_bin / "uv")
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    runtime_root = tmp_path / ".qros"
    metadata = ensure_repo_local_uv_runtime(runtime_root=runtime_root, repo_root=Path.cwd())

    assert (runtime_root / ".venv" / "bin" / "python").exists()
    assert (runtime_root / "uv.lock").exists()
    requirements_text = (runtime_root / "runtime-requirements.txt").read_text(encoding="utf-8")
    assert "PyYAML>=6.0" in requirements_text
    assert "pyarrow>=20.0" in requirements_text
    lock_text = (runtime_root / "uv.lock").read_text(encoding="utf-8")
    assert "PyYAML==6.0.2" in lock_text
    assert "pyarrow==20.0.0" in lock_text
    assert "requirements_sha256" not in lock_text
    assert ".qros.tmp-" not in lock_text
    assert metadata.python_version == "3.12.9"
    assert metadata.python_executable.endswith(".qros/.venv/bin/python")
    assert metadata.lock_path.endswith(".qros/uv.lock")
    assert len(metadata.lock_digest) == 64


def test_ensure_repo_local_uv_runtime_resolves_relative_runtime_root_from_repo_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    other_cwd = tmp_path / "other-cwd"
    _write_fake_uv(fake_bin / "uv")
    other_cwd.mkdir()
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.chdir(other_cwd)

    metadata = ensure_repo_local_uv_runtime(runtime_root=Path(".qros"), repo_root=tmp_path)

    assert (tmp_path / ".qros" / ".venv" / "bin" / "python").exists()
    assert (tmp_path / ".qros" / "uv.lock").exists()
    requirements_text = (tmp_path / ".qros" / "runtime-requirements.txt").read_text(encoding="utf-8")
    assert requirements_text.startswith("# QROS runtime dependencies are not declared")
    lock_text = (tmp_path / ".qros" / "uv.lock").read_text(encoding="utf-8")
    assert "# empty pinned runtime lock" in lock_text
    assert "requirements_sha256" not in lock_text
    assert ".qros.tmp-" not in lock_text
    assert not (other_cwd / ".qros").exists()
    assert metadata.python_executable == str((tmp_path / ".qros" / ".venv" / "bin" / "python").resolve())
    assert metadata.lock_path == str((tmp_path / ".qros" / "uv.lock").resolve())


def test_ensure_repo_local_uv_runtime_writes_comment_only_requirements_when_no_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    repo_root = tmp_path / "repo"
    runtime_root = repo_root / ".qros"
    _write_fake_uv(fake_bin / "uv")
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "empty-runtime"',
                'version = "0.0.0"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PATH", f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    ensure_repo_local_uv_runtime(runtime_root=runtime_root, repo_root=repo_root)

    requirements_text = (runtime_root / "runtime-requirements.txt").read_text(encoding="utf-8")
    assert requirements_text.startswith("# QROS runtime dependencies are not declared")
    assert "PyYAML" not in requirements_text


def test_ensure_repo_local_uv_runtime_requires_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))

    with pytest.raises(UvRuntimeError, match="uv is required"):
        ensure_repo_local_uv_runtime(runtime_root=tmp_path / ".qros", repo_root=tmp_path)
