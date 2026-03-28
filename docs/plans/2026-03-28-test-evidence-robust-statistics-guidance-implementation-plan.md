# Test Evidence Robust Statistics Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add documentation-only guidance so `Test Evidence` review and stage gates explicitly handle heteroskedasticity-, autocorrelation-, and robust-inference concerns without binding the workflow to a specific Python statistics library.

**Architecture:** Keep the change at the governance layer. Update the workflow summary, the detailed `Test Evidence` SOP, the stage-gate contract, and the duplicated local `qros-test-evidence-review` skills so all four surfaces use the same rule: formal statistical claims need a documented robust-inference protocol when they rely on regression-style significance.

**Tech Stack:** Markdown docs, YAML stage-gate config, local skill files

---

### Task 1: Save The Approved Design And Plan

**Files:**
- Create: `docs/plans/2026-03-28-test-evidence-robust-statistics-guidance-design.md`
- Create: `docs/plans/2026-03-28-test-evidence-robust-statistics-guidance-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved scope, gate semantics, accepted method examples, and non-goals.

**Step 2: Write the implementation plan**

Capture the concrete file list and verification approach for the documentation-only change.

### Task 2: Update Workflow-Level Guidance

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`

**Step 1: Add the summary requirement**

Extend the `Test Evidence` summary so it explicitly requires a documented robust-inference protocol whenever formal gate evidence depends on `t` values, `p` values, regressions, or residual-style significance.

**Step 2: Verify the wording**

Run:

```bash
rg -n "稳健推断|formal gate|t 值|p 值" docs/main-flow-sop/research_workflow_sop.md
```

Expected: the summary line shows the new robust-inference requirement.

### Task 3: Update The Detailed Test Evidence SOP

**Files:**
- Modify: `docs/main-flow-sop/04_test_evidence_sop_cn.md`

**Step 1: Add a robust-inference subsection**

Document when heteroskedasticity/autocorrelation matters, which methods are acceptable examples, and the boundary between audit-only and formal evidence.

**Step 2: Update gate and checklist language**

Add one formal-gate requirement, one fail case, and checklist items so self-review can catch missing robust-inference disclosure.

**Step 3: Verify the wording**

Run:

```bash
rg -n "HAC|Newey-West|White|Breusch|WLS|GLS|ARCH|GARCH|稳健推断" docs/main-flow-sop/04_test_evidence_sop_cn.md
```

Expected: the SOP contains the new method examples and the gate/checklist language.

### Task 4: Update The Stage-Gate Contract

**Files:**
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Add the gate rule**

Require robust-inference disclosure when formal gate uses regression-style significance, and add the related audit-only note and explanatory note.

**Step 2: Verify the wording**

Run:

```bash
rg -n "HAC|White|Breusch|OLS|稳健推断" docs/gates/workflow_stage_gates.yaml
```

Expected: the stage contract reflects the same rule as the SOP.

### Task 5: Update The Duplicated Local Review Skills

**Files:**
- Modify: `.agents/skills/qros-test-evidence-review/SKILL.md`
- Modify: `skills/qros-test-evidence-review/SKILL.md`

**Step 1: Add reviewer guidance**

Update the formal gate summary, checklist, audit-only items, and a short reviewer guidance section so the agent knows how to treat robust-inference issues during review.

**Step 2: Verify the two copies stay in sync**

Run:

```bash
diff -u .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md
```

Expected: no diff output.

### Task 6: Review The Final Diff

**Files:**
- Modify: only the files listed above

**Step 1: Inspect status and diff**

Run:

```bash
git status --short
git diff -- .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md docs/gates/workflow_stage_gates.yaml docs/main-flow-sop/04_test_evidence_sop_cn.md docs/main-flow-sop/research_workflow_sop.md docs/plans/2026-03-28-test-evidence-robust-statistics-guidance-design.md docs/plans/2026-03-28-test-evidence-robust-statistics-guidance-implementation-plan.md
```

Expected: only the approved documentation and skill files changed, with aligned wording across all surfaces.
