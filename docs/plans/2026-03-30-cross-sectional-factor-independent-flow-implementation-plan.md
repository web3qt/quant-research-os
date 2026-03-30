# Cross-Sectional Factor Independent Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a fully independent `cross_sectional_factor` research flow after `mandate`, with dedicated CSF stages, route-based runtime routing, CSF-specific review skills, and independent test coverage.

**Architecture:** Keep `idea_intake`, `mandate`, and governance tail stages shared. After `mandate`, route `cross_sectional_factor` into a dedicated `csf_*` stage tree with independent SOP docs, stage-gate truth, runtime modules, skills, and tests. Do not retrofit CSF semantics into the existing time-series stages with conditional branching.

**Tech Stack:** Markdown SOP docs, YAML gate truth, local skill files, Python runtime/session orchestration, repo tests

---

### Task 1: Save The Approved Design And Implementation Plan

**Files:**
- Create: `docs/plans/2026-03-30-cross-sectional-factor-independent-flow-design.md`
- Create: `docs/plans/2026-03-30-cross-sectional-factor-independent-flow-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved independent CSF stage map, state model, stage contracts, review/runtime/testing implications, non-goals, and acceptance criteria.

**Step 2: Write the implementation plan**

Capture the concrete file-level rollout for docs, gate truth, runtime, skills, and tests.

### Task 2: Update Shared Workflow Docs To Route CSF Into An Independent Flow

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`
- Modify: `docs/main-flow-sop/00_mandate_sop_cn.md`
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Update the workflow summary**

State that `cross_sectional_factor` no longer reuses the time-series `signal_ready / train / test / backtest` stages. Document the dedicated `csf_*` flow.

**Step 2: Update mandate downstream guidance**

Document that mandate freeze of `factor_role`, `factor_structure`, `portfolio_expression`, and `neutralization_policy` determines entry into the CSF flow.

**Step 3: Add new stage ids to gate truth**

Add:

- `01_csf_data_ready`
- `02_csf_signal_ready`
- `03_csf_train_freeze`
- `04_csf_test_evidence`
- `05_csf_backtest_ready`
- `06_csf_holdout_validation`

**Step 4: Verify the wording**

Run:

```bash
rg -n "csf_|cross_sectional_factor|factor_role|portfolio_expression|neutralization_policy" docs/main-flow-sop/research_workflow_sop.md docs/main-flow-sop/00_mandate_sop_cn.md docs/gates/workflow_stage_gates.yaml
```

Expected: all three files mention the same independent CSF route vocabulary.

### Task 3: Create Independent CSF SOP Documents

**Files:**
- Create: `docs/main-flow-sop/01_csf_data_ready_sop_cn.md`
- Create: `docs/main-flow-sop/02_csf_signal_ready_sop_cn.md`
- Create: `docs/main-flow-sop/03_csf_train_freeze_sop_cn.md`
- Create: `docs/main-flow-sop/04_csf_test_evidence_sop_cn.md`
- Create: `docs/main-flow-sop/05_csf_backtest_ready_sop_cn.md`
- Create: `docs/main-flow-sop/06_csf_holdout_validation_sop_cn.md`

**Step 1: Write `01_csf_data_ready` SOP**

Describe `date x asset` panel contracts, universe membership, eligibility masks, coverage, and taxonomy requirements.

**Step 2: Write `02_csf_signal_ready` SOP**

Describe factor panel contracts, deterministic multi-factor score support, factor direction, and signal coverage.

**Step 3: Write `03_csf_train_freeze` SOP**

Describe preprocess, standardize, neutralize, quantile bucket, rebalance, and search-governance freeze rules.

**Step 4: Write `04_csf_test_evidence` SOP**

Split formal gate semantics between `standalone_alpha` and `regime_filter | combo_filter`.

**Step 5: Write `05_csf_backtest_ready` SOP**

Describe `long_short_market_neutral` and `long_only_rank` only, with machine-readable portfolio contracts.

**Step 6: Write `06_csf_holdout_validation` SOP**

Describe frozen reuse, holdout-vs-test comparisons, and regime-shift audit expectations.

**Step 7: Verify the file set**

Run:

```bash
ls docs/main-flow-sop/*csf*_sop_cn.md
```

Expected: all six independent CSF SOP files exist.

