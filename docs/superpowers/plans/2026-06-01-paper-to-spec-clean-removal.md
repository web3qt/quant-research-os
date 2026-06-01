# Paper-to-Spec Clean Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the old `paper -> strategy_spec -> baseline` capability cleanly so `qros-paper-to-spec` can later be rebuilt as data-spec-first.

**Architecture:** This is a deletion and documentation-alignment change. Remove the old repo-local wrappers, runtime helpers, strategy spec contract, and runtime tests; keep only the Codex skill name and docs that state the old capability has been removed and v2 will be data-spec-first.

**Tech Stack:** Python `pytest`, Bash wrapper files under `runtime/bin`, YAML contracts under `contracts/`, Markdown docs and Codex skill docs.

---

## File Structure

Delete these old capability files:

- `contracts/paper_to_spec/strategy_spec_contract.yaml`: old final strategy spec schema.
- `runtime/tools/paper_to_spec.py`: old strategy spec validator/materializer.
- `runtime/scripts/run_paper_to_spec.py`: old CLI bridge for materializing `strategy_spec.yaml`.
- `runtime/bin/qros-paper-to-spec`: old repo-local wrapper.
- `runtime/tools/paper_to_spec_baseline.py`: old baseline scaffold helper.
- `runtime/scripts/run_paper_to_spec_baseline.py`: old baseline CLI bridge.
- `runtime/bin/qros-paper-to-spec-baseline`: old baseline repo-local wrapper.
- `tests/paper_to_spec/`: old runtime and wrapper tests for the removed capability.

Modify these active docs and tests:

- `skills/core/qros-paper-to-spec/SKILL.md`: keep the skill name; replace old strategy spec protocol with removed/v2 data-spec-first direction.
- `docs/guides/qros-paper-to-spec-usage.md`: replace old usage guide with current removed/v2 status.
- `docs/README.codex.md`: remove old wrapper/baseline examples and describe v2 reset.
- `README.md`: remove old paper-to-spec usage and wrapper/baseline examples.
- `tests/bootstrap/test_project_bootstrap.py`: stop requiring deleted files; assert they are absent.
- `tests/docs/test_install_docs.py`: stop requiring removed wrappers; assert old baseline/wrapper examples are absent from active user docs.
- `tests/docs/test_paper_to_spec_docs.py`: rewrite expectations around removal and v2 data-spec-first direction.
- `tests/skills/test_paper_to_spec_assets.py`: rewrite skill expectations around removal and v2 data-spec-first direction.

Historical design/plan docs under `docs/superpowers/` may continue to mention old commands as history. Active user docs and active skills must not.

---

### Task 1: Lock Bootstrap Expectations For Removed Runtime

**Files:**
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Delete later in this task: `contracts/paper_to_spec/strategy_spec_contract.yaml`
- Delete later in this task: `runtime/tools/paper_to_spec.py`
- Delete later in this task: `runtime/scripts/run_paper_to_spec.py`
- Delete later in this task: `runtime/bin/qros-paper-to-spec`
- Delete later in this task: `runtime/tools/paper_to_spec_baseline.py`
- Delete later in this task: `runtime/scripts/run_paper_to_spec_baseline.py`
- Delete later in this task: `runtime/bin/qros-paper-to-spec-baseline`

- [ ] **Step 1: Update bootstrap test to assert removed files are absent**

In `tests/bootstrap/test_project_bootstrap.py`, remove these positive assertions:

```python
    assert Path("runtime/bin/qros-paper-to-spec").exists()
    assert Path("runtime/bin/qros-paper-to-spec-baseline").exists()
    assert Path("runtime/tools/paper_to_spec.py").exists()
    assert Path("runtime/tools/paper_to_spec_baseline.py").exists()
    assert Path("runtime/scripts/run_paper_to_spec.py").exists()
    assert Path("runtime/scripts/run_paper_to_spec_baseline.py").exists()
    assert Path("contracts/paper_to_spec/strategy_spec_contract.yaml").exists()
```

