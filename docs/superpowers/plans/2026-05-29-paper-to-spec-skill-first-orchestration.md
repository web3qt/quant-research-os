# Paper-to-Spec Skill-First Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `paper-to-spec` from a materializer-only fast lane into a skill-first orchestration flow that can ingest `URL / local PDF / pasted summary`, generate an implementable spec, and optionally scaffold a runnable baseline with minimal verification in the active research repo.

**Architecture:** Keep source reading and ambiguity judgment in `$qros-paper-to-spec`, and keep deterministic validation/materialization in runtime helpers. Add a small deterministic baseline-scaffold helper that consumes `strategy_spec.yaml`, writes repo-local baseline files in either repo-native or fallback layout, and runs minimal verification without touching QROS governance flow.

**Tech Stack:** Python 3.12, repo-local `./.qros/bin` wrappers, QROS skill bundles, YAML, `pytest`

---

## Planned File Map

- `skills/core/qros-paper-to-spec/SKILL.md`
  - Upgrade from “materializer-aware skill” to the real ordinary user entrypoint for source ingestion, ambiguity handling, target-repo routing, and optional baseline implementation.
- `docs/guides/qros-paper-to-spec-usage.md`
  - User-facing usage guide for `URL / local PDF / pasted summary`, stop-at-spec default behavior, and optional auto-implement behavior.
- `docs/README.codex.md`
  - Codex entry table and workflow summary for the new orchestration surface.
- `runtime/tools/paper_to_spec.py`
  - Continue as deterministic materializer; add bridge-level helper(s) needed to validate orchestration metadata and block duplicate derived slugs.
- `runtime/tools/paper_to_spec_baseline.py`
  - New deterministic helper for baseline scaffold generation and minimal verification.
- `runtime/scripts/run_paper_to_spec.py`
  - Keep as low-level materializer/debug surface; expand only if needed for deterministic orchestration metadata handoff.
- `runtime/scripts/run_paper_to_spec_baseline.py`
  - New low-level debug surface for baseline scaffold generation from an existing `strategy_spec.yaml`.
- `runtime/bin/qros-paper-to-spec-baseline`
  - Repo-local wrapper for deterministic baseline generation/debug.
- `tests/paper_to_spec/test_paper_to_spec_runtime.py`
  - Extend materializer/bridge coverage.
- `tests/paper_to_spec/test_paper_to_spec_baseline.py`
  - New coverage for repo-native/fallback scaffold decisions and minimal verification.
- `tests/skills/test_paper_to_spec_assets.py`
  - Lock skill contract wording for ingestion inputs, ambiguity rules, repo boundary, and auto-implement discipline.
- `tests/docs/test_paper_to_spec_docs.py`
  - Lock docs/runtime/skill consistency on actual wrapper flags and actual artifact names.
- `tests/bootstrap/test_project_bootstrap.py`
  - Add existence assertions for any new deterministic baseline helper surface.
- `tests/docs/test_install_docs.py`
  - Add assertions for Codex README references to the new orchestration and baseline debug surface.

### Task 1: Upgrade `$qros-paper-to-spec` into the real orchestration skill

**Files:**
- Modify: `skills/core/qros-paper-to-spec/SKILL.md`
- Modify: `docs/guides/qros-paper-to-spec-usage.md`
- Modify: `docs/README.codex.md`
- Test: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`

- [ ] **Step 1: Write the failing skill/docs tests**

```python
from pathlib import Path

from tests.helpers.skill_test_utils import skill_path


def test_paper_to_spec_skill_documents_source_ingestion_and_optional_auto_implement() -> None:
    content = skill_path("qros-paper-to-spec").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec <url>" in content
    assert "URL / 本地 PDF 路径 / 粘贴文本摘要" in content
    assert "默认先产 spec，不先写代码" in content
    assert "auto_implement" in content
    assert "只有阻断自动实现的歧义才追问" in content
    assert "active research repo" in content
    assert "./.qros/bin/qros-paper-to-spec --spec-file" in content


