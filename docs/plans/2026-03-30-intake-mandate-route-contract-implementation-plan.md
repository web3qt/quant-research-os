# Intake Mandate Route Contract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add first-wave route governance so `idea_intake` recommends a research route and `mandate` freezes a machine-readable route truth for `time_series_signal` and `cross_sectional_factor`.

**Architecture:** Keep the workflow skeleton unchanged. Extend intake artifacts with a route recommendation block, add a dedicated mandate route freeze artifact, update the author/orchestrator skills to ask and persist the new fields, and teach the session runtime to surface route status without yet implementing full downstream route-specific stage contracts.

**Tech Stack:** Markdown SOP docs, YAML schemas/examples, local skill files, Python session/runtime scripts, repo tests

---

### Task 1: Save The Approved Design And Plan

**Files:**
- Create: `docs/plans/2026-03-30-intake-mandate-route-contract-design.md`
- Create: `docs/plans/2026-03-30-intake-mandate-route-contract-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved route taxonomy, intake recommendation contract, mandate freeze contract, downstream routing boundary, scope, non-goals, and acceptance criteria.

**Step 2: Write the implementation plan**

Capture the concrete files, sequencing, and verification steps for the first-wave route-governance change.

### Task 2: Extend Intake Documentation And Artifact Contracts

**Files:**
- Modify: `docs/main-flow-sop/00_idea_intake_sop_cn.md`
- Modify: `docs/intake-sop/idea_gate_decision_schema.yaml`
- Modify: `docs/intake-sop/examples/idea_gate_decision.example.yaml`

**Step 1: Add route assessment to the intake SOP**

Document the four mandatory route-judgment questions, the meaning of `candidate_routes` vs `recommended_route`, and the rule that `GO_TO_MANDATE` requires a non-empty route assessment.

**Step 2: Extend the intake schema**

Add a `route_assessment` block with exact first-wave fields and restrict `recommended_route` / `candidate_routes` to `time_series_signal` and `cross_sectional_factor`.

**Step 3: Update the example artifact**

Show one approved example where `cross_sectional_factor` is recommended over `time_series_signal`.

**Step 4: Verify the wording**

Run:

```bash
rg -n "route_assessment|candidate_routes|recommended_route|why_not_other_routes" docs/main-flow-sop/00_idea_intake_sop_cn.md docs/intake-sop/idea_gate_decision_schema.yaml docs/intake-sop/examples/idea_gate_decision.example.yaml
```

Expected: all three files mention the same intake route fields.

### Task 3: Add Mandate Route Freeze Contracts

**Files:**
- Modify: `docs/main-flow-sop/00_mandate_sop_cn.md`
- Create: `docs/main-flow-sop/research_route_schema.yaml`
- Create: `docs/main-flow-sop/research_route.example.yaml`

**Step 1: Add mandate route freeze language**

Document that `research_route`, `excluded_routes`, `route_rationale`, and `route_change_policy` are frozen inside the `research_intent` confirmation group.

**Step 2: Define the machine-readable route artifact**

Create `research_route_schema.yaml` for the new `01_mandate/research_route.yaml` file and keep the first-wave enum limited to the two approved routes.

**Step 3: Add a concrete example**

Create `research_route.example.yaml` showing a frozen `cross_sectional_factor` mandate with `time_series_signal` in `excluded_routes`.

**Step 4: Verify the wording**

Run:

```bash
rg -n "research_route|excluded_routes|route_change_policy|route_rationale" docs/main-flow-sop/00_mandate_sop_cn.md docs/main-flow-sop/research_route_schema.yaml docs/main-flow-sop/research_route.example.yaml
```

Expected: the SOP, schema, and example all reflect the same mandate route freeze contract.

### Task 4: Update Workflow Summary Guidance

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`

**Step 1: Add governance-vs-route wording**

State that intake/mandate/data governance stays unified while route-specific contract dispatch begins from `signal_ready`.

**Step 2: Verify the wording**

Run:

```bash
rg -n "治理|route|signal_ready|cross_sectional_factor|time_series_signal" docs/main-flow-sop/research_workflow_sop.md
```

Expected: the workflow summary explains the new two-layer model and the `signal_ready` dispatch point.

### Task 5: Update Intake, Mandate, And Session Skills

**Files:**
- Modify: `skills/qros-idea-intake-author/SKILL.md`
- Modify: `skills/qros-mandate-author/SKILL.md`
- Modify: `skills/qros-research-session/SKILL.md`

**Step 1: Update intake interview guidance**

Require the four route-judgment questions and the new `route_assessment` outputs before `GO_TO_MANDATE`.

**Step 2: Update mandate freeze guidance**

Require `research_route` and `excluded_routes` confirmation inside `research_intent`.

**Step 3: Update research-session routing**

Make the orchestrator treat route as a formal state field that must be surfaced at intake/mandate time and reused in later status output.

**Step 4: Verify the wording**

Run:

```bash
rg -n "research_route|route_assessment|candidate_routes|excluded_routes" skills/qros-idea-intake-author/SKILL.md skills/qros-mandate-author/SKILL.md skills/qros-research-session/SKILL.md
```

Expected: all three skills mention the new route contract with consistent field names.

### Task 6: Teach The Runtime To Persist And Report Route State

**Files:**
- Modify: `tools/research_session.py`
- Modify: `scripts/build_mandate_from_intake.py`
- Modify: `scripts/run_research_session.py`
- Test: `tests/test_research_session_runtime.py`
- Test: `tests/test_run_research_session_script.py`
- Test: `tests/test_idea_intake_assets.py`

**Step 1: Persist intake route assessment**

Teach the intake-to-mandate build path to accept `route_assessment` from intake artifacts without silently dropping it.

**Step 2: Persist mandate route freeze**

Write `01_mandate/research_route.yaml` from the confirmed mandate freeze content.

**Step 3: Surface route in session status**

Make the runtime report the current route when intake or mandate artifacts already contain route state.

**Step 4: Add or extend tests**

Cover:
- `GO_TO_MANDATE` intake artifacts missing `route_assessment` should fail validation
- confirmed mandate writes `research_route.yaml`
- session status prints the frozen route when present

**Step 5: Verify the focused tests**

Run:

```bash
python -m pytest tests/test_idea_intake_assets.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py -q
```

Expected: all targeted tests pass with route-governance coverage.

### Task 7: Review The Final Diff

**Files:**
- Modify: only the docs, schemas, skills, runtime, and tests listed above

**Step 1: Inspect status and diff**

Run:

```bash
git status --short
git diff -- docs/main-flow-sop/00_idea_intake_sop_cn.md docs/main-flow-sop/00_mandate_sop_cn.md docs/main-flow-sop/research_workflow_sop.md docs/intake-sop/idea_gate_decision_schema.yaml docs/intake-sop/examples/idea_gate_decision.example.yaml docs/main-flow-sop/research_route_schema.yaml docs/main-flow-sop/research_route.example.yaml skills/qros-idea-intake-author/SKILL.md skills/qros-mandate-author/SKILL.md skills/qros-research-session/SKILL.md tools/research_session.py scripts/build_mandate_from_intake.py scripts/run_research_session.py tests/test_idea_intake_assets.py tests/test_research_session_runtime.py tests/test_run_research_session_script.py docs/plans/2026-03-30-intake-mandate-route-contract-design.md docs/plans/2026-03-30-intake-mandate-route-contract-implementation-plan.md
```

Expected: only the approved first-wave route-governance surfaces changed, with no unrelated files in the diff.