### Task 4: Extend Stage-Gate Truth For All CSF Stages

**Files:**
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Add `01_csf_data_ready` gate truth**

Encode required inputs, outputs, machine artifacts, human artifacts, formal gate, audit-only findings, rollback rules, and downstream permissions.

**Step 2: Add `02_csf_signal_ready` gate truth**

Require `factor_panel`, `factor_manifest`, deterministic score construction, and explicit direction semantics.

**Step 3: Add `03_csf_train_freeze` gate truth**

Require preprocess / neutralization / bucket / rebalance / eligibility freeze groups and reject ledgers.

**Step 4: Add `04_csf_test_evidence` gate truth**

Encode separate formal-gate expectations for `standalone_alpha` and `regime_filter | combo_filter`.

**Step 5: Add `05_csf_backtest_ready` gate truth**

Require `portfolio_contract`, net-of-cost evidence, concentration diagnostics, and capacity analysis.

**Step 6: Add `06_csf_holdout_validation` gate truth**

Require frozen reuse, holdout-vs-test comparison artifacts, and regime-shift audit outputs.

**Step 7: Verify gate truth coverage**

Run:

```bash
rg -n "01_csf_data_ready|02_csf_signal_ready|03_csf_train_freeze|04_csf_test_evidence|05_csf_backtest_ready|06_csf_holdout_validation" docs/gates/workflow_stage_gates.yaml
```

Expected: all six stages appear exactly once as top-level stage contracts.

### Task 5: Add CSF Runtime Modules And Routing

**Files:**
- Create: `tools/csf_data_ready_runtime.py`
- Create: `tools/csf_signal_ready_runtime.py`
- Create: `tools/csf_train_runtime.py`
- Create: `tools/csf_test_evidence_runtime.py`
- Create: `tools/csf_backtest_runtime.py`
- Create: `tools/csf_holdout_runtime.py`
- Modify: `tools/research_session.py`
- Modify: `scripts/run_research_session.py`

**Step 1: Create CSF scaffold/build runtimes**

Mirror the existing stage runtime pattern, but use CSF-specific draft filenames, group orders, required outputs, and builder entrypoints.

**Step 2: Add route-based stage routing**

Teach `tools/research_session.py` that `research_route = cross_sectional_factor` routes into `01_csf_data_ready` after mandate review instead of the time-series path.

**Step 3: Add CSF status reporting**

Surface `factor_role`, `portfolio_expression`, and current `csf_*` stage in session status where artifacts already exist.

**Step 4: Update the CLI session script**

Print CSF route and stage information clearly without reusing time-series labels.

**Step 5: Verify targeted routing tests**

Run:

```bash
python -m pytest tests/test_research_session_runtime.py tests/test_run_research_session_script.py -q
```

Expected: route-based stage routing passes without entering old time-series stages for CSF lineages.

### Task 6: Add Independent CSF Author And Review Skills

**Files:**
- Create: `skills/qros-csf-data-ready-author/SKILL.md`
- Create: `skills/qros-csf-data-ready-review/SKILL.md`
- Create: `skills/qros-csf-signal-ready-author/SKILL.md`
- Create: `skills/qros-csf-signal-ready-review/SKILL.md`
- Create: `skills/qros-csf-train-freeze-author/SKILL.md`
- Create: `skills/qros-csf-train-freeze-review/SKILL.md`
- Create: `skills/qros-csf-test-evidence-author/SKILL.md`
- Create: `skills/qros-csf-test-evidence-review/SKILL.md`
- Create: `skills/qros-csf-backtest-ready-author/SKILL.md`
- Create: `skills/qros-csf-backtest-ready-review/SKILL.md`
- Create: `skills/qros-csf-holdout-validation-author/SKILL.md`
- Create: `skills/qros-csf-holdout-validation-review/SKILL.md`
- Create matching copies under: `.agents/skills/...`
- Modify: `skills/qros-research-session/SKILL.md`
- Modify: `.agents/skills/qros-research-session/SKILL.md`

**Step 1: Write CSF author skills**

Each author skill must drive grouped confirmation for the CSF-specific freeze contract, artifact set, and prohibited rewrites.

**Step 2: Write CSF review skills**

Each review skill must reference the new CSF formal gate and reject time-series fallback semantics.

