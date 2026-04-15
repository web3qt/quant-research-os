# Stage Author Review Layout Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure every stage directory so author draft/formal artifacts and review request/result/closure/governance artifacts are written into separate subdirectories instead of being mixed at stage root.

**Architecture:** Introduce a single stage layout contract centered on `stage_root/author/*` and `stage_root/review/*`. Update author runtimes to write only to `author/draft` or `author/formal`, update review infrastructure to write only to `review/*`, and then switch orchestration and tests to read the new paths without old-path compatibility.

**Tech Stack:** Python, YAML, markdown docs, pytest

---

### Task 1: Lock The New Directory Contract In Tests

**Files:**
- Modify: `tests/test_closure_writer_stage_outputs.py`
- Modify: `tests/test_review_engine.py`
- Modify: `tests/test_run_stage_review_script.py`
- Modify: `tests/test_adversarial_review_runtime.py`

**Step 1: Write failing closure path tests**

Add assertions that:

- closure artifacts are written to `review/closure/`
- governance signal is written to `review/governance/`
- review request is read from `review/request/`
- review result is read from `review/result/`

**Step 2: Run focused tests to verify failure**

Run:

```bash
python -m pytest \
  tests/test_closure_writer_stage_outputs.py \
  tests/test_review_engine.py \
  tests/test_run_stage_review_script.py \
  tests/test_adversarial_review_runtime.py -v
```

Expected: failures because the current implementation still reads and writes stage-root review files.

### Task 2: Update Review Context Inference And Closure Writer

**Files:**
- Modify: `tools/review_skillgen/context_inference.py`
- Modify: `tools/review_skillgen/closure_writer.py`
- Modify: `tools/review_governance_runtime.py`
- Modify: `tools/review_skillgen/review_engine.py`

**Step 1: Implement stage layout helpers**

Add helpers that derive:

- `stage_root`
- `author_draft_dir`
- `author_formal_dir`
- `review_request_dir`
- `review_result_dir`
- `review_closure_dir`
- `review_governance_dir`

**Step 2: Switch review read/write paths**

Make review runtime:

- read request from `review/request/adversarial_review_request.yaml`
- read result from `review/result/adversarial_review_result.yaml`
- write closure files to `review/closure/`
- write governance signal to `review/governance/`

**Step 3: Run focused tests**

Run:

```bash
python -m pytest \
  tests/test_closure_writer_stage_outputs.py \
  tests/test_review_engine.py \
  tests/test_run_stage_review_script.py \
  tests/test_adversarial_review_runtime.py -v
```

Expected: review-path tests pass.

### Task 3: Move Mainline Stage Runtime Outputs Into `author/*`

**Files:**
- Modify: `tools/idea_runtime.py`
- Modify: `tools/mandate_runtime.py`
- Modify: `tools/data_ready_runtime.py`
- Modify: `tools/signal_ready_runtime.py`
- Modify: `tools/train_runtime.py`
- Modify: `tools/test_evidence_runtime.py`
- Modify: `tools/backtest_runtime.py`
- Modify: `tools/holdout_runtime.py`
- Modify: relevant script wrappers under `scripts/`

**Step 1: Write failing author path tests**

Add assertions that:

- freeze drafts and transition approvals are under `author/draft/`
- formal artifacts are under `author/formal/`
- `artifact_catalog.md` and `field_dictionary.md` are under `author/formal/`

**Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest \
  tests/test_idea_runtime_scripts.py \
  tests/test_train_runtime.py \
  tests/test_test_evidence_runtime.py -v
