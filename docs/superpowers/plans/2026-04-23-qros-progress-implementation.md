# QROS Progress Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks; this repository forbids unauthorized commits.

**Goal:** Add a read-only `$qros-progress` skill and `./.qros/bin/qros-progress` command that shows the latest QROS research progress.

**Architecture:** Add a small read-only progress runtime that selects an existing lineage, reuses session status summarization without writing transition artifacts, and exposes text/JSON output through a script plus repo-local wrapper. Add a core skill and user docs that position `qros-progress` as status lookup, not workflow progression.

**Tech Stack:** Python standard library, existing `runtime.tools.research_session`, Bash runtime wrappers, pytest.

---

## File Structure

- Create `runtime/tools/progress_runtime.py` for read-only lineage selection and status payload rendering.
- Create `runtime/scripts/run_progress.py` for CLI parsing and text/JSON output.
- Create `runtime/bin/qros-progress` as the repo-local stable wrapper.
- Create `skills/core/qros-progress/SKILL.md` and `skills/core/qros-progress/agents/openai.yaml`.
- Modify `tests/session/test_qros_progress_runtime.py` for focused runtime and CLI behavior tests.
- Modify `tests/bootstrap/test_install_runtime.py` and `tests/bootstrap/test_native_skill_runtime_paths.py` to lock repo-local wrapper installation.
- Modify `tests/skills/test_skill_tree.py` to lock the new skill tree location.
- Modify `tests/docs/test_install_docs.py` or `tests/docs/test_readme_summary_role.py` to lock user-facing docs.
- Modify `README.md` and `docs/guides/qros-research-session-usage.md` to document the new read-only entry.

## Task 1: Add Failing Runtime And CLI Tests

**Files:**
- Create: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Write tests for read-only progress selection and output**

```python
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from runtime.tools.progress_runtime import ProgressError, latest_lineage_id, progress_status_payload


def _touch_lineage(outputs_root: Path, lineage_id: str, filename: str = "marker.txt") -> Path:
    lineage_root = outputs_root / lineage_id
    lineage_root.mkdir(parents=True)
    marker = lineage_root / filename
    marker.write_text(lineage_id + "\n", encoding="utf-8")
    return lineage_root


def test_latest_lineage_id_selects_most_recent_existing_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _touch_lineage(outputs_root, "old_lineage")
    time.sleep(0.01)
    _touch_lineage(outputs_root, "new_lineage")

    assert latest_lineage_id(outputs_root) == "new_lineage"


def test_latest_lineage_id_does_not_create_outputs_root(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"

    try:
        latest_lineage_id(outputs_root)
    except ProgressError as exc:
        assert "No QROS outputs directory found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not outputs_root.exists()


def test_progress_status_payload_requires_existing_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    outputs_root.mkdir()

    try:
        progress_status_payload(outputs_root=outputs_root, lineage_id="missing")
    except ProgressError as exc:
        assert "QROS lineage not found" in str(exc)
    else:
        raise AssertionError("expected ProgressError")

    assert not (outputs_root / "missing").exists()


def test_progress_json_outputs_stable_status_fields_for_explicit_lineage(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = _touch_lineage(outputs_root, "btc_leads_alts")
    (lineage_root / "00_idea_intake").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "runtime/scripts/run_progress.py",
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["selection_mode"] == "explicit"
    assert payload["current_stage"] == "idea_intake_confirmation_pending"
    assert "current_skill" in payload
    assert "gate_status" in payload
    assert "next_action" in payload
    assert payload["artifacts_written"] == []
```

- [ ] **Step 2: Run the tests and verify they fail because the new runtime does not exist**

Run: `python -m pytest tests/session/test_qros_progress_runtime.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.progress_runtime'`.

## Task 2: Implement Read-Only Progress Runtime

**Files:**
- Create: `runtime/tools/progress_runtime.py`

- [ ] **Step 1: Add the runtime module**