**Step 3: Update the research-session skill**

Teach the orchestrator skill to dispatch into the independent CSF stage sequence when `research_route = cross_sectional_factor`.

**Step 4: Sync duplicate skill trees**

Every `skills/` change must be mirrored into `.agents/skills/` for the corresponding files.

**Step 5: Verify skill vocabulary**

Run:

```bash
rg -n "csf_|cross_sectional_factor|factor_role|portfolio_expression" skills .agents/skills
```

Expected: the CSF skill tree and session skill use a consistent vocabulary.

### Task 7: Add Independent CSF Runtime Tests

**Files:**
- Create: `tests/test_csf_data_ready_runtime.py`
- Create: `tests/test_csf_signal_ready_runtime.py`
- Create: `tests/test_csf_train_runtime.py`
- Create: `tests/test_csf_test_evidence_runtime.py`
- Create: `tests/test_csf_backtest_runtime.py`
- Create: `tests/test_csf_holdout_runtime.py`
- Create: `tests/test_csf_research_session_routing.py`
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`

**Step 1: Add CSF stage scaffold/build tests**

For each new runtime module, add focused scaffold/build tests mirroring the existing runtime style.

**Step 2: Add routing regression tests**

Verify:

- CSF lineages do not enter time-series stages after mandate
- missing CSF artifacts block advancement
- CSF status reports route and stage correctly

**Step 3: Add negative tests**

Cover:

- unsupported `factor_role`
- unsupported `portfolio_expression`
- train-freeze data leaking into signal-ready
- test evidence using wrong evidence contract for the current `factor_role`

**Step 4: Verify the CSF-focused suite**

Run:

```bash
python -m pytest tests/test_csf_data_ready_runtime.py tests/test_csf_signal_ready_runtime.py tests/test_csf_train_runtime.py tests/test_csf_test_evidence_runtime.py tests/test_csf_backtest_runtime.py tests/test_csf_holdout_runtime.py tests/test_csf_research_session_routing.py -q
```

Expected: the dedicated CSF suite passes independently of the time-series suite.

### Task 8: Reconcile Shared Governance Hooks

**Files:**
- Modify: `tools/research_session.py`
- Modify: any stage transition helpers that still assume the time-series flow is the only downstream path
- Modify: mandate review/closure hooks only if they still hard-code old stage names

**Step 1: Audit downstream permission assumptions**

Replace any hard-coded assumption that `mandate -> data_ready` always means the old time-series stage tree.

**Step 2: Keep lineage and approval artifacts shared**

Do not duplicate transition approval formats or status vocabularies unless route-specific semantics truly require it.

**Step 3: Verify no old stage leakage remains**

Run:

```bash
rg -n "signal_ready|train_freeze|test_evidence|backtest_ready|holdout_validation" tools/research_session.py skills/qros-research-session/SKILL.md .agents/skills/qros-research-session/SKILL.md
```

Expected: shared session logic still mentions the legacy route, but CSF routing is explicit and not implemented as hidden fall-through.

### Task 9: Final Verification And Diff Review

**Files:**
- Modify only the approved workflow docs, gate truth, CSF runtime modules, shared routing files, skill files, and tests

**Step 1: Run the shared and CSF-focused tests**

Run:

```bash
python -m pytest tests/test_idea_intake_assets.py tests/test_idea_runtime_scripts.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py tests/test_csf_data_ready_runtime.py tests/test_csf_signal_ready_runtime.py tests/test_csf_train_runtime.py tests/test_csf_test_evidence_runtime.py tests/test_csf_backtest_runtime.py tests/test_csf_holdout_runtime.py tests/test_csf_research_session_routing.py -q
```

Expected: both the shared governance tests and the dedicated CSF flow tests pass.

**Step 2: Run whitespace and merge-safety checks**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; only approved files changed.

**Step 3: Review the final diff**

Run:

```bash
git diff -- docs/main-flow-sop docs/gates/workflow_stage_gates.yaml skills .agents/skills tools scripts tests docs/plans/2026-03-30-cross-sectional-factor-independent-flow-design.md docs/plans/2026-03-30-cross-sectional-factor-independent-flow-implementation-plan.md
```

Expected: the diff shows a dedicated CSF flow, not a thin layer of time-series conditionals.