Add these assertions near the other removed-file assertions:

```python
    assert not Path("runtime/bin/qros-paper-to-spec").exists()
    assert not Path("runtime/bin/qros-paper-to-spec-baseline").exists()
    assert not Path("runtime/tools/paper_to_spec.py").exists()
    assert not Path("runtime/tools/paper_to_spec_baseline.py").exists()
    assert not Path("runtime/scripts/run_paper_to_spec.py").exists()
    assert not Path("runtime/scripts/run_paper_to_spec_baseline.py").exists()
    assert not Path("contracts/paper_to_spec/strategy_spec_contract.yaml").exists()
```

- [ ] **Step 2: Run bootstrap test and verify it fails before deletion**

Run:

```bash
python -m pytest tests/bootstrap/test_project_bootstrap.py -q
```

Expected: FAIL because the old paper-to-spec files still exist.

- [ ] **Step 3: Delete the old runtime and contract files**

Run:

```bash
rm -f contracts/paper_to_spec/strategy_spec_contract.yaml \
  runtime/tools/paper_to_spec.py \
  runtime/scripts/run_paper_to_spec.py \
  runtime/bin/qros-paper-to-spec \
  runtime/tools/paper_to_spec_baseline.py \
  runtime/scripts/run_paper_to_spec_baseline.py \
  runtime/bin/qros-paper-to-spec-baseline
```

- [ ] **Step 4: Run bootstrap test and verify it passes**

Run:

```bash
python -m pytest tests/bootstrap/test_project_bootstrap.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit runtime removal**

Run:

```bash
git add tests/bootstrap/test_project_bootstrap.py \
  contracts/paper_to_spec/strategy_spec_contract.yaml \
  runtime/tools/paper_to_spec.py \
  runtime/scripts/run_paper_to_spec.py \
  runtime/bin/qros-paper-to-spec \
  runtime/tools/paper_to_spec_baseline.py \
  runtime/scripts/run_paper_to_spec_baseline.py \
  runtime/bin/qros-paper-to-spec-baseline
git commit -m "remove old paper-to-spec runtime"
```

---

### Task 2: Remove Old Runtime Tests

**Files:**
- Delete: `tests/paper_to_spec/test_paper_to_spec_runtime.py`
- Delete: `tests/paper_to_spec/test_run_paper_to_spec_script.py`
- Delete: `tests/paper_to_spec/test_paper_to_spec_baseline.py`
- Delete: `tests/paper_to_spec/` if empty

- [ ] **Step 1: Delete old paper-to-spec runtime tests**

Run:

```bash
rm -f tests/paper_to_spec/test_paper_to_spec_runtime.py \
  tests/paper_to_spec/test_run_paper_to_spec_script.py \
  tests/paper_to_spec/test_paper_to_spec_baseline.py
rmdir tests/paper_to_spec
```

Expected: `rmdir` succeeds if the directory is empty.

- [ ] **Step 2: Verify pytest no longer discovers deleted tests**

Run:

```bash
python -m pytest tests/bootstrap/test_project_bootstrap.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit test removal**

Run:

```bash
git add tests/paper_to_spec
git commit -m "test: remove old paper-to-spec runtime tests"
```

If `git add tests/paper_to_spec` fails because the directory no longer exists, use:

```bash
git add -u tests/paper_to_spec
git commit -m "test: remove old paper-to-spec runtime tests"
```

---

### Task 3: Rewrite Skill Contract Around Removed Capability

**Files:**
- Modify: `skills/core/qros-paper-to-spec/SKILL.md`
- Modify: `tests/skills/test_paper_to_spec_assets.py`

- [ ] **Step 1: Rewrite skill test expectations**

Replace `test_paper_to_spec_skill_contains_required_contract_strings` in `tests/skills/test_paper_to_spec_assets.py` with:

