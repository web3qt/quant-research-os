# Hybrid Stage Review Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a hybrid stage review engine that combines automatic evidence checks with reviewer-supplied findings and writes formal closure artifacts.

**Architecture:** Add a `review_findings` schema loader, a shared `review_engine` that loads stage contract and checklist, validates evidence under the current stage directory, resolves a final verdict, and then writes closure artifacts through the existing writer. Add a thin `scripts/run_stage_review.py` entrypoint and update generated skill text to point to this flow.

**Tech Stack:** Python 3.11+, `PyYAML`, `pytest`, existing `tools/review_skillgen/` package

---

### Task 1: Add Review Findings Schema Loader

**Files:**
- Create: `tools/review_skillgen/review_findings.py`
- Create: `tests/test_review_findings.py`

**Step 1: Write the failing tests**

- Verify `review_findings.yaml` loads as a mapping
- Verify missing list fields normalize to `[]`
- Verify unsupported verdicts fail fast

**Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_review_findings.py -v
```

**Step 3: Implement minimal loader**

- Load YAML from file
- Normalize:
  - `blocking_findings`
  - `reservation_findings`
  - `info_findings`
  - `residual_risks`
  - `allowed_modifications`
  - `downstream_permissions`
- Validate `recommended_verdict` against shared vocabulary

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_review_findings.py -v
```

### Task 2: Add Hybrid Review Engine

**Files:**
- Create: `tools/review_skillgen/review_engine.py`
- Create: `tests/test_review_engine.py`

**Step 1: Write the failing engine tests**

- PASS path: all required files exist and reviewer has no blocking findings
- RETRY path: missing required output downgrades verdict
- `PASS FOR RETRY` path: reviewer recommendation accepted only with rollback metadata

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_review_engine.py -v
```

**Step 3: Implement minimal engine**

- infer context
- load stage contract + checklist
- check `required_outputs`
- check `artifact_catalog.md`
- check `field_dictionary.md` or `*_fields.md`
- check `run_manifest.json` or `repro_manifest.json`
- check recommended gate doc
- load `review_findings.yaml`
- merge auto findings + reviewer findings
- resolve final verdict
- build payload
- call `write_closure_artifacts(...)`

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_review_engine.py -v
```

### Task 3: Add CLI Entrypoint

**Files:**
- Create: `scripts/run_stage_review.py`
- Create: `tests/test_run_stage_review_script.py`

**Step 1: Write the failing CLI test**

- run script in a temp stage dir
- verify closure artifacts are created

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_run_stage_review_script.py -v
```

**Step 3: Implement the script**

- support cwd inference
- support explicit `--stage-dir` and `--lineage-root`
- print final verdict and output paths

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_run_stage_review_script.py -v
```

### Task 4: Expand Shared Vocabulary And Payload Coverage

**Files:**
- Modify: `tools/review_skillgen/closure_models.py`
- Modify: `tools/review_skillgen/closure_writer.py`
- Modify: `tests/test_closure_models.py`
- Modify: `tests/test_closure_writer_stage_outputs.py`

**Step 1: Write or update failing tests**

- align `ALLOWED_VERDICTS` with the gate vocabulary
- persist reviewer/evidence metadata into closure artifacts

**Step 2: Run focused tests to verify they fail**

```bash
python -m pytest tests/test_closure_models.py tests/test_closure_writer_stage_outputs.py -v
```

**Step 3: Implement the minimal updates**

- include `NO-GO` and `GO`
- include:
  - `reviewer_identity`
  - `contract_source`
  - `checklist_source`
  - `required_outputs_checked`
  - `evidence_summary`

**Step 4: Run focused tests to verify they pass**

```bash
python -m pytest tests/test_closure_models.py tests/test_closure_writer_stage_outputs.py -v
```

### Task 5: Update Generated Skills And Usage Docs

**Files:**
- Modify: `templates/skills/review-stage/SKILL.md.tmpl`
- Modify: `scripts/gen_codex_stage_review_skills.py`
- Modify: `tests/test_render.py`
- Modify: `docs/experience/codex-stage-review-skill-usage.md`
- Modify: `tests/test_generated_skills_fresh.py` if needed

**Step 1: Write failing assertions**

- generated skill text should mention `review_findings.yaml`
- generated skill text should mention `python scripts/run_stage_review.py`

**Step 2: Run focused tests to verify they fail**

```bash
python -m pytest tests/test_render.py tests/test_generated_skills_fresh.py -v
```

**Step 3: Implement the template update**

**Step 4: Run focused tests to verify they pass**

```bash
python -m pytest tests/test_render.py tests/test_generated_skills_fresh.py -v
```

### Task 6: Full Verification

**Files:**
- Modify: `tests/test_project_bootstrap.py`

**Step 1: Add existence assertions for new engine files**

**Step 2: Run full verification**

```bash
python -m pytest tests -v
python scripts/gen_codex_stage_review_skills.py --dry-run
```
