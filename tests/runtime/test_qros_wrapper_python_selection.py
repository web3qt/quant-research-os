from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER_LIB = REPO_ROOT / "runtime" / "bin" / "qros-wrapper-lib"
RUNTIME_BIN = REPO_ROOT / "runtime" / "bin"


def _sh(path: Path) -> str:
    return shlex.quote(str(path))


def _write_fake_python(path: Path, *, major: int, minor: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -euo pipefail",
                f"export QROS_FAKE_PYTHON_VERSION='{major}.{minor}.0'",
                "if [ \"${1:-}\" = \"-\" ]; then",
                f"  if [ '{major}.{minor}' = '3.12' ]; then exit 0; else exit 1; fi",
                "fi",
                "if [ \"${1:-}\" = \"-c\" ]; then",
                f"  echo '{major}.{minor}.0'",
                "  exit 0",
                "fi",
                "exit 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_fake_uv(path: Path, python_path: Path | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "#!/bin/bash",
        "set -euo pipefail",
        "if [ \"${1:-}\" = \"python\" ] && [ \"${2:-}\" = \"find\" ] && [ \"${3:-}\" = \"3.12\" ]; then",
    ]
    if python_path is None:
        body.extend(["  exit 1", "fi"])
    else:
        body.extend([f"  printf '%s\\n' {shlex.quote(str(python_path))}", "  exit 0", "fi"])
    body.extend(["exit 1"])
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    path.chmod(0o755)


def _run_selector(tmp_path: Path, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    script_dir = tmp_path / ".qros" / "bin"
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "qros-wrapper-lib").write_text(WRAPPER_LIB.read_text(encoding="utf-8"), encoding="utf-8")
    runner = tmp_path / "run-selector.sh"
    runner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"source {_sh(script_dir / 'qros-wrapper-lib')}",
                f"qros_select_python_bin {_sh(script_dir)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    merged_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("QROS_") and not k.startswith("UV_")
    }
    if env:
        merged_env.update(env)
    return subprocess.run(["/bin/bash", str(runner)], check=False, capture_output=True, text=True, env=merged_env)