```python
def test_paper_to_spec_skill_documents_removed_legacy_path_and_v2_direction() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "PDF 读取覆盖",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不直接生成回测代码",
        "独立于 `qros-research-session`",
        "heavy governance flow",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        "./.qros/bin/qros-paper-to-spec",
        "./.qros/bin/qros-paper-to-spec-baseline",
        "--spec-file",
        "--auto-implement",
        "auto_implement",
        "source -> spec -> materialize -> stop",
        "默认只产出 `strategy_spec.yaml`",
        "report where the baseline files were written",
    ]

    for needle in forbidden_strings:
        assert needle not in content
```

- [ ] **Step 2: Run skill test and verify it fails**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py -q
```

Expected: FAIL because `SKILL.md` still documents old strategy spec and baseline behavior.

- [ ] **Step 3: Replace the skill body**

Replace the contents of `skills/core/qros-paper-to-spec/SKILL.md` with:

```markdown
---
name: qros-paper-to-spec
description: Prepare the next paper-to-spec v2 flow; the old strategy_spec materializer has been removed and the rebuilt path will be data-spec-first.
---

# qros-paper-to-spec

## Current status

`qros-paper-to-spec` 保留为 Codex skill 名称，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要把这个入口解释成“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”。旧的 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

## Direction

下一版 `qros-paper-to-spec` 会采用 data-spec-first：

1. 读取论文来源。
2. 记录 PDF 读取覆盖和低置信区域。
3. 面向 crypto perpetual 场景生成 `paper_data_spec.yaml`。
4. 如果核心 data 口径不清楚，先停下来问研究员。
5. 等 data spec 稳定后，再设计 signal / train-freeze / test-evidence / backtest spec。

## Boundaries

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不进入 `qros-research-session`。
- 不进入 mandate / freeze / review / failure handling 的 heavy governance flow。
- 不把 agent 对 crypto perpetual 的迁移假设伪装成论文原文。

## Next implementation target

后续重建时，第一产物应是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该产物应包含 PDF 读取覆盖摘要、crypto perpetual 数据需求、严格阻断问题和 data implementation handoff。
```

- [ ] **Step 4: Run skill test and verify it passes**

Run:

```bash
python -m pytest tests/skills/test_paper_to_spec_assets.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit skill cleanup**

Run:

```bash
git add skills/core/qros-paper-to-spec/SKILL.md tests/skills/test_paper_to_spec_assets.py
git commit -m "docs: reset paper-to-spec skill direction"
```

---

### Task 4: Rewrite Paper-to-Spec User Docs

**Files:**
- Modify: `docs/guides/qros-paper-to-spec-usage.md`
- Modify: `docs/README.codex.md`
- Modify: `README.md`
- Modify: `tests/docs/test_paper_to_spec_docs.py`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Rewrite paper-to-spec docs test**

Replace `tests/docs/test_paper_to_spec_docs.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/guides/qros-paper-to-spec-usage.md"
README_PATH = ROOT / "docs/README.codex.md"


def test_paper_to_spec_usage_guide_exists() -> None:
    assert GUIDE_PATH.exists(), f"missing guide: {GUIDE_PATH}"


def test_paper_to_spec_usage_guide_documents_removed_legacy_path() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "PDF 读取覆盖",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不直接生成回测代码",
        "不是 `qros-research-session` 的阶段入口",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        "./.qros/bin/qros-paper-to-spec",
        "./.qros/bin/qros-paper-to-spec-baseline",
        "--spec-file",
        "--auto-implement",
        "auto_implement",
        "source -> spec -> materialize -> stop",
        "默认停在 `strategy_spec.yaml`",
    ]

    for needle in forbidden_strings:
        assert needle not in content


def test_codex_readme_documents_paper_to_spec_reset() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "旧 `strategy_spec` materializer 已移除" in content
    assert "paper_data_spec.yaml" in content
    assert "./.qros/bin/qros-paper-to-spec" not in content
    assert "./.qros/bin/qros-paper-to-spec-baseline" not in content
    assert "--auto-implement" not in content
```

- [ ] **Step 2: Update install docs test expectations**