def test_paper_to_spec_docs_lock_actual_runtime_surface_and_repo_boundary() -> None:
    guide = Path("docs/guides/qros-paper-to-spec-usage.md").read_text(encoding="utf-8")
    readme = Path("docs/README.codex.md").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec https://example.com/paper.pdf" in guide
    assert "URL / 本地 PDF 路径 / 粘贴文本摘要" in guide
    assert "strategy_spec.yaml" in guide
    assert "strategy_spec.md" in guide
    assert "source_manifest.yaml" in guide
    assert "./.qros/bin/qros-paper-to-spec --spec-file" in guide
    assert "active research repo" in guide

    assert "$qros-paper-to-spec" in readme
    assert "./.qros/bin/qros-paper-to-spec --spec-file" in readme
    assert "docs/guides/qros-paper-to-spec-usage.md" in readme
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: FAIL because the current skill/docs do not yet describe the full orchestration surface or the final wording locked by this plan.

- [ ] **Step 3: Rewrite the skill and docs for the new orchestration surface**

Update `skills/core/qros-paper-to-spec/SKILL.md` so the ordinary entrypoint becomes source ingestion rather than just “spec materializer awareness”:

```markdown
## Purpose

这是独立于 `qros-research-session` 的 skill-first fast lane。

普通用户入口：

- `$qros-paper-to-spec <url>`
- `$qros-paper-to-spec /abs/path/to/paper.pdf`
- `$qros-paper-to-spec "<paper summary>"`

它负责：

- 读取 `URL / 本地 PDF 路径 / 粘贴文本摘要`
- 提炼 `paper_stated` 与 `agent_inferred`
- 在必要时追问 1-3 个阻断自动实现的关键歧义
- 生成 `strategy_spec.yaml` / `strategy_spec.md` / `source_manifest.yaml`
- 在用户显式要求 `auto_implement` 且无阻断歧义时，继续生成 baseline 实现

低层 deterministic debug/materializer 入口仍然是：

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```

## Hard Boundaries

- 不进入 `mandate_admission`。
- 不进入 freeze / review / failure handling 主流程。
- `paper_stated` 只能写 source 可归因的内容。
- `agent_inferred` 不能冒充论文原文。
- 默认先产 spec，不先写代码。
- 只有阻断自动实现的歧义才追问。
- 所有 `outputs/paper_to_spec/<paper_slug>/...` 都属于 active research repo 的本地输出，不属于 QROS 框架仓。
```

Update `docs/guides/qros-paper-to-spec-usage.md` so the guide matches the new user path and the actual lower-level wrapper:

```markdown
## 在 Codex 里怎么用

```text
$qros-paper-to-spec https://example.com/paper.pdf
$qros-paper-to-spec /abs/path/to/paper.pdf
$qros-paper-to-spec "This paper ranks assets by ..."
$qros-paper-to-spec https://example.com/paper.pdf --auto-implement
```

默认行为：

1. 读取 source
2. 生成 `strategy_spec.yaml`
3. 生成 `strategy_spec.md`
4. 生成 `source_manifest.yaml`
5. 停在 spec

只有当用户显式要求 `--auto-implement` 且没有阻断型歧义时，才继续 baseline 实现。

## Runtime 调试入口

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```
```

Update `docs/README.codex.md` to reflect the ordinary entrypoint vs lower-level debug surface split:

```markdown
| 把论文 / PDF / URL 压成实现 spec | `$qros-paper-to-spec` |
```

and:

```bash
./.qros/bin/qros-paper-to-spec --spec-file /tmp/spec.yaml --source "https://example.com/paper.pdf" --source-kind pdf_url --title "Paper Title" --slug paper_title
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py -q
```

Expected: PASS with the skill/docs tests green and the fast-lane orchestration surface aligned.

- [ ] **Step 5: Commit**

```bash
git add skills/core/qros-paper-to-spec/SKILL.md docs/guides/qros-paper-to-spec-usage.md docs/README.codex.md tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py
git commit -m "feat: upgrade paper-to-spec skill orchestration"
```

### Task 2: Add the draft-to-materializer bridge and block duplicate derived slugs

