# QROS uv Python 3.12 Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make repo-local QROS wrappers use a uv-provisioned Python 3.12 runtime instead of falling back to system `python` / `python3`.

**Architecture:** Add one shared Bash selector in `runtime/bin/qros-wrapper-lib`, then migrate every `runtime/bin/qros-*` wrapper to use it. Add a small Python uv runtime helper for install/update/bootstrap to create `.qros/.venv`, write `.qros/uv.lock`, and record lock/runtime metadata in `install-manifest.json`; normal wrappers only verify and fail closed.

**Tech Stack:** Bash wrappers, Python 3.12, `uv`, Python standard library, pytest, existing QROS install/update helpers.

---

## Scope

This plan implements only the Python 3.12 + uv runtime hardening layer from `docs/superpowers/specs/2026-05-09-qros-uv-python312-runtime-design.md`.

It intentionally does not implement the later A/B/C governance fixes:

- forged `program_execution_manifest.json` prevention
- independent reviewer identity enforcement
- factor direction / proxy return / autocorrelation semantic gates

Those should be separate plans after wrappers stop forcing agents to bypass QROS entrypoints.

## File Map

- Modify: `runtime/bin/qros-wrapper-lib`
  - Add shared `qros_select_python_bin`.
  - Add shared runtime lock digest verification.
  - Keep existing `qros_resolve_runtime_root`.
- Modify: `runtime/bin/qros-agent-eval`
- Modify: `runtime/bin/qros-audit-reviewer`
- Modify: `runtime/bin/qros-check-stage-entry`
- Modify: `runtime/bin/qros-factor-diagnostics`
- Modify: `runtime/bin/qros-progress`
- Modify: `runtime/bin/qros-review`
- Modify: `runtime/bin/qros-review-cycle`
- Modify: `runtime/bin/qros-review-preflight`
- Modify: `runtime/bin/qros-session`
- Modify: `runtime/bin/qros-signal-diagnostics`
- Modify: `runtime/bin/qros-start-review`
- Modify: `runtime/bin/qros-update`
- Modify: `runtime/bin/qros-validate-stage`
- Modify: `runtime/bin/qros-verify`
  - Remove duplicated Python discovery and call `qros_select_python_bin "$SCRIPT_DIR"`.
- Create: `runtime/tools/uv_runtime_env.py`
  - uv detection, Python 3.12 installation, `.qros/.venv` creation, dependency lock/sync, lock digest metadata.
- Modify: `runtime/tools/install_runtime.py`
  - For repo-local installs, call `ensure_repo_local_uv_runtime`.
  - Add manifest fields for runtime Python and uv lock.
  - Include manifest checks for lock drift.
- Modify: `runtime/tools/update_runtime.py`
  - Ensure update path provisions repo-local runtime through `install_qros`.
- Modify: `tests/runtime/test_qros_wrapper_python_selection.py`
  - Shell-level tests for selector behavior and wrapper migration.
- Modify: `tests/bootstrap/test_install_runtime.py`
  - Manifest fields and lock digest tests.
- Modify: `tests/bootstrap/test_qros_update_script.py`
  - qros-update creates `.qros/.venv` / `.qros/uv.lock`.
- Modify: `tests/bootstrap/test_project_bootstrap.py`
  - Bootstrap exposes the new runtime expectation.
- Modify: `docs/guides/installation.md`
  - Document uv + Python 3.12 behavior and no implicit installs in ordinary commands.
- Modify: `docs/README.codex.md`
  - Keep setup/update instructions consistent with installation guide.

## Design Details

### Shared Bash Selector

Add this public function to `runtime/bin/qros-wrapper-lib`:

```bash
qros_select_python_bin() {
  local script_dir="$1"
  local qros_root
  qros_root="$(cd "$script_dir/.." && pwd)"

  local candidates=()
  if [ -n "${QROS_PYTHON:-}" ]; then
    candidates+=("$QROS_PYTHON")
  fi
  candidates+=("$qros_root/.venv/bin/python")

  local uv_python=""
  if command -v uv >/dev/null 2>&1; then
    uv_python="$(uv python find 3.12 2>/dev/null || true)"
    if [ -n "$uv_python" ]; then
      candidates+=("$uv_python")
    fi
  fi

  candidates+=("python3.12")

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -z "$candidate" ]; then
      continue
    fi
    if [[ "$candidate" != */* ]] && ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if [[ "$candidate" == */* ]] && [ ! -x "$candidate" ]; then
      continue
    fi
    if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)
PY
    then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  {
    echo "QROS requires Python 3.12 for repo-local runtime wrappers."
    echo "Recovery: run qros-update from the active research repo, or install uv and rerun bootstrap."
    echo "Checked: QROS_PYTHON, .qros/.venv/bin/python, uv python find 3.12, python3.12"
  } >&2
  return 1
}
```