```python
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from runtime.tools.research_session import (
    _gate_status_and_next_action,
    _latest_review_failure_status,
    current_research_route,
    current_route_contract,
    detect_session_stage,
    session_transition_summary,
    summarize_session_status,
)


class ProgressError(RuntimeError):
    pass


def _lineage_latest_mtime(lineage_root: Path) -> float:
    latest = lineage_root.stat().st_mtime
    for path in lineage_root.rglob("*"):
        latest = max(latest, path.stat().st_mtime)
    return latest


def latest_lineage_id(outputs_root: Path) -> str:
    if not outputs_root.exists():
        raise ProgressError(f"No QROS outputs directory found: {outputs_root}")
    lineage_dirs = [path for path in outputs_root.iterdir() if path.is_dir()]
    if not lineage_dirs:
        raise ProgressError(f"No QROS lineage directories found under: {outputs_root}")
    latest = max(lineage_dirs, key=lambda path: (_lineage_latest_mtime(path), path.name))
    return latest.name


def _read_only_session_status(lineage_root: Path, *, selection_mode: str):
    current_stage = detect_session_stage(lineage_root)
    gate_status, next_action = _gate_status_and_next_action(lineage_root, current_stage)
    review_verdict, requires_failure_handling, failure_stage, failure_reason_summary = (
        _latest_review_failure_status(lineage_root)
    )
    if requires_failure_handling and failure_stage is not None:
        gate_status = "FAILURE_HANDLING_REQUIRED"
        next_action = f"Enter failure handling for {failure_stage} via qros-stage-failure-handler"

    why_now, open_risks = session_transition_summary(lineage_root, current_stage)
    route_contract = current_route_contract(lineage_root)
    return summarize_session_status(
        lineage_id=lineage_root.name,
        lineage_root=lineage_root,
        lineage_mode=f"progress_{selection_mode}",
        lineage_selection_reason=f"qros-progress selected {lineage_root.name} using {selection_mode} mode",
        current_stage=current_stage,
        current_route=current_research_route(lineage_root),
        artifacts_written=[],
        gate_status=gate_status,
        next_action=next_action,
        why_now=why_now,
        open_risks=open_risks,
        factor_role=route_contract["factor_role"],
        factor_structure=route_contract["factor_structure"],
        portfolio_expression=route_contract["portfolio_expression"],
        neutralization_policy=route_contract["neutralization_policy"],
        review_verdict=review_verdict,
        requires_failure_handling=requires_failure_handling,
        failure_stage=failure_stage,
        failure_reason_summary=failure_reason_summary,
    )


def progress_status_payload(*, outputs_root: Path, lineage_id: str | None = None) -> dict[str, object]:
    selection_mode = "explicit" if lineage_id else "latest"
    selected_lineage_id = lineage_id or latest_lineage_id(outputs_root)
    lineage_root = outputs_root / selected_lineage_id
    if not lineage_root.exists() or not lineage_root.is_dir():
        raise ProgressError(f"QROS lineage not found: {lineage_root}")

    status = _read_only_session_status(lineage_root, selection_mode=selection_mode)
    payload = asdict(status)
    payload["lineage_root"] = str(status.lineage_root)
    payload["selection_mode"] = selection_mode
    return payload
```

- [ ] **Step 2: Run the focused tests**

Run: `python -m pytest tests/session/test_qros_progress_runtime.py -q`

Expected: tests still fail because `runtime/scripts/run_progress.py` is not implemented yet.

## Task 3: Add Progress CLI And Wrapper

**Files:**
- Create: `runtime/scripts/run_progress.py`
- Create: `runtime/bin/qros-progress`

- [ ] **Step 1: Add the Python CLI**

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.tools.progress_runtime import ProgressError, progress_status_payload  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show read-only QROS research progress.")
    parser.add_argument("--outputs-root", type=Path, required=True)
    parser.add_argument("--lineage-id", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _render_text(payload: dict[str, object]) -> str:
    lines = [
        "QROS Progress",
        f"Lineage: {payload['lineage_id']} ({payload['selection_mode']})",
        f"Current stage: {payload['current_stage']}",
        f"Current active skill: {payload['current_skill']}",
        f"Stage status: {payload['stage_status']}",
        f"Gate status: {payload['gate_status']}",
        f"Blocking reason code: {payload['blocking_reason_code']}",
    ]
    if payload.get("blocking_reason"):
        lines.append(f"Blocking reason: {payload['blocking_reason']}")
    lines.extend(
        [
            f"Next action: {payload['next_action']}",
            f"Resume hint: {payload['resume_hint']}",
        ]
    )
    open_risks = payload.get("open_risks")
    if isinstance(open_risks, list) and open_risks:
        lines.append("Open risks:")
        lines.extend(f"- {item}" for item in open_risks)
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    try:
        payload = progress_status_payload(
            outputs_root=args.outputs_root.resolve(),
            lineage_id=args.lineage_id,
        )
    except ProgressError as exc:
        print(f"qros-progress: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_render_text(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Add the repo-local wrapper**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

TARGET_CWD="$PWD"
ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cwd)
      TARGET_CWD="$2"
      shift 2
      ;;
    --outputs-root)
      echo "qros-progress does not accept --outputs-root; it is derived from the project root" >&2
      exit 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

PROJECT_ROOT="$(cd "$TARGET_CWD" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  PYTHON_BIN="python"
fi

RUNTIME_ROOT=""
MANIFEST_PATH="$SCRIPT_DIR/../install-manifest.json"
if [ -f "$MANIFEST_PATH" ]; then
  SOURCE_REPO="$("$PYTHON_BIN" - "$MANIFEST_PATH" <<'PY'
import json, sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(manifest.get("source_repo_path", ""))
PY
)"
  if [ -n "$SOURCE_REPO" ] && [ -d "$SOURCE_REPO/runtime/scripts" ]; then
    RUNTIME_ROOT="$SOURCE_REPO/runtime"
  fi
fi

if [ -z "$RUNTIME_ROOT" ] && [ -d "$SCRIPT_DIR/../../runtime/scripts" ]; then
  RUNTIME_ROOT="$(cd "$SCRIPT_DIR/../../runtime" && pwd)"