**Files:**
- Modify: `runtime/tools/paper_to_spec.py`
- Test: `tests/paper_to_spec/test_paper_to_spec_runtime.py`

- [ ] **Step 1: Write the failing runtime bridge tests**

```python
from pathlib import Path

import pytest

from runtime.tools.paper_to_spec import PaperToSpecError, materialize_strategy_spec_bundle


def test_materialize_strategy_spec_bundle_rejects_duplicate_derived_slug(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    payload = _valid_spec_payload(title="Same Title")

    materialize_strategy_spec_bundle(
        outputs_root=outputs_root,
        source_locator="https://example.com/paper-a.pdf",
        source_kind="pdf_url",
        source_title="Same Title",
        spec_payload=payload,
    )

    with pytest.raises(PaperToSpecError, match="already exists"):
        materialize_strategy_spec_bundle(
            outputs_root=outputs_root,
            source_locator="https://example.com/paper-b.pdf",
            source_kind="pdf_url",
            source_title="Same Title",
            spec_payload=payload,
        )


def test_validate_strategy_spec_accepts_orchestration_ready_payload_shape() -> None:
    payload = _valid_spec_payload(title="Momentum Paper")
    payload["agent_inferred"]["ambiguities"] = [
        {
            "field": "portfolio_construction.method",
            "severity": "blocking_for_auto_implement",
            "question": "Should the baseline be long-short or top-decile only?",
        }
    ]

    validated = validate_strategy_spec(payload)
    assert validated["agent_inferred"]["ambiguities"][0]["severity"] == "blocking_for_auto_implement"
```

- [ ] **Step 2: Run the runtime tests to verify they fail**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_runtime.py -q
```

Expected: FAIL because duplicate derived slugs are still overwritten or reused silently.

- [ ] **Step 3: Add the deterministic bridge behavior**

Update `runtime/tools/paper_to_spec.py` so derived slugs fail closed too, while keeping runtime source-agnostic:

```python
def materialize_strategy_spec_bundle(
    *,
    outputs_root: Path,
    source_locator: str,
    source_kind: str,
    source_title: str,
    spec_payload: dict[str, Any],
    requested_slug: str | None = None,
) -> dict[str, str]:
    contract = _load_contract()
    _validate_source_kind(contract, source_kind)
    validated_payload = validate_strategy_spec(spec_payload)

    strategy_identity = _require_map(validated_payload, "strategy_identity")
    derived_name = requested_slug or source_title or _required_string(strategy_identity, "title")
    slug = _resolve_bundle_slug(derived_name, explicit=requested_slug is not None)
    bundle_root = outputs_root / "paper_to_spec" / slug

    if bundle_root.exists():
        slug_kind = "explicit" if requested_slug is not None else "derived"
        raise PaperToSpecError(f"paper-to-spec {slug_kind} slug target already exists: {bundle_root}")

    bundle_root.mkdir(parents=True, exist_ok=False)
    source_manifest = {
        "schema_id": "qros-paper-to-spec-source-manifest-v1",
        "source": {
            "kind": source_kind,
            "locator": source_locator,
            "title": source_title,
            "capture_time": _utc_iso_timestamp(),
        },
    }
    ...
```

Keep the bridge deterministic:
- runtime still does not read the paper
- runtime only consumes the already-built draft payload
- ambiguity objects can be passed through as machine-readable content without runtime judging their truth

- [ ] **Step 4: Run the runtime tests to verify they pass**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_runtime.py -q
```

Expected: PASS with duplicate derived slug rejection and orchestration-ready ambiguity payload shape covered.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/paper_to_spec.py tests/paper_to_spec/test_paper_to_spec_runtime.py
git commit -m "feat: harden paper-to-spec draft bridge"
```

### Task 3: Add deterministic baseline scaffold generation and minimal verification

**Files:**
- Create: `runtime/tools/paper_to_spec_baseline.py`
- Create: `runtime/scripts/run_paper_to_spec_baseline.py`
- Create: `runtime/bin/qros-paper-to-spec-baseline`
- Create: `tests/paper_to_spec/test_paper_to_spec_baseline.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Write the failing baseline scaffold tests**