Add this verification helper to the same file:

```bash
qros_verify_runtime_lock() {
  local script_dir="$1"
  local python_bin="$2"
  local manifest_path="$script_dir/../install-manifest.json"
  local lock_path="$script_dir/../uv.lock"

  "$python_bin" - "$manifest_path" "$lock_path" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
lock_path = Path(sys.argv[2])

if not manifest_path.exists():
    raise SystemExit(0)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
expected = str(manifest.get("runtime_lock_digest", "")).strip()
recorded_path = str(manifest.get("runtime_lock_path", "")).strip()

if not expected and not recorded_path:
    raise SystemExit(0)

if not lock_path.exists():
    print("QROS runtime lock missing: .qros/uv.lock", file=sys.stderr)
    print("Recovery: run qros-update from the active research repo", file=sys.stderr)
    raise SystemExit(1)

actual = hashlib.sha256(lock_path.read_bytes()).hexdigest()
if expected and actual != expected:
    print("QROS runtime lock drift detected:", file=sys.stderr)
    print(f"manifest: {manifest_path}", file=sys.stderr)
    print(f"expected runtime_lock_digest: {expected}", file=sys.stderr)
    print(f"current runtime_lock_digest: {actual}", file=sys.stderr)
    print("Recovery: run qros-update from the active research repo", file=sys.stderr)
    raise SystemExit(1)
PY
}
```

Each wrapper should use the same pattern:

```bash
source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" strict)"
```

`qros-update` is the exception only for provenance mode:

```bash
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" recovery)"
```

It still uses `qros_select_python_bin` and `qros_verify_runtime_lock`.

### uv Runtime Helper

Create `runtime/tools/uv_runtime_env.py` with these public functions:

```python
from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PYTHON_RUNTIME = "3.12"


class UvRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeEnvMetadata:
    python_executable: str
    python_version: str
    lock_path: str
    lock_digest: str


def ensure_repo_local_uv_runtime(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        raise UvRuntimeError(
            "uv is required to provision QROS Python 3.12 runtime. "
            "Install uv, then rerun qros-update from the active research repo."
        )

    runtime_root.mkdir(parents=True, exist_ok=True)
    lock_path = runtime_root / "uv.lock"
    requirements_path = _write_runtime_requirements(runtime_root=runtime_root)

    _run([uv_bin, "python", "install", PYTHON_RUNTIME], cwd=repo_root)
    _run([uv_bin, "venv", "--python", PYTHON_RUNTIME, str(runtime_root / ".venv")], cwd=repo_root)
    _run(
        [
            uv_bin,
            "pip",
            "install",
            "--python",
            str(runtime_root / ".venv" / "bin" / "python"),
            "-r",
            str(requirements_path),
        ],
        cwd=repo_root,
    )

    lock_path.write_text(
        "\n".join(
            [
                "# QROS repo-local runtime lock",
                "python = \"3.12\"",
                f"requirements_sha256 = \"{_sha256(requirements_path)}\"",
                "",
            ]
        ),
        encoding="utf-8",
    )

    python_bin = runtime_root / ".venv" / "bin" / "python"
    version = _python_version(python_bin)
    if not version.startswith("3.12."):
        raise UvRuntimeError(f"QROS managed runtime expected Python 3.12, found {version}")

    return RuntimeEnvMetadata(
        python_executable=str(python_bin.resolve()),
        python_version=version,
        lock_path=str(lock_path),
        lock_digest=_sha256(lock_path),
    )
```

The first implementation may install from an empty generated requirements file if the repo currently has no canonical dependency lock. This keeps the runtime environment lockable without inventing a dependency list in this patch. If QROS already has a canonical dependency source when this plan is executed, replace `_write_runtime_requirements` with a copy from that source and lock the copied file digest.

Implement these private helpers:

```python
def _write_runtime_requirements(*, runtime_root: Path) -> Path:
    requirements_path = runtime_root / "runtime-requirements.txt"
    requirements_path.write_text("# QROS runtime dependencies are stdlib-only in this lock revision.\n", encoding="utf-8")
    return requirements_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_version(python_bin: Path) -> str:
    completed = _run(
        [
            str(python_bin),
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:3])))",
        ],
        cwd=python_bin.parent,
    )
    return completed.stdout.strip()


def _run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise UvRuntimeError(f"command failed: {' '.join(args)}\n{detail}")
    return completed
```

## Task 1: Add failing wrapper selector tests

**Files:**
- Create: `tests/runtime/test_qros_wrapper_python_selection.py`

- [ ] **Step 1: Create shell-test helpers and first failing test**

Add:

```python
from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER_LIB = REPO_ROOT / "runtime" / "bin" / "qros-wrapper-lib"
RUNTIME_BIN = REPO_ROOT / "runtime" / "bin"


def _write_fake_python(path: Path, *, major: int, minor: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
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
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "if [ \"${1:-}\" = \"python\" ] && [ \"${2:-}\" = \"find\" ] && [ \"${3:-}\" = \"3.12\" ]; then",
    ]
    if python_path is None:
        body.extend(["  exit 1", "fi"])
    else:
        body.extend([f"  echo '{python_path}'", "  exit 0", "fi"])
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
                f"source '{script_dir / 'qros-wrapper-lib'}'",
                f"qros_select_python_bin '{script_dir}'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run([str(runner)], check=False, capture_output=True, text=True, env=merged_env)


def test_selector_prefers_qros_python_when_it_is_python312(tmp_path: Path) -> None:
    py312 = tmp_path / "custom" / "python312"
    _write_fake_python(py312, major=3, minor=12)

    completed = _run_selector(
        tmp_path,
        env={"QROS_PYTHON": str(py312), "PATH": "/usr/bin:/bin"},
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == str(py312)
```

- [ ] **Step 2: Run the new test and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py::test_selector_prefers_qros_python_when_it_is_python312 -v
```

Expected: FAIL because `qros_select_python_bin` is not defined.

## Task 2: Implement shared Python 3.12 selector

**Files:**
- Modify: `runtime/bin/qros-wrapper-lib`
- Test: `tests/runtime/test_qros_wrapper_python_selection.py`

- [ ] **Step 1: Add `qros_select_python_bin`**

Insert the shared selector from the "Shared Bash Selector" section above before `qros_resolve_runtime_root`.

- [ ] **Step 2: Run focused selector test**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py::test_selector_prefers_qros_python_when_it_is_python312 -v
```

Expected: PASS.

- [ ] **Step 3: Add selector precedence and rejection tests**

Append:

```python
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
```

- [ ] **Step 4: Run selector tests**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py -v
```

Expected: PASS.

## Task 3: Add runtime lock verification tests and helper

**Files:**
- Modify: `tests/runtime/test_qros_wrapper_python_selection.py`
- Modify: `runtime/bin/qros-wrapper-lib`

- [ ] **Step 1: Add failing tests for lock verification**

Append:

```python
def _run_lock_check(tmp_path: Path, *, manifest: dict[str, object], lock_text: str) -> subprocess.CompletedProcess[str]:
    script_dir = tmp_path / ".qros" / "bin"
    script_dir.mkdir(parents=True, exist_ok=True)
    (script_dir / "qros-wrapper-lib").write_text(WRAPPER_LIB.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / ".qros" / "install-manifest.json").write_text(
        __import__("json").dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )
    lock_path = tmp_path / ".qros" / "uv.lock"
    lock_path.write_text(lock_text, encoding="utf-8")
    py312 = tmp_path / "python312"
    py312.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                "exec python \"$@\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    py312.chmod(0o755)
    runner = tmp_path / "run-lock-check.sh"
    runner.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f"source '{script_dir / 'qros-wrapper-lib'}'",
                f"qros_verify_runtime_lock '{script_dir}' '{py312}'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    return subprocess.run([str(runner)], check=False, capture_output=True, text=True)


def test_runtime_lock_check_passes_when_digest_matches(tmp_path: Path) -> None:
    import hashlib

    lock_text = 'python = "3.12"\n'
    digest = hashlib.sha256(lock_text.encode("utf-8")).hexdigest()

    completed = _run_lock_check(
        tmp_path,
        manifest={"runtime_lock_digest": digest, "runtime_lock_path": ".qros/uv.lock"},
        lock_text=lock_text,
    )

    assert completed.returncode == 0, completed.stderr


