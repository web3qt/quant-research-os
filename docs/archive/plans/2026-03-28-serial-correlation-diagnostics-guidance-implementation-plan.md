# Serial Correlation Diagnostics Guidance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add documentation-only governance so `Test Evidence` review explicitly handles residual serial-correlation diagnostics without binding QROS to a specific statistics library.

**Architecture:** Keep the change at the governance layer. Update the workflow summary, the detailed `Test Evidence` SOP, the shared checklist and stage-gate contract, then align the duplicated local `qros-test-evidence-review` skills so all review surfaces use the same conditional rule: if formal gate relies on residual independence or raw `OLS` error assumptions, it must disclose a serial-correlation diagnostic protocol or a reasoned exemption.

**Tech Stack:** Markdown docs, YAML checklist and stage-gate config, local skill files

---

### Task 1: Save The Approved Design And Plan

**Files:**
- Create: `docs/plans/2026-03-28-serial-correlation-diagnostics-guidance-design.md`
- Create: `docs/plans/2026-03-28-serial-correlation-diagnostics-guidance-implementation-plan.md`

**Step 1: Write the design doc**

Capture the approved scope, gate semantics, accepted diagnostic examples, and non-goals.

**Step 2: Write the implementation plan**

Capture the concrete file list and doc-only verification approach.

### Task 2: Update Workflow-Level Guidance

**Files:**
- Modify: `docs/main-flow-sop/research_workflow_sop.md`

**Step 1: Extend the `Test Evidence` summary**

Add one conditional sentence so formal claims that rely on residual independence or raw `OLS` assumptions require a serial-correlation diagnostic protocol or an exemption.

**Step 2: Verify the wording**

Run:

```bash
rg -n "自相关诊断|Durbin-Watson|Breusch-Godfrey|Ljung-Box|稳健推断" docs/main-flow-sop/research_workflow_sop.md
```

Expected: the `Test Evidence` summary mentions the new disclosure rule.

### Task 3: Update The Detailed Test Evidence SOP

**Files:**
- Modify: `docs/main-flow-sop/04_test_evidence_sop_cn.md`

**Step 1: Extend the robust-inference subsection**

Document when `Durbin-Watson`、`Breusch-Godfrey LM`、`Ljung-Box` matter, how they relate to `HAC / Newey-West`, and when raw `OLS` residual-independence claims need a protocol.

**Step 2: Update gate, audit-only, and checklist language**

Add one pass condition, one fail condition, one audit-only item, and checklist items so self-review can catch missing serial-correlation diagnostics.

**Step 3: Verify the wording**

Run:

```bash
rg -n "Durbin-Watson|Breusch-Godfrey|Ljung-Box|自相关诊断|serial correlation" docs/main-flow-sop/04_test_evidence_sop_cn.md
```

Expected: the SOP shows the new diagnostic guidance and aligned gate/checklist wording.

### Task 4: Update Shared Review Sources

**Files:**
- Modify: `docs/review-sop/review_checklist_master.yaml`
- Modify: `docs/gates/workflow_stage_gates.yaml`

**Step 1: Extend checklist and gate sources**

Add the conditional serial-correlation checks for `test_evidence`, plus aligned audit-only wording.

**Step 2: Verify the wording**

Run:

```bash
rg -n "Durbin-Watson|Breusch-Godfrey|Ljung-Box|自相关诊断|serial correlation" docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml
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
git diff -- docs/review-sop/review_checklist_master.yaml docs/gates/workflow_stage_gates.yaml docs/main-flow-sop/research_workflow_sop.md docs/main-flow-sop/04_test_evidence_sop_cn.md .agents/skills/qros-test-evidence-review/SKILL.md skills/qros-test-evidence-review/SKILL.md docs/plans/2026-03-28-serial-correlation-diagnostics-guidance-design.md docs/plans/2026-03-28-serial-correlation-diagnostics-guidance-implementation-plan.md
```

Expected: only the approved documentation and skill files changed, with aligned wording across all surfaces.