```python
from pathlib import Path

from runtime.tools.paper_to_spec_baseline import scaffold_baseline_from_spec


def test_scaffold_baseline_from_spec_fallback_layout_writes_runnable_bundle(tmp_path: Path) -> None:
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="cross_sectional_factor"), encoding="utf-8")

    result = scaffold_baseline_from_spec(
        target_repo=target_repo,
        spec_path=spec_path,
        prefer_repo_native=True,
    )

    bundle_root = target_repo / "paper_specs" / "value_paper"
    assert result["layout_mode"] == "fallback"
    assert (bundle_root / "strategy_config.yaml").exists()
    assert (bundle_root / "build_dataset.py").exists()
    assert (bundle_root / "build_signal.py").exists()
    assert (bundle_root / "run_backtest.py").exists()
    assert (bundle_root / "tests" / "test_smoke.py").exists()


def test_scaffold_baseline_from_spec_rejects_missing_target_repo(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing_repo"
    spec_path = tmp_path / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="time_series_signal"), encoding="utf-8")

    with pytest.raises(BaselineScaffoldError, match="target repo"):
        scaffold_baseline_from_spec(
            target_repo=missing_repo,
            spec_path=spec_path,
            prefer_repo_native=True,
        )
```

- [ ] **Step 2: Run the baseline tests to verify they fail**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_baseline.py -q
```

Expected: FAIL because the baseline scaffold helper does not exist yet.

- [ ] **Step 3: Implement fallback scaffold generation and minimal verification**

Create `runtime/tools/paper_to_spec_baseline.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class BaselineScaffoldError(RuntimeError):
    pass


@dataclass(frozen=True)
class BaselineScaffoldResult:
    layout_mode: str
    bundle_root: Path
    run_entrypoint: Path
    smoke_test_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "layout_mode": self.layout_mode,
            "bundle_root": str(self.bundle_root),
            "run_entrypoint": str(self.run_entrypoint),
            "smoke_test_path": str(self.smoke_test_path),
        }


def scaffold_baseline_from_spec(*, target_repo: Path, spec_path: Path, prefer_repo_native: bool = True) -> dict[str, str]:
    if not target_repo.exists() or not target_repo.is_dir():
        raise BaselineScaffoldError(f"target repo not found: {target_repo}")
    spec_payload = _load_yaml(spec_path)
    slug = spec_path.parent.name

    repo_native_root = _discover_repo_native_root(target_repo) if prefer_repo_native else None
    if repo_native_root is not None:
        return _scaffold_repo_native(repo_native_root=repo_native_root, slug=slug, spec_payload=spec_payload).as_dict()
    return _scaffold_fallback(target_repo=target_repo, slug=slug, spec_payload=spec_payload).as_dict()


def _discover_repo_native_root(target_repo: Path) -> Path | None:
    for candidate in ("research", "strategies", "src"):
        path = target_repo / candidate
        if path.exists() and path.is_dir():
            return path
    return None


def _scaffold_fallback(*, target_repo: Path, slug: str, spec_payload: dict[str, Any]) -> BaselineScaffoldResult:
    bundle_root = target_repo / "paper_specs" / slug
    bundle_root.mkdir(parents=True, exist_ok=False)
    tests_dir = bundle_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=False)

    _write_yaml(bundle_root / "strategy_config.yaml", {
        "spec_path": str(target_repo / "outputs" / "paper_to_spec" / slug / "strategy_spec.yaml"),
        "strategy_type": spec_payload["strategy_identity"]["strategy_type"],
        "validation_targets": spec_payload["implementation_handoff"]["validation_targets"],
    })
    (bundle_root / "README.md").write_text("# Paper baseline\n", encoding="utf-8")
    (bundle_root / "build_dataset.py").write_text(_dataset_stub(), encoding="utf-8")
    (bundle_root / "build_signal.py").write_text(_signal_stub(), encoding="utf-8")
    (bundle_root / "run_backtest.py").write_text(_backtest_stub(), encoding="utf-8")
    (tests_dir / "test_smoke.py").write_text(_smoke_test_stub(), encoding="utf-8")

    return BaselineScaffoldResult(
        layout_mode="fallback",
        bundle_root=bundle_root,
        run_entrypoint=bundle_root / "run_backtest.py",
        smoke_test_path=tests_dir / "test_smoke.py",
    )