def test_runtime_lock_check_fails_when_digest_drifts(tmp_path: Path) -> None:
    completed = _run_lock_check(
        tmp_path,
        manifest={"runtime_lock_digest": "0" * 64, "runtime_lock_path": ".qros/uv.lock"},
        lock_text='python = "3.12"\n',
    )

    assert completed.returncode != 0
    assert "QROS runtime lock drift detected" in completed.stderr
    assert "run qros-update" in completed.stderr
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py::test_runtime_lock_check_passes_when_digest_matches tests/runtime/test_qros_wrapper_python_selection.py::test_runtime_lock_check_fails_when_digest_drifts -v
```

Expected: FAIL because `qros_verify_runtime_lock` is not defined.

- [ ] **Step 3: Add `qros_verify_runtime_lock` to wrapper lib**

Insert the helper from the "Shared Bash Selector" section after `qros_select_python_bin`.

- [ ] **Step 4: Run wrapper lib tests**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py -v
```

Expected: PASS.

## Task 4: Migrate all runtime wrappers to shared selector

**Files:**
- Modify every `runtime/bin/qros-*` executable listed in File Map
- Modify: `tests/runtime/test_qros_wrapper_python_selection.py`

- [ ] **Step 1: Add failing scan test**

Append:

```python
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
        if "select_python_bin()" in text:
            offenders.append(f"{wrapper.name}: local select_python_bin")
        if 'for CANDIDATE in python python3' in text or 'command -v python3' in text:
            offenders.append(f"{wrapper.name}: legacy python discovery")
        if "Python >=3.11" in text or "Python 3.11+" in text:
            offenders.append(f"{wrapper.name}: legacy Python 3.11 message")

    assert offenders == []
```

- [ ] **Step 2: Run scan test and verify failure**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py::test_all_qros_wrappers_use_shared_python_selector -v
```

Expected: FAIL listing wrappers with legacy Python discovery.

- [ ] **Step 3: Update `runtime/bin/qros-session`**

Replace the local `select_python_bin` function and call with:

```bash
source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" strict)"
```

Keep all argument parsing and exit-code handling unchanged.

- [ ] **Step 4: Update `runtime/bin/qros-review`**

Use the same shared block as `qros-session`; keep its existing review arguments unchanged.

- [ ] **Step 5: Update simple exec wrappers**

In each wrapper below, replace the local Python discovery block with:

```bash
source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" strict)"
```

Wrappers:

- `runtime/bin/qros-agent-eval`
- `runtime/bin/qros-audit-reviewer`
- `runtime/bin/qros-check-stage-entry`
- `runtime/bin/qros-factor-diagnostics`
- `runtime/bin/qros-progress`
- `runtime/bin/qros-review-cycle`
- `runtime/bin/qros-review-preflight`
- `runtime/bin/qros-signal-diagnostics`
- `runtime/bin/qros-start-review`
- `runtime/bin/qros-validate-stage`
- `runtime/bin/qros-verify`

- [ ] **Step 6: Update `runtime/bin/qros-update`**

Use:

```bash
source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" recovery)"
```

Keep the rest of the wrapper unchanged.

- [ ] **Step 7: Run scan test**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py::test_all_qros_wrappers_use_shared_python_selector -v
```

Expected: PASS.

## Task 5: Add uv runtime provisioning helper

**Files:**
- Create: `runtime/tools/uv_runtime_env.py`
- Create: `tests/bootstrap/test_uv_runtime_env.py`

- [ ] **Step 1: Add tests with a fake `uv` binary**

Create `tests/bootstrap/test_uv_runtime_env.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from runtime.tools import uv_runtime_env
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
                "if [ \"${1:-}\" = \"pip\" ] && [ \"${2:-}\" = \"install\" ]; then exit 0; fi",
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

    metadata = ensure_repo_local_uv_runtime(runtime_root=tmp_path / ".qros", repo_root=tmp_path)

    assert (tmp_path / ".qros" / ".venv" / "bin" / "python").exists()
    assert (tmp_path / ".qros" / "uv.lock").exists()
    assert metadata.python_version == "3.12.9"
    assert metadata.python_executable.endswith(".qros/.venv/bin/python")
    assert metadata.lock_path.endswith(".qros/uv.lock")
    assert len(metadata.lock_digest) == 64


def test_ensure_repo_local_uv_runtime_requires_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    (tmp_path / "empty-bin").mkdir()

    with pytest.raises(UvRuntimeError, match="uv is required"):
        ensure_repo_local_uv_runtime(runtime_root=tmp_path / ".qros", repo_root=tmp_path)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python -m pytest tests/bootstrap/test_uv_runtime_env.py -v
```