fi

if [ -z "$RUNTIME_ROOT" ]; then
  echo "Unable to locate QROS runtime root from $SCRIPT_DIR" >&2
  exit 1
fi

cd "$PROJECT_ROOT"
exec "$PYTHON_BIN" "$RUNTIME_ROOT/scripts/run_progress.py" --outputs-root "$PROJECT_ROOT/outputs" "${ARGS[@]}"
```

- [ ] **Step 3: Run the focused progress tests**

Run: `python -m pytest tests/session/test_qros_progress_runtime.py -q`

Expected: PASS.

## Task 4: Add Skill And Install Contract Tests

**Files:**
- Modify: `tests/skills/test_skill_tree.py`
- Modify: `tests/bootstrap/test_install_runtime.py`
- Modify: `tests/bootstrap/test_native_skill_runtime_paths.py`
- Create: `skills/core/qros-progress/SKILL.md`
- Create: `skills/core/qros-progress/agents/openai.yaml`

- [ ] **Step 1: Add failing skill and install assertions**

Add assertions that `qros-progress` exists, lives under `skills/core`, has an OpenAI agent metadata file, and that repo-local runtime installs `bin/qros-progress`.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python -m pytest tests/skills/test_skill_tree.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: FAIL because the skill bundle and install manifest expectations are not implemented.

- [ ] **Step 3: Add the skill bundle**

`skills/core/qros-progress/SKILL.md`:

```markdown
---
name: qros-progress
description: Use when the user asks for latest QROS research progress, current lineage status, current stage, blocking gate, next action, or explicitly invokes qros-progress.
---

# QROS Progress

## Purpose

这是只读进度查询 skill。它告诉研究员当前 research repo 中最新或指定 lineage 推进到哪里、当前应使用哪个 skill、被哪个 gate 卡住、下一步应该做什么。

## Required Runtime

优先使用 repo-local wrapper：

```bash
./.qros/bin/qros-progress
./.qros/bin/qros-progress --lineage-id "<lineage_id>"
```

需要机读输出时使用：

```bash
./.qros/bin/qros-progress --json
```

## Hard Boundaries

- 不写 artifact。
- 不创建 lineage。
- 不 scaffold `00_idea_intake/`。
- 不确认任何 transition。
- 不把目录存在、placeholder 文件或 contract-only 文档说成 stage 已完成。
- 不替代 `qros-research-session`、stage author skill、review skill 或 failure handling skill。

## Reporting Rules

汇报时至少覆盖：

- `lineage_id`
- `current_stage`
- `current_skill`
- `stage_status`
- `gate_status`
- `blocking_reason`
- `next_action`
- `open_risks`

如果无参数查询，必须说明这是最新修改 lineage 的状态，而不是全 repo 聚合状态。
```

`skills/core/qros-progress/agents/openai.yaml`:

```yaml
name: qros-progress
description: Read-only QROS research progress lookup.
```

- [ ] **Step 4: Update install tests and run them**

Run: `python -m pytest tests/skills/test_skill_tree.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: PASS.

## Task 5: Update User Docs And Doc Tests

**Files:**
- Modify: `README.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `tests/docs/test_readme_summary_role.py` or `tests/docs/test_install_docs.py`

- [ ] **Step 1: Add failing doc assertions**

Assert the README and research-session usage guide mention `$qros-progress` or `./.qros/bin/qros-progress` and describe it as read-only progress lookup.

- [ ] **Step 2: Run doc tests and verify failure**

Run: `python -m pytest tests/docs/test_readme_summary_role.py tests/docs/test_install_docs.py -q`

Expected: FAIL because docs do not mention the new command yet.

- [ ] **Step 3: Update docs**

Add a short section that keeps `qros-research-session` as the formal workflow entry and introduces `qros-progress` as read-only status lookup:

```text
查看最新研究进度：

$qros-progress

这只读取当前 repo 的 outputs/，默认选择最近修改的 lineage，不写 artifact、不推进 stage。
```

- [ ] **Step 4: Run doc tests**

Run: `python -m pytest tests/docs/test_readme_summary_role.py tests/docs/test_install_docs.py -q`

Expected: PASS.

## Task 6: Verification

**Files:**
- No new files beyond prior tasks.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/session/test_qros_progress_runtime.py tests/skills/test_skill_tree.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py tests/docs/test_readme_summary_role.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 2: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 3: Confirm full-smoke scope**

No full-smoke is required because this change adds a read-only status entry and does not alter stage flow, gate semantics, CSF routing, review orchestration, anti-drift naming, display-stage contract, or lineage-local stage-program author seams.

## Self-Review

- Spec coverage: The plan covers runtime selection, read-only behavior, skill entry, wrapper installation, user docs, and focused + smoke verification.
- Placeholder scan: The plan contains no unfinished implementation placeholders.
- Type consistency: Runtime functions use `latest_lineage_id(outputs_root: Path)` and `progress_status_payload(outputs_root: Path, lineage_id: str | None)` consistently across tests and CLI.