```

Create `runtime/scripts/run_paper_to_spec_baseline.py`:

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

from runtime.tools.paper_to_spec_baseline import BaselineScaffoldError, scaffold_baseline_from_spec  # noqa: E402


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise BaselineScaffoldError(message)


def _parse_args() -> argparse.Namespace:
    parser = _Parser(description="Scaffold a paper-to-spec baseline from an existing strategy spec.")
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--spec-path", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        args = _parse_args()
        result = scaffold_baseline_from_spec(
            target_repo=args.target_repo.resolve(),
            spec_path=args.spec_path.resolve(),
            prefer_repo_native=True,
        )
    except BaselineScaffoldError as exc:
        print(f"qros-paper-to-spec-baseline: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n".join([
            "QROS Paper-to-Spec Baseline",
            f"Layout: {result['layout_mode']}",
            f"Bundle root: {result['bundle_root']}",
            f"Run entrypoint: {result['run_entrypoint']}",
            f"Smoke test: {result['smoke_test_path']}",
        ]))
    return 0
```

Create `runtime/bin/qros-paper-to-spec-baseline`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_CWD="$PWD"
ARGS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --cwd)
      if [ "$#" -lt 2 ]; then
        echo "qros-paper-to-spec-baseline: --cwd requires a path" >&2
        exit 2
      fi
      TARGET_CWD="$2"
      shift 2
      ;;
    --target-repo)
      echo "qros-paper-to-spec-baseline does not accept --target-repo; it is derived from --cwd or current directory" >&2
      exit 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [ ! -d "$TARGET_CWD" ]; then
  echo "qros-paper-to-spec-baseline: invalid --cwd path: $TARGET_CWD" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$TARGET_CWD" && pwd)"

source "$SCRIPT_DIR/qros-wrapper-lib"
PYTHON_BIN="$(qros_select_python_bin "$SCRIPT_DIR")"
qros_verify_runtime_lock "$SCRIPT_DIR" "$PYTHON_BIN"
RUNTIME_ROOT="$(qros_resolve_runtime_root "$SCRIPT_DIR" "$PYTHON_BIN" strict)"

cd "$PROJECT_ROOT"
exec "$PYTHON_BIN" "$RUNTIME_ROOT/scripts/run_paper_to_spec_baseline.py" --target-repo "$PROJECT_ROOT" "${ARGS[@]}"
```

Update bootstrap/doc tests for the new deterministic baseline helper surface:

```python
assert Path("runtime/bin/qros-paper-to-spec-baseline").exists()
assert Path("runtime/scripts/run_paper_to_spec_baseline.py").exists()
assert Path("runtime/tools/paper_to_spec_baseline.py").exists()
```

and:

```python
assert "./.qros/bin/qros-paper-to-spec-baseline" in content
```

- [ ] **Step 4: Run the baseline tests to verify they pass**

Run:

```bash
python -m pytest tests/paper_to_spec/test_paper_to_spec_baseline.py -q
```

Expected: PASS with fallback scaffold generation and target-repo validation covered.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/paper_to_spec_baseline.py runtime/scripts/run_paper_to_spec_baseline.py runtime/bin/qros-paper-to-spec-baseline tests/paper_to_spec/test_paper_to_spec_baseline.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
git commit -m "feat: add paper-to-spec baseline scaffolder"
```

### Task 4: Lock cross-layer consistency and run focused verification + smoke