Expected: FAIL because `runtime.tools.uv_runtime_env` does not exist.

- [ ] **Step 3: Create `runtime/tools/uv_runtime_env.py`**

Use the code from the "uv Runtime Helper" section.

- [ ] **Step 4: Run uv helper tests**

Run:

```bash
python -m pytest tests/bootstrap/test_uv_runtime_env.py -v
```

Expected: PASS.

## Task 6: Wire uv runtime into repo-local install manifest

**Files:**
- Modify: `runtime/tools/install_runtime.py`
- Modify: `tests/bootstrap/test_install_runtime.py`

- [ ] **Step 1: Add failing manifest assertions**

In `test_repo_local_install_writes_skills_globally_and_runtime_locally`, after existing manifest Python assertions, add:

```python
    assert (install_root / ".qros" / ".venv" / "bin" / "python").exists()
    assert (install_root / ".qros" / "uv.lock").exists()
    assert manifest["runtime_python_executable"].endswith(".qros/.venv/bin/python")
    assert manifest["runtime_python_version"].startswith("3.12.")
    assert manifest["runtime_lock_path"] == str(install_root / ".qros" / "uv.lock")
    assert len(manifest["runtime_lock_digest"]) == 64
```

In `test_manifest_fields_include_install_metadata`, add the same field assertions.

- [ ] **Step 2: Patch tests to avoid real uv**

Add this fixture near the top of `tests/bootstrap/test_install_runtime.py`:

```python
@pytest.fixture(autouse=True)
def fake_uv_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    from runtime.tools.uv_runtime_env import RuntimeEnvMetadata

    def _fake_runtime(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
        python_path = runtime_root / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True, exist_ok=True)
        python_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        python_path.chmod(0o755)
        lock_path = runtime_root / "uv.lock"
        lock_path.write_text('python = "3.12"\n', encoding="utf-8")
        return RuntimeEnvMetadata(
            python_executable=str(python_path),
            python_version="3.12.9",
            lock_path=str(lock_path),
            lock_digest="a" * 64,
        )

    monkeypatch.setattr(install_runtime, "ensure_repo_local_uv_runtime", _fake_runtime)
```

This fixture keeps install tests deterministic and does not call the real network or uv tool.

- [ ] **Step 3: Run install test and verify failure**

Run:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py::test_repo_local_install_writes_skills_globally_and_runtime_locally -v
```

Expected: FAIL because manifest fields are missing and `ensure_repo_local_uv_runtime` is not imported/called.

- [ ] **Step 4: Update install runtime imports**

In `runtime/tools/install_runtime.py`, add:

```python
from runtime.tools.uv_runtime_env import RuntimeEnvMetadata, UvRuntimeError, ensure_repo_local_uv_runtime
```

- [ ] **Step 5: Extend `build_manifest` signature**

Change:

```python
def build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    installed_skills: list[str],
    installed_runtime_files: list[str],
    host: str = "codex",
) -> dict[str, object]:
```

to:

```python
def build_manifest(
    *,
    repo_root: Path,
    target: InstallTarget,
    installed_skills: list[str],
    installed_runtime_files: list[str],
    runtime_env: RuntimeEnvMetadata | None = None,
    host: str = "codex",
) -> dict[str, object]:
```

Build the manifest in a local variable, then add runtime fields when present:

```python
    manifest: dict[str, object] = {
        "project_name": repo_root.name,
        "host": host,
        "install_mode": target.mode,
        "installed_at": datetime.now(UTC).isoformat(),
        "source_repo_path": str(repo_root),
        "source_git_commit": _git_commit(repo_root),
        "source_git_dirty": bool(git_status_short.strip()),
        "source_git_status_short": git_status_short.splitlines(),
        "python_executable": _python_executable(),
        "python_version": _python_version(),
        "skills_root": str(target.skills_root),
        "runtime_root": str(target.runtime_root),
        "installed_skills": installed_skills,
        "installed_runtime_files": installed_runtime_files,
        "version_marker": _git_commit(repo_root) or "unknown",
    }
    if runtime_env is not None:
        manifest.update(
            {
                "runtime_python_executable": runtime_env.python_executable,
                "runtime_python_version": runtime_env.python_version,
                "runtime_lock_path": runtime_env.lock_path,
                "runtime_lock_digest": runtime_env.lock_digest,
            }
        )
    return manifest
