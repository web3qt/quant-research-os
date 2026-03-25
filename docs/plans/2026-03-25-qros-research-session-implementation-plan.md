# QROS Research Session Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a single-entry orchestrated research session flow so a user can start from one skill, have QROS detect or create the lineage and current stage, and automatically drive `idea_intake -> mandate -> mandate_review` while persisting state to disk.

**Architecture:** Introduce a lightweight orchestration runtime in `tools/research_session.py` plus a thin script wrapper in `scripts/run_research_session.py`. The runtime reuses existing deterministic components in `tools/idea_runtime.py` and `tools/review_skillgen/review_engine.py`, while a new `qros-research-session` skill defines the conversation contract and state reporting. The first version focuses on stage detection, controlled progression, and consistent status summaries rather than broad stage coverage.

**Tech Stack:** Python 3.11, `pytest`, existing QROS skills, existing review engine and idea runtime

---

### Task 1: Lock Bootstrap And Session Contract Tests

**Files:**
- Modify: `tests/test_project_bootstrap.py`
- Create: `tests/test_research_session_runtime.py`

**Step 1: Write the failing bootstrap assertions**

Extend `tests/test_project_bootstrap.py` to assert these files exist:

- `tools/research_session.py`
- `scripts/run_research_session.py`
- `.agents/skills/qros-research-session/SKILL.md`
- `docs/experience/qros-research-session-usage.md`

Also extend usage doc checks so the repo bootstrap test expects the new session usage document.

**Step 2: Write failing session runtime tests**

Create `tests/test_research_session_runtime.py` with coverage for:

- deriving a lineage slug from a raw idea
- detecting `idea_intake` when no lineage exists yet
- detecting `idea_intake` when `00_idea_intake/` exists but the gate is not `GO_TO_MANDATE`
- detecting `mandate_author` when intake is admitted but `01_mandate/` artifacts are missing
- detecting `mandate_review` when mandate artifacts exist but no review closure artifacts exist
- detecting `mandate_review_complete` when closure artifacts exist
- status summaries include `lineage`, `current_stage`, `artifacts_written`, `gate_status`, and `next_action`

Keep these tests strictly against the runtime layer. Do not touch skills or scripts yet.

**Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_project_bootstrap.py tests/test_research_session_runtime.py -v`

Expected: FAIL because the session runtime and skill assets do not exist yet.

**Step 4: Commit**

```bash
git add tests/test_project_bootstrap.py tests/test_research_session_runtime.py
git commit -m "test: add research session bootstrap expectations"
```

### Task 2: Implement The Session Runtime Core

**Files:**
- Create: `tools/research_session.py`
- Test: `tests/test_research_session_runtime.py`

**Step 1: Write minimal session runtime structures**

Implement:

- `SessionStage = Literal["idea_intake", "mandate_author", "mandate_review", "mandate_review_complete"]`
- `SessionContext` dataclass with `lineage_id`, `lineage_root`, `current_stage`, `artifacts_written`, `gate_status`, `next_action`

Add helpers:

- `slugify_idea(raw_idea: str) -> str`
- `resolve_lineage_root(outputs_root: Path, lineage_id: str | None, raw_idea: str | None) -> Path`
- `detect_session_stage(lineage_root: Path) -> str`
- `summarize_session_status(...) -> SessionContext`

**Step 2: Implement orchestrated deterministic actions**

Add functions that reuse existing runtime:

- `ensure_intake_scaffold(lineage_root: Path) -> list[str]`
- `build_mandate_if_admitted(lineage_root: Path) -> list[str]`
- `run_mandate_review_if_ready(lineage_root: Path) -> dict[str, object] | None`

Rules:

- never advance beyond `mandate_review`
- do not fabricate review findings
- only call mandate build when `idea_gate_decision.yaml.verdict == GO_TO_MANDATE`
- only call mandate review when required mandate outputs and `review_findings.yaml` exist

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_research_session_runtime.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add tools/research_session.py tests/test_research_session_runtime.py
git commit -m "feat: add research session runtime core"
```

### Task 3: Add The Script Entry Point

**Files:**
- Create: `scripts/run_research_session.py`
- Create: `tests/test_run_research_session_script.py`
- Modify: `tools/research_session.py`

