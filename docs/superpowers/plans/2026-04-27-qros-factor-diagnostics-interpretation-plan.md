# QROS Factor Diagnostics Interpretation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `$qros-factor-diagnostics` explain observed CSF factor diagnostics in Chinese instead of returning only metric values.

**Architecture:** Keep runtime diagnostics read-only. Add deterministic metric-level interpretation fields to `runtime/tools/factor_diagnostics.py`, render them in Chinese text output, then update the skill and docs so Codex treats explanation as required reporting behavior.

**Tech Stack:** Python 3.11, pytest, existing QROS runtime wrappers and skill source.

---

### Task 1: Runtime Interpretation

**Files:**
- Modify: `tests/runtime/test_factor_diagnostics.py`
- Modify: `runtime/tools/factor_diagnostics.py`

- [x] **Step 1: Write failing runtime tests**

Add assertions that negative `rank_ic` includes a Chinese interpretation explaining reverse predictive relation and direction risk, and that backtest metrics include cost/drawdown/capacity interpretation fields.

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: FAIL because observed metrics currently have no interpretation field.

- [x] **Step 2: Implement deterministic metric interpretations**

Add `interpretation` and `severity` to observed metric dictionaries. Keep the rules deterministic and diagnostic-only.

- [x] **Step 3: Verify runtime tests pass**

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: PASS.

### Task 2: Text Rendering

**Files:**
- Modify: `tests/runtime/test_factor_diagnostics.py`
- Modify: `runtime/scripts/run_factor_diagnostics.py`

- [x] **Step 1: Write failing renderer test**

Assert text output includes Chinese sections such as `先说结论`, `怎么理解这些数`, and the metric interpretations.

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: FAIL until renderer is updated.

- [x] **Step 2: Update renderer**

Render Chinese-first report text while preserving lineage, stage, health, confidence, boundary, missing diagnostics, and next diagnostics.

- [x] **Step 3: Verify renderer tests pass**

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: PASS.

### Task 3: Skill And Docs

**Files:**
- Modify: `skills/core/qros-factor-diagnostics/SKILL.md`
- Modify: `docs/guides/qros-factor-diagnostics.md`
- Modify: `README.md`
- Modify: `docs/README.codex.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `tests/docs/test_factor_diagnostics_docs.py`

- [x] **Step 1: Write failing docs/skill tests**

Assert the skill and docs require Chinese explanation, strategy linkage, and no metric-only dump.

Run: `python -m pytest tests/docs/test_factor_diagnostics_docs.py -q`

Expected: FAIL until docs and skill are updated.

- [x] **Step 2: Update skill and docs**

Add user examples for asking what negative mean IC means and require reports to explain meaning, strategy relationship, weak evidence, and next checks in Chinese.

- [x] **Step 3: Verify docs/skill tests pass**

Run: `python -m pytest tests/docs/test_factor_diagnostics_docs.py -q`

Expected: PASS.

### Task 4: Verification And Commit

**Files:**
- All changed files.

- [x] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/runtime/test_factor_diagnostics.py tests/docs/test_factor_diagnostics_docs.py tests/bootstrap/test_native_skill_runtime_paths.py tests/skills/test_skill_tree.py -q
```

Expected: PASS.

- [x] **Step 2: Run docs/bootstrap minimum**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [x] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [x] **Step 4: Commit**

Commit message:

```bash
git commit -m "feat: explain factor diagnostics in Chinese"
```