```

Expected: failures because formal and draft files are still at stage root.

**Step 3: Implement minimal author path migration**

Update each runtime so:

- draft files write to `author/draft/`
- formal files write to `author/formal/`
- artifact path references and catalogs point to the new locations

**Step 4: Run focused tests**

Run the same test set and confirm pass.

### Task 4: Move CSF Stage Runtime Outputs Into `author/*`

**Files:**
- Modify: `tools/csf_data_ready_runtime.py`
- Modify: `tools/csf_signal_ready_runtime.py`
- Modify: `tools/csf_train_runtime.py`
- Modify: `tools/csf_test_evidence_runtime.py`
- Modify: `tools/csf_backtest_runtime.py`
- Modify: `tools/csf_holdout_runtime.py`

**Step 1: Write failing CSF path tests**

Add assertions that CSF stage outputs now land in:

- `author/draft/`
- `author/formal/`

**Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest \
  tests/test_csf_train_runtime.py \
  tests/test_csf_data_ready_auto_program.py \
  tests/test_idea_runtime_scripts.py -v
```

Expected: failures due to old stage-root assumptions.

**Step 3: Implement minimal CSF runtime changes**

Switch all CSF runtimes to the same layout contract.

**Step 4: Run focused tests**

Run the same test set and confirm pass.

### Task 5: Update Research Session Stage Detection And Upstream Reads

**Files:**
- Modify: `tools/research_session.py`
- Modify: `scripts/run_research_session.py`
- Modify: `tests/test_research_session_runtime.py`
- Modify: `tests/test_run_research_session_script.py`
- Modify: `tests/test_csf_research_session_routing.py`

**Step 1: Write failing state-detection tests**

Add assertions that:

- completion detection reads `review/closure/stage_completion_certificate.yaml`
- author artifacts are loaded from `author/formal/`
- review request checks use `review/request/`

**Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest \
  tests/test_research_session_runtime.py \
  tests/test_run_research_session_script.py \
  tests/test_csf_research_session_routing.py -v
```

Expected: failures because session runtime still assumes stage-root files.

**Step 3: Implement minimal orchestration changes**

Update:

- stage completion probes
- upstream contract reads
- next-stage readiness detection
- user-facing path references

**Step 4: Run focused tests**

Run the same test set and confirm pass.

### Task 6: Update Anti-Drift Fixtures And Scenario Support

**Files:**
- Modify: `tools/anti_drift_scenarios_support.py`
- Modify: `tools/anti_drift_scenarios_mainline.py`
- Modify: `tools/anti_drift_scenarios_csf.py`
- Modify: `tools/anti_drift_scenarios_failure.py`
- Modify: affected files under `tests/fixtures/anti_drift/`
- Modify: `tests/test_anti_drift.py`
- Modify: `tests/test_anti_drift_replay.py`
- Modify: `tests/test_anti_drift_metamorphic.py`

**Step 1: Rewrite fixture generators**

Make generated fixtures produce the new `author/*` and `review/*` structure only.

**Step 2: Run anti-drift tests**

Run:

```bash
python -m pytest \
  tests/test_anti_drift.py \
  tests/test_anti_drift_replay.py \
  tests/test_anti_drift_metamorphic.py -v
```

Expected: pass after fixture regeneration and runtime alignment.

### Task 7: Update Docs And Path Examples

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`
- Modify: `docs/review-sop/stage_completion_standard_cn.md`
- Modify: `docs/review-sop/stage_completion_certificate_template_cn.md`
- Modify: `docs/experience/codex-stage-review-skill-usage.md`
- Modify: `docs/experience/closure-artifact-writer-usage.md`
- Modify: `docs/experience/qros-research-session-usage.md`
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Replace old stage-root path examples**

Document:

- `author/draft/`
- `author/formal/`
- `review/request/`
- `review/result/`
- `review/closure/`
- `review/governance/`

**Step 2: Add explicit downstream-read rule**

State that downstream stages may only consume `author/formal/`.

**Step 3: Run minimal docs checks**

Run:

```bash
python -m pytest tests/test_project_bootstrap.py tests/test_install_docs.py
```

Expected: pass.

### Task 8: Run Full Focused Verification

**Files:**
- Test: review runtime tests
- Test: stage runtime tests
- Test: research session tests
- Test: anti-drift tests
- Test: docs checks

**Step 1: Run verification**

Run:

```bash
python -m pytest \
  tests/test_closure_writer_stage_outputs.py \
  tests/test_review_engine.py \
  tests/test_run_stage_review_script.py \
  tests/test_adversarial_review_runtime.py \
  tests/test_idea_runtime_scripts.py \
  tests/test_train_runtime.py \
  tests/test_test_evidence_runtime.py \
  tests/test_csf_train_runtime.py \
  tests/test_csf_data_ready_auto_program.py \
  tests/test_research_session_runtime.py \
  tests/test_run_research_session_script.py \
  tests/test_csf_research_session_routing.py \
  tests/test_anti_drift.py \
  tests/test_anti_drift_replay.py \
  tests/test_anti_drift_metamorphic.py \
  tests/test_project_bootstrap.py \
  tests/test_install_docs.py -v
```

Expected: all targeted tests pass.

### Task 9: Review Diff And Report Contract Changes

**Files:**
- Modify: only files above

**Step 1: Inspect diff**

Run:

```bash
git status --short
git diff -- tools scripts tests docs
```

**Step 2: Summarize**

Report:

- new stage directory contract
- changed read/write semantics
- no old-path compatibility
- verification evidence