```

- [ ] **Step 6: Call uv helper for repo-local install**

In `install_qros`, after runtime assets are copied and before `build_manifest`, add:

```python
    runtime_env: RuntimeEnvMetadata | None = None
    if target.mode == "repo-local":
        try:
            runtime_env = ensure_repo_local_uv_runtime(runtime_root=target.runtime_root, repo_root=repo_root)
        except UvRuntimeError as exc:
            raise InstallError(str(exc)) from exc
```

Pass `runtime_env=runtime_env` into `build_manifest`.

- [ ] **Step 7: Update manifest field checks**

In `check_install`, extend the required manifest keys for repo-local installs:

```python
    if target.mode == "repo-local":
        for key in (
            "runtime_python_executable",
            "runtime_python_version",
            "runtime_lock_path",
            "runtime_lock_digest",
        ):
            if key not in manifest:
                messages.append(f"manifest missing field: {key}")
```

Add a lock digest check:

```python
    if target.mode == "repo-local":
        lock_path = target.runtime_root / "uv.lock"
        expected_digest = manifest.get("runtime_lock_digest")
        if not lock_path.exists():
            messages.append(f"missing runtime lock: {lock_path}")
        elif isinstance(expected_digest, str) and expected_digest.strip():
            current_digest = _file_sha256(lock_path)
            if current_digest != expected_digest:
                messages.append(
                    "\n".join(
                        [
                            "QROS runtime lock drift detected:",
                            f"manifest: {target.manifest_path}",
                            f"installed runtime_lock_digest: {expected_digest}",
                            f"current runtime_lock_digest: {current_digest}",
                            "fix: run qros-update from the active research repo",
                        ]
                    )
                )
```

Add helper:

```python
def _file_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()
```

- [ ] **Step 8: Run install tests**

Run:

```bash
python -m pytest tests/bootstrap/test_install_runtime.py -v
```

Expected: PASS.

## Task 7: Update qros-update tests for repo-local uv runtime

**Files:**
- Modify: `tests/bootstrap/test_qros_update_script.py`

- [ ] **Step 1: Add fake uv runtime fixture**

Add:

```python
import pytest
import runtime.tools.install_runtime as install_runtime
```

Then add:

```python
@pytest.fixture(autouse=True)
def fake_uv_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    from runtime.tools.uv_runtime_env import RuntimeEnvMetadata

    def _fake_runtime(*, runtime_root: Path, repo_root: Path) -> RuntimeEnvMetadata:
        python_path = runtime_root / ".venv" / "bin" / "python"
        python_path.parent.mkdir(parents=True, exist_ok=True)
        python_path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        python_path.chmod(0o755)
        lock_path = runtime_root / "uv.lock"
        lock_path.write_text('python = "3.12"\n', encoding="utf-8")
        return RuntimeEnvMetadata(
            python_executable=str(python_path),
            python_version="3.12.9",
            lock_path=str(lock_path),
            lock_digest="b" * 64,
        )

    monkeypatch.setattr(install_runtime, "ensure_repo_local_uv_runtime", _fake_runtime)
```

For subprocess wrapper tests in this file, monkeypatching the imported function will not cross process boundaries. In those tests, prepend a fake `uv` executable to `PATH` using the same fake script from `tests/bootstrap/test_uv_runtime_env.py`, or factor the fake writer into a local helper.

- [ ] **Step 2: Add manifest assertions**

In `test_run_qros_update_refreshes_user_global_and_repo_local`, after `.qros/bin/qros-update` assertion, add:

```python
    local_manifest = json.loads((target_cwd / ".qros" / "install-manifest.json").read_text(encoding="utf-8"))
    assert (target_cwd / ".qros" / ".venv" / "bin" / "python").exists()
    assert (target_cwd / ".qros" / "uv.lock").exists()
    assert local_manifest["runtime_python_version"].startswith("3.12.")
    assert len(local_manifest["runtime_lock_digest"]) == 64