In `tests/docs/test_install_docs.py`, in `test_install_docs_reference_supported_commands`, remove:

```python
    assert "./.qros/bin/qros-paper-to-spec" in combined
    assert "./.qros/bin/qros-paper-to-spec-baseline" in combined
```

Add:

```python
    assert "./.qros/bin/qros-paper-to-spec" not in combined
    assert "./.qros/bin/qros-paper-to-spec-baseline" not in combined
```

Replace `test_codex_readme_documents_paper_to_spec_entrypoints` with:

```python
def test_codex_readme_documents_paper_to_spec_reset() -> None:
    codex_guide = Path("docs/README.codex.md").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in codex_guide
    assert "旧 `strategy_spec` materializer 已移除" in codex_guide
    assert "paper_data_spec.yaml" in codex_guide
    assert "./.qros/bin/qros-paper-to-spec" not in codex_guide
    assert "./.qros/bin/qros-paper-to-spec-baseline" not in codex_guide
```

Replace `test_root_readme_documents_paper_to_spec_usage` with:

```python
def test_root_readme_documents_paper_to_spec_reset() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in readme
    assert "旧 `strategy_spec` materializer 已移除" in readme
    assert "paper_data_spec.yaml" in readme
    assert "strategy_spec.yaml" not in readme
    assert "strategy_spec.md" not in readme
    assert "./.qros/bin/qros-paper-to-spec" not in readme
    assert "./.qros/bin/qros-paper-to-spec-baseline" not in readme
```

- [ ] **Step 3: Run docs tests and verify they fail**

Run:

```bash
python -m pytest tests/docs/test_paper_to_spec_docs.py tests/docs/test_install_docs.py -q
```

Expected: FAIL because active docs still contain old wrapper, baseline, and strategy spec claims.

- [ ] **Step 4: Replace the usage guide**

Replace `docs/guides/qros-paper-to-spec-usage.md` with:

````markdown
# QROS paper-to-spec 使用说明

## 当前状态

`qros-paper-to-spec` 的旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要再把它当作“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”的入口。旧版 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

## 新方向

下一版 `qros-paper-to-spec` 会采用 data-spec-first。第一产物将是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

这个 `paper_data_spec.yaml` 会优先解决：

- PDF 读取覆盖：读了哪些页、哪些章节、哪些表格或公式低置信。
- crypto perpetual 数据需求：universe、bar、price type、funding、fees/slippage、label、timestamp alignment。
- 严格阻断问题：核心 data 口径不清楚时，先停下来问研究员。
- data implementation handoff：后续数据准备需要哪些 raw inputs、derived inputs 和 validation checks。

## 边界

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不是 `qros-research-session` 的阶段入口。
- 不进入 heavy governance flow。
- 不把 crypto perpetual 迁移假设伪装成论文原文。

## 后续

`paper_data_spec.yaml` 稳定后，再继续设计 paper signal spec、train-freeze spec、test-evidence spec 和 backtest spec。
````

- [ ] **Step 5: Update `docs/README.codex.md`**

In `docs/README.codex.md`, replace the old paper-to-spec section with this text:

```markdown
### paper-to-spec v2 方向

`$qros-paper-to-spec` 这个 Codex skill 名称保留，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。当前不要再把它当作 PDF 直接生成完整 strategy spec 或回测代码的入口。

下一版会采用 data-spec-first，第一产物将是 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml`，重点记录 PDF 读取覆盖、crypto perpetual 数据需求、严格阻断问题和 data implementation handoff。

完整说明见 `docs/guides/qros-paper-to-spec-usage.md`。
```

Remove any old `./.qros/bin/qros-paper-to-spec`, `qros-paper-to-spec-baseline`, `--spec-file`, or `--auto-implement` examples from this file.

- [ ] **Step 6: Update `README.md`**

Replace the old `## 📄 paper-to-spec 用法` section in `README.md` with:

````markdown
## 📄 paper-to-spec v2 方向

`$qros-paper-to-spec` 这个 Codex skill 名称保留，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

