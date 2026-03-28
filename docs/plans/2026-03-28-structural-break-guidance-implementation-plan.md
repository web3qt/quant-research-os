# Structural Break Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add documentation-only governance so `Test Evidence` and `Holdout Validation` explicitly handle structural-break and parameter-stability claims without binding QROS to a specific statistics library.

**Architecture:** Keep the change at the governance layer. Update the workflow summary, the detailed stage SOPs, the shared checklist and stage-gate contract, then align the duplicated local review skills so all user-facing review surfaces use the same conditional rule: if formal gate claims continuity/stability across windows, it must disclose a structural-break protocol or a reasoned exemption.

**Tech Stack:** Markdown docs, YAML checklist and stage-gate config, local skill files

---

### Task 1: Save The Approved Design And Plan

**Files:**
- Create: `docs/plans/2026-03-28-structural-break-guidance-design.md`
- Create: `docs/plans/2026-03-28-structural-break-guidance-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved scope, gate semantics, accepted method examples, and non-goals.

**Step 2: Write the implementation plan**

Capture the concrete file list and the doc-first verification strategy.

### Task 2: Update Workflow-Level Guidance

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`

**Step 1: Extend the `Test Evidence` summary**

Add one conditional sentence so formal claims about coefficient/relationship continuity require a structural-break protocol or an exemption.

**Step 2: Extend the `Holdout Validation` summary**

Add one conditional sentence so regime-mismatch vs structural-failure judgments require the same disclosure boundary.

**Step 3: Verify the wording**

Run:

```bash
rg -n "结构突变|关系连续|regime 不匹配|稳健推断" docs/main-flow-sop/research_workflow_sop.md
```

Expected: both stage summaries mention the new disclosure rule.

### Task 3: Update The Detailed Test Evidence SOP

**Files:**
- Modify: `docs/main-flow-sop/04_test_evidence_sop_cn.md`

**Step 1: Add a structural-break subsection**

Document when formal gate continuity claims require `Chow / Bai-Perron / CUSUM / rolling coefficient stability` style protocol disclosure and how to interpret break findings.

**Step 2: Update gate, audit-only, and checklist language**

Add one pass condition, one fail condition, one audit-only item, and checklist items so self-review can catch missing structural-break disclosure.

**Step 3: Verify the wording**

Run:

```bash
rg -n "结构突变|Bai-Perron|Chow|CUSUM|rolling coefficient" docs/main-flow-sop/04_test_evidence_sop_cn.md
```

Expected: the SOP shows the new subsection and the aligned gate/checklist wording.

### Task 4: Update The Detailed Holdout Validation SOP

**Files:**
- Modify: `docs/main-flow-sop/06_holdout_validation_sop_cn.md`

**Step 1: Add a structural-break audit subsection**

Document when holdout verdicts need a structural-break protocol to distinguish regime mismatch from actual mechanism failure.

**Step 2: Update gate, audit-only, and checklist language**

Add one conditional pass rule, one fail condition, one audit-only item, and checklist items aligned with the new protocol.

**Step 3: Verify the wording**

Run:

```bash
rg -n "结构突变|Bai-Perron|Chow|CUSUM|regime 不匹配|机制断裂" docs/main-flow-sop/06_holdout_validation_sop_cn.md
```

Expected: the holdout SOP shows the new audit rule and the aligned gate/checklist wording.

### Task 5: Update Shared Review Sources

**Files:**
- Modify: `docs/review-sop/review_checklist_master.yaml`
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Extend checklist and gate sources**

Add the conditional structural-break checks for `test_evidence` and `holdout_validation`, plus aligned audit-only wording.

**Step 2: Verify the wording**

Run:

```bash
rg -n "结构突变|Bai-Perron|Chow|CUSUM|关系连续|regime 不匹配" docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml
```

Expected: both source files encode the same rule.

### Task 6: Align The Duplicated Local Review Skills

**Files:**
- Modify: `.agents/skills/qros-test-evidence-review/SKILL.md`
- Modify: `skills/qros-test-evidence-review/SKILL.md`
- Modify: `.agents/skills/qros-holdout-validation-review/SKILL.md`
- Modify: `skills/qros-holdout-validation-review/SKILL.md`

**Step 1: Update the two review skills**

Mirror the formal-gate, checklist, audit-only, and reviewer-guidance wording introduced in the SOP and gate sources.

**Step 2: Verify the duplicated copies stay in sync**

Run:

```bash
diff -u .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md
diff -u .agents/skills/qros-holdout-validation-review/SKILL.md skills/qros-holdout-validation-review/SKILL.md
```

Expected: no diff output for either pair.

### Task 7: Review The Final Diff

**Files:**
- Modify: only the files listed above

**Step 1: Inspect status and diff**

Run:

```bash
git status --short
git diff -- docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml docs/main-flow-sop/research_workflow_sop.md docs/main-flow-sop/04_test_evidence_sop_cn.md docs/main-flow-sop/06_holdout_validation_sop_cn.md .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md .agents/skills/qros-holdout-validation-review/SKILL.md skills/qros-holdout-validation-review/SKILL.md docs/plans/2026-03-28-structural-break-guidance-design.md docs/plans/2026-03-28-structural-break-guidance-implementation-plan.md
```

Expected: only the approved documentation and skill files changed, with aligned wording across all surfaces.
