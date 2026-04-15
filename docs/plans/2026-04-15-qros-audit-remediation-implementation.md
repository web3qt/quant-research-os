# QROS Audit Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复当前 4 个全量测试失败，并把对应 contract 收敛到更小的 shared skill surfaces。

**Architecture:** 先用 focused tests 锁定 anti-drift、closure writer、review skill generation、author language guidance 的目标行为，再做最小代码与文档变更。review skills 继续由生成器维护，author skills 只做轻量引用收敛，不额外引入新的生成系统。

**Tech Stack:** Python, pytest, Markdown skill docs, QROS runtime scripts

---

### Task 1: Lock Anti-Drift Semantics

**Files:**
- Modify: `tests/test_anti_drift.py`
- Modify: `tests/test_anti_drift_metamorphic.py`
- Modify: `runtime/tools/anti_drift.py`

**Step 1: Write the failing test**

- `test_semantic_projection_ignores_lineage_selection_metadata`
- keep metamorphic comparisons on equivalent lineage flows

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_anti_drift.py tests/test_anti_drift_metamorphic.py -q`

**Step 3: Write minimal implementation**

- exclude lineage-selection metadata from `semantic_projection`
- keep raw-idea metamorphic case isolated from slug collision state

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_anti_drift.py tests/test_anti_drift_metamorphic.py -q`

### Task 2: Align Closure Writer Truth Surface

**Files:**
- Modify: `tests/test_closure_writer_context_modes.py`
- Modify: `docs/guides/closure-artifact-writer-usage.md`

**Step 1: Update the failing expectation**

- assert inferred-context closure files live under `review/closure/`

**Step 2: Run focused test**

Run: `python -m pytest tests/test_closure_writer_context_modes.py tests/test_closure_writer_stage_outputs.py -q`

### Task 3: Shrink Review Skill Boilerplate

**Files:**
- Add: `docs/guides/qros-review-shared-protocol.md`
- Modify: `templates/skills/review-stage/SKILL.md.tmpl`
- Modify: `runtime/tools/review_skillgen/render.py`
- Regenerate: `skills/*/qros-*-review/SKILL.md`
- Modify: `tests/test_adversarial_review_skill_generation.py`
- Verify: `tests/test_generated_skills_fresh.py`

**Step 1: Write the failing test**

- generated review skills must reference the shared protocol
- shared protocol doc must carry adversarial contract language

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_adversarial_review_skill_generation.py tests/test_generated_skills_fresh.py -q`

**Step 3: Write minimal implementation**

- move shared review contract into one doc
- shrink template to stage-specific blocks plus shared-protocol reference
- regenerate checked-in review skills

**Step 4: Run tests to verify green**

Run: `python -m pytest tests/test_adversarial_review_skill_generation.py tests/test_generated_skills_fresh.py tests/test_generation.py -q`

### Task 4: Centralize Author Language Guidance

**Files:**
- Add: `docs/guides/qros-authoring-language-discipline.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: all author SKILL files under `skills/*/qros-*-author/SKILL.md`
- Modify: `tests/test_author_skill_comment_contracts.py`
- Modify: `tests/test_research_session_assets.py`

**Step 1: Write the failing test**

- author skills must reference the shared guidance doc
- legacy inline language block should disappear from author skills

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_author_skill_comment_contracts.py tests/test_research_session_assets.py -q`

**Step 3: Write minimal implementation**

- replace inline language block with one shared-reference line

**Step 4: Run tests to verify green**

Run: `python -m pytest tests/test_author_skill_comment_contracts.py tests/test_research_session_assets.py -q`

### Task 5: Expand Full-Smoke Coverage

**Files:**
- Modify: `runtime/tools/verification_tiers.py`
- Modify: `tests/test_verification_tiers.py`
- Modify: `docs/guides/qros-verification-tiers.md`

**Step 1: Write the failing test**

- full-smoke dry-run payload must include the new anti-drift and closure tests

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_verification_tiers.py -q`

**Step 3: Write minimal implementation**

- add `tests/test_anti_drift_metamorphic.py`
- add `tests/test_closure_writer_context_modes.py`

**Step 4: Run verification**

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`
Run: `python runtime/scripts/run_verification_tier.py --tier full-smoke`
Run: `python -m pytest`