下一版会采用 data-spec-first，第一产物将是：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

它会优先记录 PDF 读取覆盖、crypto perpetual 数据需求、严格阻断问题和 data implementation handoff。当前不要把它当作 PDF 直接生成完整 strategy spec 或回测代码的入口。

完整说明见 [docs/guides/qros-paper-to-spec-usage.md](docs/guides/qros-paper-to-spec-usage.md)。
````

- [ ] **Step 7: Run docs tests and verify they pass**

Run:

```bash
python -m pytest tests/docs/test_paper_to_spec_docs.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit docs cleanup**

Run:

```bash
git add docs/guides/qros-paper-to-spec-usage.md docs/README.codex.md README.md \
  tests/docs/test_paper_to_spec_docs.py tests/docs/test_install_docs.py
git commit -m "docs: remove old paper-to-spec user path"
```

---

### Task 5: Repo-Wide Active Reference Sweep

**Files:**
- Modify any active doc/test/skill found by the searches below.
- Do not edit historical `docs/superpowers/specs/*` or `docs/superpowers/plans/*` unless they are the new cleanup spec/plan.

- [ ] **Step 1: Search for forbidden old active references**

Run:

```bash
rg -n "qros-paper-to-spec-baseline|--auto-implement|auto_implement|--spec-file|strategy_spec.yaml|strategy_spec.md|runtime/tools/paper_to_spec|run_paper_to_spec" README.md docs skills contracts runtime tests -S
```

Expected before cleanup: any remaining hits are either in historical `docs/superpowers/` files or in files that still need updating.

- [ ] **Step 2: Remove active forbidden references**

For every hit outside `docs/superpowers/`, remove or rewrite the text so active docs and tests no longer present the old capability as available. Keep `paper_data_spec.yaml`, `data-spec-first`, and "旧 `strategy_spec` materializer 已移除" wording where paper-to-spec is discussed.

- [ ] **Step 3: Re-run the forbidden reference search**

Run:

```bash
rg -n "qros-paper-to-spec-baseline|--auto-implement|auto_implement|--spec-file|strategy_spec.yaml|strategy_spec.md|runtime/tools/paper_to_spec|run_paper_to_spec" README.md docs skills contracts runtime tests -S
```

Expected: no hits outside historical `docs/superpowers/` files and the already committed cleanup design/plan.

- [ ] **Step 4: Search for deleted file paths**

Run:

```bash
rg -n "runtime/bin/qros-paper-to-spec|runtime/bin/qros-paper-to-spec-baseline|contracts/paper_to_spec/strategy_spec_contract.yaml|tests/paper_to_spec" README.md docs skills contracts runtime tests -S
```

Expected: no hits outside historical `docs/superpowers/` files and the already committed cleanup design/plan.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py \
  tests/docs/test_paper_to_spec_docs.py \
  tests/skills/test_paper_to_spec_assets.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit reference sweep**

If Step 2 changed files, run:

```bash
git add README.md docs skills contracts runtime tests
git commit -m "chore: sweep old paper-to-spec references"
```

If Step 2 made no changes, do not create an empty commit.

---

### Task 6: Final Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: Run focused verification**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py \
  tests/docs/test_paper_to_spec_docs.py \
  tests/skills/test_paper_to_spec_assets.py -q
```

Expected: PASS.

- [ ] **Step 2: Run smoke verification**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS. If smoke fails because it references deleted paper-to-spec files, update the smoke fixture or bootstrap expectation that owns that reference, then rerun this command.

- [ ] **Step 3: Confirm full-smoke is not required**

Full-smoke is not required for this cleanup because it does not change:

- `qros-research-session` stage flow / gate semantics
- review / display / next-stage orchestration
- route split / CSF routing
- anti-drift snapshots or canonical session stage naming
- stage-display supported stage contract
- lineage-local stage-program auto-author behavior

- [ ] **Step 4: Check working tree**

Run:

```bash
git status --short
```

Expected: no uncommitted changes.