def _run_runtime_lock_check(
    tmp_path: Path,
    *,
    manifest: dict[str, str],
    lock_text: str,
    mode: str | None = None,
) -> subprocess.CompletedProcess[str]:
    qros_dir = tmp_path / ".qros"
    script_dir = qros_dir / "bin"
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "qros-wrapper-lib").write_text(WRAPPER_LIB.read_text(encoding="utf-8"), encoding="utf-8")
    (qros_dir / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (qros_dir / "uv.lock").write_text(lock_text, encoding="utf-8")

    py312 = tmp_path / "python312"
    py312.write_text(
        f"#!/usr/bin/env bash\nexec {shlex.quote(sys.executable)} \"$@\"\n",
        encoding="utf-8",
    )
    py312.chmod(0o755)

    runner = tmp_path / "run-lock-check.sh"
    runner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"source {_sh(script_dir / 'qros-wrapper-lib')}",
                " ".join(
                    part
                    for part in [
                        "qros_verify_runtime_lock",
                        _sh(script_dir),
                        _sh(py312),
                        shlex.quote(mode) if mode is not None else "",
                    ]
                    if part
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    return subprocess.run(["/bin/bash", str(runner)], check=False, capture_output=True, text=True)


def test_selector_prefers_qros_python_when_it_is_python312(tmp_path: Path) -> None:
    py312 = tmp_path / "custom" / "python312"
    _write_fake_python(py312, major=3, minor=12)

    completed = _run_selector(
        tmp_path,
        env={"QROS_PYTHON": str(py312), "PATH": "/usr/bin:/bin"},
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(py312)


def test_selector_prefers_repo_local_venv_before_uv_and_system(tmp_path: Path) -> None:
    venv_python = tmp_path / ".qros" / ".venv" / "bin" / "python"
    uv_python = tmp_path / "uv-python" / "python"
    system_bin = tmp_path / "system-bin"
    _write_fake_python(venv_python, major=3, minor=12)
    _write_fake_python(uv_python, major=3, minor=12)
    _write_fake_python(system_bin / "python3.12", major=3, minor=12)
    _write_fake_uv(system_bin / "uv", uv_python)

    completed = _run_selector(tmp_path, env={"PATH": str(system_bin)})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(venv_python)


def test_selector_uses_uv_python_find_when_no_venv_exists(tmp_path: Path) -> None:
    uv_python = tmp_path / "uv-python" / "python"
    system_bin = tmp_path / "system-bin"
    _write_fake_python(uv_python, major=3, minor=12)
    _write_fake_uv(system_bin / "uv", uv_python)

    completed = _run_selector(tmp_path, env={"PATH": str(system_bin)})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(uv_python)


def test_selector_uses_python312_when_uv_has_no_runtime(tmp_path: Path) -> None:
    system_bin = tmp_path / "system-bin"
    _write_fake_python(system_bin / "python3.12", major=3, minor=12)
    _write_fake_uv(system_bin / "uv", None)

    completed = _run_selector(tmp_path, env={"PATH": str(system_bin)})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "python3.12"


def test_selector_rejects_python39_candidates_and_fails_closed(tmp_path: Path) -> None:
    system_bin = tmp_path / "system-bin"
    _write_fake_python(tmp_path / ".qros" / ".venv" / "bin" / "python", major=3, minor=9)
    _write_fake_python(system_bin / "python3.12", major=3, minor=9)
    _write_fake_uv(system_bin / "uv", None)

    completed = _run_selector(tmp_path, env={"PATH": str(system_bin)})

    assert completed.returncode != 0
    assert "QROS requires Python 3.12" in completed.stderr
    assert "run qros-update" in completed.stderr


def test_runtime_lock_check_passes_when_digest_matches(tmp_path: Path) -> None:
    lock_text = 'python = "3.12"\n'
    digest = hashlib.sha256(lock_text.encode("utf-8")).hexdigest()

    completed = _run_runtime_lock_check(
        tmp_path,
        manifest={
            "runtime_lock_digest": digest,
            "runtime_lock_path": ".qros/uv.lock",
        },
        lock_text=lock_text,
    )

    assert completed.returncode == 0, completed.stderr


def test_runtime_lock_check_fails_when_digest_drifts(tmp_path: Path) -> None:
    completed = _run_runtime_lock_check(
        tmp_path,
        manifest={
            "runtime_lock_digest": "0" * 64,
            "runtime_lock_path": ".qros/uv.lock",
        },
        lock_text='python = "3.11"\n',
    )

    assert completed.returncode != 0
    assert "QROS runtime lock drift detected" in completed.stderr
    assert "run qros-update" in completed.stderr


def test_runtime_lock_check_recovery_mode_warns_but_allows_digest_drift(tmp_path: Path) -> None:
    completed = _run_runtime_lock_check(
        tmp_path,
        manifest={
            "runtime_lock_digest": "0" * 64,
            "runtime_lock_path": ".qros/uv.lock",
        },
        lock_text='python = "3.11"\n',
        mode="recovery",
    )

    assert completed.returncode == 0, completed.stderr
    assert "QROS runtime lock drift detected" in completed.stderr
    assert "run qros-update" in completed.stderr


def test_all_qros_wrappers_use_shared_python_selector() -> None:
    wrappers = sorted(
        path
        for path in RUNTIME_BIN.iterdir()
        if path.name.startswith("qros-") and path.name != "qros-wrapper-lib" and path.is_file()
    )
    assert wrappers

    offenders: list[str] = []
    for wrapper in wrappers:
        text = wrapper.read_text(encoding="utf-8")
        if "qros_select_python_bin" not in text:
            offenders.append(f"{wrapper.name}: missing qros_select_python_bin")
        if "qros_verify_runtime_lock" not in text:
            offenders.append(f"{wrapper.name}: missing qros_verify_runtime_lock")
        if wrapper.name == "qros-update" and 'qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN" recovery' not in text:
            offenders.append(f"{wrapper.name}: lock verification must use recovery mode")
        if "select_python_bin()" in text:
            offenders.append(f"{wrapper.name}: local select_python_bin")
        if 'for CANDIDATE in python python3' in text or 'command -v python3' in text:
            offenders.append(f"{wrapper.name}: legacy python discovery")
        if "Python >=3.11" in text or "Python 3.11+" in text:
            offenders.append(f"{wrapper.name}: legacy Python 3.11 message")

    assert offenders == []
