# Idea Intake To Mandate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a structured `idea_intake -> mandate` pre-research flow that qualifies ideas before they are allowed to become formal mandates.

**Architecture:** Introduce a new `00_idea_intake` stage with machine-readable qualification artifacts, then add first-wave author-facing assets for `qros-idea-intake-author` and `qros-mandate-author`. Keep the first version doc-first and generation-friendly so it can later feed the existing skill/runtime stack.

**Tech Stack:** Markdown, YAML, existing `docs/`, `.agents/skills/`, generator-oriented repository structure

---

### Task 1: Add Intake Schemas

**Files:**
- Create: `docs/intake-sop/qualification_scorecard_schema.yaml`
- Create: `docs/intake-sop/idea_gate_decision_schema.yaml`

**Step 1: Define qualification score dimensions**

- `observability`
- `mechanism_plausibility`
- `tradeability`
- `data_feasibility`
- `scoping_clarity`
- `distinctiveness`

Each dimension should specify required fields and allowed score range.

**Step 2: Define gate decision schema**

- `verdict`
- `why`
- `approved_scope`
- `required_reframe_actions`
- `rollback_target`

**Step 3: Add one example block per schema**

### Task 2: Add Design/Usage Documentation

**Files:**
- Create: `docs/experience/idea-intake-to-mandate-flow.md`

**Step 1: Document the new pre-mandate flow**

- `Idea -> Observation -> Hypothesis -> Qualification -> Mandate`
- required artifacts
- gate rules
- handoff into `mandate`

### Task 3: Add First-Wave Skill Specs

**Files:**
- Create: `.agents/skills/qros-idea-intake-author/SKILL.md`
- Create: `.agents/skills/qros-idea-intake-author/agents/openai.yaml`
- Create: `.agents/skills/qros-mandate-author/SKILL.md`
- Create: `.agents/skills/qros-mandate-author/agents/openai.yaml`

**Step 1: Define `qros-idea-intake-author`**

- produce `00_idea_intake` artifacts
- require counter-hypothesis
- require qualification scorecard
- require machine-readable gate decision

**Step 2: Define `qros-mandate-author`**

- consume only qualified intake artifacts
- freeze scope into mandate outputs
- forbid post-hoc restatement

### Task 4: Add Minimal Template Assets

**Files:**
- Create: `docs/intake-sop/examples/qualification_scorecard.example.yaml`
- Create: `docs/intake-sop/examples/idea_gate_decision.example.yaml`

**Step 1: Provide a BTC-led ALT transmission example**

### Task 5: Add Bootstrap Coverage

**Files:**
- Modify: `tests/test_project_bootstrap.py`

**Step 1: Assert existence of the new schema/docs/skill files**

### Task 6: Full Verification

**Step 1: Run tests**

```bash
python -m pytest tests -v
```

**Step 2: Manually inspect the new artifacts for coherence**