```

- [ ] **Step 3: Run update tests**

Run:

```bash
python -m pytest tests/bootstrap/test_qros_update_script.py -v
```

Expected: PASS.

## Task 8: Update bootstrap tests and docs

**Files:**
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `docs/guides/installation.md`
- Modify: `docs/README.codex.md`
- Modify or add: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Update bootstrap expectations**

Find the test that asserts `.qros` outputs in `tests/bootstrap/test_project_bootstrap.py`. Add expectations that repo-local install includes:

```python
assert (project_root / ".qros" / ".venv" / "bin" / "python").exists()
assert (project_root / ".qros" / "uv.lock").exists()
```

If that test uses subprocess setup, provide fake `uv` on `PATH` instead of monkeypatching a Python function.

- [ ] **Step 2: Update installation guide**

In `docs/guides/installation.md`, replace the section that says `python_executable` and `python_version` are only future audit fields with:

```markdown
Repo-local `./.qros/` now owns a managed Python runtime:

- `./.qros/.venv/bin/python` must be Python 3.12.
- `./.qros/uv.lock` records the runtime lock.
- `./.qros/install-manifest.json` records `runtime_python_executable`, `runtime_python_version`, `runtime_lock_path`, and `runtime_lock_digest`.

`qros-update` / bootstrap uses `uv` to create or refresh this runtime. Ordinary commands such as `qros-session`, `qros-review`, `qros-progress`, diagnostics, preflight, and validators do not install dependencies as a side effect. They select Python in this order: `QROS_PYTHON`, `./.qros/.venv/bin/python`, `uv python find 3.12`, `python3.12`. If none is Python 3.12, they fail closed and ask you to run `qros-update`.
```

- [ ] **Step 3: Update Codex README**

In `docs/README.codex.md`, add the same operational rule in shorter form:

```markdown
QROS repo-local commands require Python 3.12. Run `qros-update` from the active research repo to create `./.qros/.venv` via `uv`; do not bypass `./.qros/bin/qros-*` by calling `runtime/scripts/*` directly to work around Python version problems.
```

- [ ] **Step 4: Add or update doc regression test**

In `tests/docs/test_install_docs.py`, add:

```python
def test_install_docs_describe_uv_python312_runtime() -> None:
    text = Path("docs/guides/installation.md").read_text(encoding="utf-8")

    assert "./.qros/.venv/bin/python" in text
    assert "Python 3.12" in text
    assert "./.qros/uv.lock" in text
    assert "runtime_lock_digest" in text
    assert "Ordinary commands" in text
    assert "do not install dependencies as a side effect" in text
```

- [ ] **Step 5: Run docs/bootstrap tests**

Run:

```bash
python -m pytest tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -v
```

Expected: PASS.

## Task 9: Focused verification

**Files:**
- No edits

- [ ] **Step 1: Run wrapper/runtime focused tests**

Run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py tests/bootstrap/test_uv_runtime_env.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_qros_update_script.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -v
```

Expected: PASS.

- [ ] **Step 2: Run required smoke tier**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 3: Decide whether full-smoke is required**

Do not run full-smoke by default for this patch if the implementation only changes wrapper Python selection, install/update provisioning, manifest checks, and docs.

Run full-smoke only if implementation also changes:

- `qros-research-session` stage flow / gate semantics
- review / display / next-stage orchestration
- route split / CSF routing
- anti-drift snapshots
- canonical session stage naming
- stage-display supported stage contract
- lineage-local stage-program auto-author behavior

If needed, run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS.

## Self-Review

Spec coverage:

- Shared wrapper selector: Tasks 1-4.
- Python 3.12 exact check: Tasks 1-2.
- `.qros/.venv` and uv provisioning: Task 5.
- Manifest lock/runtime metadata: Task 6.
- `qros-update` / bootstrap owns provisioning: Tasks 6-8.
- Ordinary commands do not install: Tasks 3-4 and docs in Task 8.
- Lock drift fail-closed behavior: Tasks 3 and 6.
- Focused tests + smoke: Task 9.

Placeholder scan:

- No task depends on an unspecified file or function.
- Every new public function has a concrete signature.
- Every test task includes concrete assertions and commands.

Type/name consistency:

- Bash functions: `qros_select_python_bin`, `qros_verify_runtime_lock`, `qros_resolve_runtime_root`.
- Python helper: `ensure_repo_local_uv_runtime`, `RuntimeEnvMetadata`, `UvRuntimeError`.
- Manifest fields: `runtime_python_executable`, `runtime_python_version`, `runtime_lock_path`, `runtime_lock_digest`.