**Files:**
- Modify: `tests/skills/test_paper_to_spec_assets.py`
- Modify: `tests/docs/test_paper_to_spec_docs.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `tests/docs/test_install_docs.py`
- Test: `tests/paper_to_spec/test_paper_to_spec_runtime.py`
- Test: `tests/paper_to_spec/test_run_paper_to_spec_script.py`
- Test: `tests/paper_to_spec/test_paper_to_spec_baseline.py`
- Test: `tests/skills/test_paper_to_spec_assets.py`
- Test: `tests/docs/test_paper_to_spec_docs.py`
- Test: `tests/bootstrap/test_project_bootstrap.py`
- Test: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Add cross-layer regression assertions**

Strengthen `tests/skills/test_paper_to_spec_assets.py`:

```python
assert "strategy_spec.yaml" in content
assert "strategy_spec.md" in content
assert "source_manifest.yaml" in content
assert "./.qros/bin/qros-paper-to-spec --spec-file" in content
assert "默认先产 spec，不先写代码" in content
assert "只有阻断自动实现的歧义才追问" in content
assert "active research repo" in content
```

Strengthen `tests/docs/test_paper_to_spec_docs.py`:

```python
assert "strategy_spec.yaml" in guide_text
assert "strategy_spec.md" in guide_text
assert "source_manifest.yaml" in guide_text
assert "./.qros/bin/qros-paper-to-spec --spec-file" in guide_text
assert "./.qros/bin/qros-paper-to-spec-baseline" in guide_text
assert "active research repo" in guide_text
assert "--auto-implement" in guide_text
```

Add the baseline helper reference to `tests/docs/test_install_docs.py`:

```python
assert "./.qros/bin/qros-paper-to-spec-baseline" in content
```

- [ ] **Step 2: Run the focused verification suite**

Run:

```bash
python -m pytest \
  tests/paper_to_spec/test_paper_to_spec_runtime.py \
  tests/paper_to_spec/test_run_paper_to_spec_script.py \
  tests/paper_to_spec/test_paper_to_spec_baseline.py \
  tests/skills/test_paper_to_spec_assets.py \
  tests/docs/test_paper_to_spec_docs.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py -q
```

Expected: PASS with all paper-to-spec runtime, baseline, docs, skill, bootstrap, and install-doc checks green.

- [ ] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS. `full-smoke` should remain unnecessary because this orchestration does not modify `qros-research-session` stage flow/gate semantics, review/display/next-stage orchestration, route split/CSF routing, anti-drift stage naming, stage-display contracts, or lineage-local stage-program auto-author seams.

- [ ] **Step 4: Manual sanity-check the deterministic baseline helper**

Run:

```bash
python runtime/scripts/run_paper_to_spec_baseline.py \
  --target-repo /tmp/qros-paper-to-spec-target \
  --spec-path /tmp/qros-paper-to-spec-target/outputs/paper_to_spec/value_paper/strategy_spec.yaml \
  --json
```

Expected: JSON output with `layout_mode`, `bundle_root`, `run_entrypoint`, and `smoke_test_path`, and files under `/tmp/qros-paper-to-spec-target/paper_specs/value_paper/`.

- [ ] **Step 5: Commit**

```bash
git add tests/skills/test_paper_to_spec_assets.py tests/docs/test_paper_to_spec_docs.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
git commit -m "test: lock paper-to-spec orchestration regressions"
```

## Self-Review Checklist

- Spec coverage:
  - Skill-first single-entry orchestration: Task 1.
  - `URL / local PDF / pasted summary` input contract: Task 1.
  - Blocking-ambiguity-only follow-up questions: Task 1 + Task 4 string-contract tests.
  - Draft-to-materializer bridge and fail-closed derived slugs: Task 2.
  - Target-repo-aware baseline implementation and minimal verification: Task 3.
  - Cross-layer consistency and repo boundary: Task 4.
- Placeholder scan: no `TODO` / `TBD` / “similar to Task N” placeholders remain.
- Type consistency:
  - Artifacts stay `strategy_spec.yaml`, `strategy_spec.md`, `source_manifest.yaml`.
  - Lower-level materializer wrapper stays `qros-paper-to-spec` with `--spec-file --source --source-kind --title [--slug]`.
  - Baseline helper wrapper stays `qros-paper-to-spec-baseline` with `--spec-path`.
