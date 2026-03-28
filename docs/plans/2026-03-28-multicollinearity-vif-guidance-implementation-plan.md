# Multicollinearity And VIF Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add documentation-only governance so `Test Evidence` review explicitly handles multicollinearity and `VIF`-style diagnostics when formal claims rely on multivariate regression coefficient interpretation.

**Architecture:** Keep the change at the governance layer. Update the workflow summary, the detailed `Test Evidence` SOP, the shared checklist and stage-gate contract, then align the duplicated local `qros-test-evidence-review` skills so all review surfaces use the same conditional rule: if formal gate relies on single-coefficient interpretation inside a multivariate regression, it must disclose a multicollinearity diagnostic protocol or a reasoned exemption.

**Tech Stack:** Markdown docs, YAML checklist and stage-gate config, local skill files

---

### Task 1: Save The Approved Design And Plan

**Files:**
- Create: `docs/plans/2026-03-28-multicollinearity-vif-guidance-design.md`
- Create: `docs/plans/2026-03-28-multicollinearity-vif-guidance-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved scope, gate semantics, accepted diagnostic examples, and non-goals.

**Step 2: Write the implementation plan**

Capture the concrete file list and the doc-only verification strategy.

### Task 2: Update Workflow-Level Guidance

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`

**Step 1: Extend the `Test Evidence` summary**

Add one conditional sentence so formal claims that rely on multivariate regression single-coefficient interpretation require a multicollinearity diagnostic protocol or an exemption.

**Step 2: Verify the wording**

Run:

```bash
rg -n "VIF|多重共线性|condition number|共线性" docs/main-flow-sop/research_workflow_sop.md
```

Expected: the `Test Evidence` summary mentions the new disclosure rule.

### Task 3: Update The Detailed Test Evidence SOP

**Files:**
- Modify: `docs/main-flow-sop/04_test_evidence_sop_cn.md`

**Step 1: Extend the robust-inference subsection**

Document when `VIF` matters, how it relates to `condition number` and pairwise correlation checks, and when single-coefficient formal claims need a collinearity protocol.

**Step 2: Update gate, audit-only, and checklist language**

Add one pass condition, one fail condition, one audit-only item, and checklist items so self-review can catch missing multicollinearity diagnostics.

**Step 3: Verify the wording**

Run:

```bash
rg -n "VIF|多重共线性|condition number|共线性" docs/main-flow-sop/04_test_evidence_sop_cn.md
```

Expected: the SOP shows the new diagnostic guidance and aligned gate/checklist wording.

### Task 4: Update Shared Review Sources

**Files:**
- Modify: `docs/review-sop/review_checklist_master.yaml`
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Extend checklist and gate sources**

Add the conditional multicollinearity checks for `test_evidence`, plus aligned audit-only wording.

**Step 2: Verify the wording**

Run:

```bash
rg -n "VIF|多重共线性|condition number|共线性" docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml
```

Expected: both source files encode the same rule.

### Task 5: Align The Duplicated Local Review Skills

**Files:**
- Modify: `.agents/skills/qros-test-evidence-review/SKILL.md`
- Modify: `skills/qros-test-evidence-review/SKILL.md`

**Step 1: Update the two review skills**

Mirror the formal-gate, checklist, audit-only, and reviewer-guidance wording introduced in the SOP and gate sources.

**Step 2: Verify the duplicated copies stay in sync**

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
git diff -- docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml docs/main-flow-sop/research_workflow_sop.md docs/main-flow-sop/04_test_evidence_sop_cn.md .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md docs/plans/2026-03-28-multicollinearity-vif-guidance-design.md docs/plans/2026-03-28-multicollinearity-vif-guidance-implementation-plan.md
```

Expected: only the approved documentation and skill files changed, with aligned wording across all surfaces.
