# QROS Factor Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only `$qros-factor-diagnostics` skill and runtime command that reports CSF stage diagnostics without changing review, gate, closure, or session state.

**Architecture:** Add machine-readable diagnostics contracts, a small runtime report engine, a CLI wrapper, a repo-local shell entrypoint, a core skill, and user docs. V1 reads existing formal artifacts and reports observed metrics plus evidence gaps; it does not recompute all factor analytics from raw market data.

**Tech Stack:** Python 3.11, PyYAML, pyarrow, existing QROS runtime wrapper style, pytest.

---

### Task 1: Diagnostics Contracts

**Files:**
- Create: `contracts/diagnostics/factor_metric_library.yaml`
- Create: `contracts/diagnostics/csf_stage_diagnostic_profiles.yaml`
- Create: `tests/contracts/test_factor_diagnostic_contracts.py`

- [x] **Step 1: Write failing contract tests**

Add tests that assert both contract files exist, each metric has required fields, each CSF profile has health dimensions, and every referenced metric exists in the library.

Run: `python -m pytest tests/contracts/test_factor_diagnostic_contracts.py -q`

Expected: FAIL because the files do not exist.

- [x] **Step 2: Add contract YAML files**

Add the metric library and stage profiles from the approved design. Keep profile entries diagnostic-only; do not include formal gate verdicts.

- [x] **Step 3: Verify contract tests pass**

Run: `python -m pytest tests/contracts/test_factor_diagnostic_contracts.py -q`

Expected: PASS.

### Task 2: Runtime Diagnostics Engine

**Files:**
- Create: `runtime/tools/factor_diagnostics.py`
- Create: `tests/runtime/test_factor_diagnostics.py`

- [x] **Step 1: Write failing runtime tests**

Cover:

- missing `outputs/` raises a clear diagnostics error and creates no directories
- latest lineage selection chooses the newest lineage
- explicit `lineage_id` is honored
- unsupported stages are rejected
- `csf_test_evidence` reads `mean_rank_ic`
- `csf_backtest_ready` reads `mean_net_return`, `mean_gross_return`, `max_drawdown`, `turnover`, `capacity_utilization`
- `csf_holdout_validation` reads `direction_match`, `holdout_mean_net_return`, `net_return_delta`
- missing metrics are returned as evidence gaps, not command failures

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: FAIL because `runtime.tools.factor_diagnostics` does not exist.

- [x] **Step 2: Implement minimal runtime**

Implement:

- `FactorDiagnosticsError`
- `latest_lineage_id(outputs_root: Path) -> str`
- `diagnostics_payload(outputs_root: Path, lineage_id: str | None, stage: str | None) -> dict[str, object]`
- helpers to load YAML/JSON/CSV/parquet safely
- stage-specific collectors for the six CSF stages

The runtime must be read-only and must not create directories.

- [x] **Step 3: Verify runtime tests pass**

Run: `python -m pytest tests/runtime/test_factor_diagnostics.py -q`

Expected: PASS.

### Task 3: CLI And Wrapper

**Files:**
- Create: `runtime/scripts/run_factor_diagnostics.py`
- Create: `runtime/bin/qros-factor-diagnostics`
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `tests/bootstrap/test_native_skill_runtime_paths.py`

- [x] **Step 1: Write failing CLI/bootstrap tests**

Assert wrapper exists, bootstrap knows it, and the public skill references the repo-local wrapper rather than direct Python script execution.

Run: `python -m pytest tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: FAIL because the wrapper and skill do not exist yet.

- [x] **Step 2: Add CLI script and shell wrapper**

Follow `qros-progress` wrapper style:

- derive `outputs-root` from current project root
- support `--cwd`
- reject user-provided `--outputs-root` at wrapper level
- find Python 3.11+
- locate runtime via `.qros/install-manifest.json` or source tree

- [x] **Step 3: Verify CLI/bootstrap tests pass**

Run: `python -m pytest tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_native_skill_runtime_paths.py -q`

Expected: PASS.

### Task 4: Skill And Docs

**Files:**
- Create: `skills/core/qros-factor-diagnostics/SKILL.md`
- Create: `skills/core/qros-factor-diagnostics/agents/openai.yaml`
- Create: `docs/guides/qros-factor-diagnostics.md`
- Modify: `README.md`
- Modify: `docs/README.codex.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `tests/skills/test_skill_tree.py`
- Create: `tests/docs/test_factor_diagnostics_docs.py`

- [x] **Step 1: Write failing skill/docs tests**

Assert:

- skill tree includes `qros-factor-diagnostics`
- skill is under `skills/core`
- skill says read-only
- skill says it does not replace `qros-review`
- skill forbids writing closure artifacts or gate decisions
- docs mention `$qros-factor-diagnostics` as optional diagnostics
- docs do not describe it as review/gate
- docs list the six supported CSF stages

Run: `python -m pytest tests/skills/test_skill_tree.py tests/docs/test_factor_diagnostics_docs.py -q`

Expected: FAIL because the skill and docs do not exist yet.

- [x] **Step 2: Add skill and docs**

Create the skill with hard boundaries:

- do not write artifact
- do not create lineage
- do not modify `*_gate_decision.md`
- do not write review closure
- do not advance stage
- do not map health to formal PASS/FAIL

Update docs with a short user-facing entry and link to the detailed guide.

- [x] **Step 3: Verify skill/docs tests pass**

Run: `python -m pytest tests/skills/test_skill_tree.py tests/docs/test_factor_diagnostics_docs.py -q`

Expected: PASS.

### Task 5: Final Verification

**Files:**
- All files changed in Tasks 1-4.

- [x] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/contracts/test_factor_diagnostic_contracts.py tests/runtime/test_factor_diagnostics.py tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_native_skill_runtime_paths.py tests/skills/test_skill_tree.py tests/docs/test_factor_diagnostics_docs.py -q
```

Expected: PASS.

- [x] **Step 2: Run required docs/bootstrap minimum**

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

- [x] **Step 4: Commit implementation**

Commit message:

```bash
git commit -m "feat: add qros factor diagnostics"
```