**Step 1: Write the failing script tests**

Create `tests/test_run_research_session_script.py` to verify:

- the script can create a new lineage from `--raw-idea ...`
- the script scaffolds `00_idea_intake/` when starting from nothing
- the script reports `idea_intake` as current stage when intake is incomplete
- the script reports `mandate_author` after intake is admitted but before mandate artifacts exist
- the script reports `mandate_review` when mandate artifacts exist and review is pending

Use `tmp_path` and a temporary `outputs/` root.

**Step 2: Implement the wrapper**

Create `scripts/run_research_session.py` with a CLI like:

- `--outputs-root`
- `--lineage-id`
- `--raw-idea`

The script should:

- resolve or create lineage
- ensure intake scaffold when needed
- detect current stage
- optionally run deterministic actions for the current stage
- print a concise session status summary

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_run_research_session_script.py tests/test_research_session_runtime.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add scripts/run_research_session.py tests/test_run_research_session_script.py tools/research_session.py
git commit -m "feat: add research session script entry point"
```

### Task 4: Add The Orchestrator Skill And Usage Doc

**Files:**
- Create: `.agents/skills/qros-research-session/SKILL.md`
- Create: `.agents/skills/qros-research-session/agents/openai.yaml`
- Create: `docs/experience/qros-research-session-usage.md`
- Create: `tests/test_research_session_assets.py`
- Modify: `tests/test_project_bootstrap.py`

**Step 1: Write the failing asset tests**

Create `tests/test_research_session_assets.py` to assert:

- the new skill exists
- it references `idea_intake`, `mandate`, and `mandate review`
- it instructs the agent to auto-write artifacts and reuse the session runtime
- the usage doc exists and mentions `python scripts/run_research_session.py`

Extend `tests/test_project_bootstrap.py` so the session skill and usage doc become part of the repo bootstrap contract.

**Step 2: Write the new assets**

Create `qros-research-session` skill with sections covering:

- purpose
- scope and stage boundary
- lineage resolution
- stage detection
- when to auto-act versus when to ask the user
- required status reporting format

Create `docs/experience/qros-research-session-usage.md` with:

- one-skill mental model
- how the runtime decides current stage
- example session from raw idea to mandate review
- explicit note that `data_ready` is out of scope in v1

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_research_session_assets.py tests/test_project_bootstrap.py -v`

Expected: PASS

**Step 4: Commit**

```bash
git add .agents/skills/qros-research-session/SKILL.md .agents/skills/qros-research-session/agents/openai.yaml docs/experience/qros-research-session-usage.md tests/test_research_session_assets.py tests/test_project_bootstrap.py
git commit -m "feat: add qros research session skill"
```

### Task 5: Run Full Verification And Smoke The Session Flow

**Files:**
- Verify only: repository-wide

**Step 1: Run the full test suite**

Run: `python -m pytest tests -v`

Expected: PASS with the new session runtime, script, skill, and docs included.

**Step 2: Smoke-test the orchestrated flow**

Run in the repo root:

```bash
python scripts/run_research_session.py --outputs-root /tmp/qros-session-smoke/outputs --raw-idea "BTC leads high-liquidity alts after shock events"
```

Expected:

- a lineage is created automatically
- `00_idea_intake/` is scaffolded
- the reported stage is `idea_intake`

Then prepare a minimal admitted intake and rerun:

```bash
python scripts/run_research_session.py --outputs-root /tmp/qros-session-smoke/outputs --lineage-id <generated-lineage>
```

Expected:

- the runtime detects `mandate_author` or `mandate_review` correctly depending on the artifacts present

**Step 3: Review git status**

Run: `git status --short`

Expected: clean, or only the intended tracked files changed. Do not commit smoke outputs under `/tmp`.

**Step 4: Commit final implementation**

```bash
git add tools/research_session.py scripts/run_research_session.py .agents/skills/qros-research-session/SKILL.md .agents/skills/qros-research-session/agents/openai.yaml docs/experience/qros-research-session-usage.md tests/test_research_session_runtime.py tests/test_run_research_session_script.py tests/test_research_session_assets.py tests/test_project_bootstrap.py
git commit -m "feat: add qros research session orchestrator"
```
