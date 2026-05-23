# Codex Research Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Front-load reusable research facts and deterministic preflight checks so Codex users do not repeatedly discover basic data, route, and provenance problems inside reviewer lanes on new QROS lineages.

**Architecture:** Add a dedicated research-preflight layer that runs before review-heavy boundaries and combines runtime-derived truth with tighter user-confirmed freeze contracts. The implementation will first land reusable deterministic checks for data viability, route viability, time coverage, expression identity, and provenance viability, then rewire author/review entry and documentation so reviewer lanes only see stage-local gate questions instead of first-pass basic fact discovery.

**Tech Stack:** Python 3.13, pytest, QROS runtime modules under `runtime/tools/`, CLI wrappers under `runtime/scripts/`, Markdown guides under `docs/guides/`, skill docs under `skills/`.

---

## File Map

### New files

- `runtime/tools/research_preflight.py`
  Deterministic truth layer for research-preflight facts shared across admission, mandate freeze, next-stage confirmation, and review entry.
- `tests/session/test_research_preflight_runtime.py`
  Focused runtime tests for preflight truth categories and priority order.
- `docs/guides/research-preflight-contracts.md`
  User-facing explanation of the new preflight fact families and which ones are user-confirmed vs runtime-derived.

### Modified runtime files

- `runtime/tools/research_session.py`
  Invoke research-preflight checks before mandate freeze, stage freeze, and review confirmation; expose clearer blocked semantics.
- `runtime/tools/progress_runtime.py`
  Project research-preflight blockers consistently in `qros-progress`.
- `runtime/tools/idea_runtime.py`
  Strengthen admission-time route/data-source/bar-size capture so later stages do not rediscover missing basics.
- `runtime/tools/mandate_admission_runtime.py`
  Add admission-time route viability and data viability checks.
- `runtime/tools/author_context_runtime.py`
  Surface preflight-derived facts into stage author context so author lanes inherit deterministic truth instead of recomputing from chat.
- `runtime/tools/review_skillgen/review_preflight.py`
  Shrink reviewer-lane responsibility by assuming preflight-locked facts and rejecting attempts to use review as first-pass discovery.

### Modified docs and skill files

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/stage-freeze-group-field-guide.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/qros-progress/SKILL.md`
- `skills/mandate/qros-mandate-author/SKILL.md`
- `skills/data_ready/qros-data-ready-author/SKILL.md`
- `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`

### Modified test files

- `tests/session/test_research_session_runtime.py`
- `tests/session/test_qros_progress_runtime.py`
- `tests/session/test_idea_runtime_scripts.py`
- `tests/session/test_run_research_session_script.py`
- `tests/skills/test_csf_test_evidence_contract_first_guidance.py`
- `tests/docs/test_install_docs.py`

## Task 1: Add the Core Research Preflight Truth Layer

**Files:**
- Create: `runtime/tools/research_preflight.py`
- Test: `tests/session/test_research_preflight_runtime.py`

- [ ] **Step 1: Write the failing research-preflight tests**

```python
from pathlib import Path

from runtime.tools.research_preflight import (
    ResearchPreflightStatus,
    compute_research_preflight,
)


def test_compute_research_preflight_blocks_when_time_window_exceeds_real_data_coverage(tmp_path):
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    status = compute_research_preflight(
        stage="mandate",
        user_confirmed={
            "research_route": "cross_sectional_factor",
            "bar_size": "5m",
            "train_start": "2023-01-01",
            "holdout_end": "2026-03-01",
        },
        runtime_facts={
            "data_min_ts": "2024-03-01",
            "data_max_ts": "2024-12-31",
        },
    )

    assert status == ResearchPreflightStatus(
        passable=False,
        blocker_family="time_coverage_contract",
        blocker_code="TIME_COVERAGE_OUT_OF_RANGE",
        blocker_reason="Frozen review windows exceed real data coverage.",
        next_action="Adjust train/test/backtest/holdout to fit actual data coverage before mandate freeze.",
    )


def test_compute_research_preflight_allows_route_and_time_window_when_facts_align(tmp_path):
    lineage_root = tmp_path / "outputs" / "case"
    lineage_root.mkdir(parents=True)

    status = compute_research_preflight(
        stage="mandate",
        user_confirmed={
            "research_route": "cross_sectional_factor",
            "bar_size": "5m",
            "train_start": "2024-03-01",
            "holdout_end": "2024-12-31",
        },
        runtime_facts={
            "data_min_ts": "2024-03-01",
            "data_max_ts": "2024-12-31",
        },
    )

    assert status.passable is True
    assert status.blocker_family is None
    assert status.blocker_code is None
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m pytest tests/session/test_research_preflight_runtime.py -v`

Expected: FAIL with `ModuleNotFoundError` for `runtime.tools.research_preflight`

- [ ] **Step 3: Implement the minimal truth model**

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchPreflightStatus:
    passable: bool
    blocker_family: str | None
    blocker_code: str | None
    blocker_reason: str | None
    next_action: str | None


def compute_research_preflight(*, stage: str, user_confirmed: dict[str, str], runtime_facts: dict[str, str]) -> ResearchPreflightStatus:
    if stage == "mandate":
        train_start = user_confirmed["train_start"]
        holdout_end = user_confirmed["holdout_end"]
        data_min_ts = runtime_facts["data_min_ts"]
        data_max_ts = runtime_facts["data_max_ts"]
        if train_start < data_min_ts or holdout_end > data_max_ts:
            return ResearchPreflightStatus(
                passable=False,
                blocker_family="time_coverage_contract",
                blocker_code="TIME_COVERAGE_OUT_OF_RANGE",
                blocker_reason="Frozen review windows exceed real data coverage.",
                next_action="Adjust train/test/backtest/holdout to fit actual data coverage before mandate freeze.",
            )
    return ResearchPreflightStatus(True, None, None, None, None)
```

- [ ] **Step 4: Re-run the tests and confirm they pass**

Run: `python -m pytest tests/session/test_research_preflight_runtime.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_preflight.py tests/session/test_research_preflight_runtime.py
git commit -m "feat: add research preflight truth layer"
```

## Task 2: Front-Load Data Viability and Route Viability Before Mandate Freeze

**Files:**
- Modify: `runtime/tools/idea_runtime.py`
- Modify: `runtime/tools/mandate_admission_runtime.py`
- Modify: `tests/session/test_idea_runtime_scripts.py`

- [ ] **Step 1: Add failing tests for route/data viability before mandate**

```python
def test_build_mandate_from_intake_rejects_route_when_problem_is_clearly_cross_sectional(tmp_path):
    payload = _load_admission_payload(tmp_path)
    payload["route_assessment"]["recommended_route"] = "time_series_signal"
    payload["observation"] = "rank all assets by breakout quality every rebalance"

    result = run_build_mandate_from_intake(tmp_path, payload)

    assert result.returncode != 0
    assert "route_assessment" in result.stderr
    assert "cross_sectional_factor" in result.stderr


def test_build_mandate_from_intake_rejects_time_window_outside_real_data_inventory(tmp_path):
    payload = _load_admission_payload(tmp_path)
    payload["groups"]["scope_contract"]["draft"]["time_boundary"] = "2023-01-01/2026-03-01"
    payload["groups"]["data_contract"]["draft"]["data_source"] = "/tmp/real-data"

    result = run_build_mandate_from_intake(tmp_path, payload)

    assert result.returncode != 0
    assert "time coverage" in result.stderr.lower()
```

- [ ] **Step 2: Run the focused intake/mandate tests**

Run: `python -m pytest tests/session/test_idea_runtime_scripts.py -k "route_assessment or time coverage or build_mandate" -v`

Expected: FAIL because current mandate build does not yet enforce these preflight facts

- [ ] **Step 3: Add deterministic preflight checks to admission/mandate build**

```python
preflight_status = compute_research_preflight(
    stage="mandate",
    user_confirmed={
        "research_route": route_assessment["recommended_route"],
        "bar_size": data_contract["bar_size"],
        "train_start": scope_contract["train_start"],
        "holdout_end": scope_contract["holdout_end"],
    },
    runtime_facts=discover_data_inventory(data_contract["data_source"]),
)
if not preflight_status.passable:
    raise RuntimeError(f"{preflight_status.blocker_code}: {preflight_status.blocker_reason}")
```

- [ ] **Step 4: Re-run the focused intake/mandate tests**

Run: `python -m pytest tests/session/test_idea_runtime_scripts.py -k "route_assessment or time coverage or build_mandate" -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/idea_runtime.py runtime/tools/mandate_admission_runtime.py tests/session/test_idea_runtime_scripts.py
git commit -m "feat: front-load route and data viability before mandate"
```

## Task 3: Surface Preflight Facts in `qros-research-session` and `qros-progress`

**Files:**
- Modify: `runtime/tools/research_session.py`
- Modify: `runtime/tools/progress_runtime.py`
- Modify: `runtime/tools/author_context_runtime.py`
- Modify: `tests/session/test_research_session_runtime.py`
- Modify: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Add failing session/progress tests for preflight blockers**

```python
def test_run_research_session_stays_in_author_fix_when_data_viability_contract_fails(tmp_path):
    status = run_research_session(
        outputs_root=tmp_path / "outputs",
        lineage_id="coverage_blocked_case",
    )

    assert status.current_stage == "mandate_freeze_confirmation_pending"
    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "TIME_COVERAGE_OUT_OF_RANGE"


def test_qros_progress_projects_data_viability_blocker_without_saying_review_ready(tmp_path):
    payload = progress_status_payload(outputs_root=tmp_path / "outputs", lineage_id="coverage_blocked_case")

    assert payload["gate_status"] == "OUTPUTS_INVALID"
    assert "review-ready" not in payload["next_action"].lower()
```

- [ ] **Step 2: Run the session/progress tests**

Run: `python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py -k "preflight or viability or coverage" -v`

Expected: FAIL

- [ ] **Step 3: Project preflight facts into runtime status**

```python
preflight_status = compute_research_preflight(...)
if not preflight_status.passable:
    gate_status = "OUTPUTS_INVALID"
    stage_status = "awaiting_author_fix"
    blocking_reason_code = preflight_status.blocker_code
    next_action = preflight_status.next_action
```

- [ ] **Step 4: Re-run the session/progress tests**

Run: `python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py -k "preflight or viability or coverage" -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py runtime/tools/progress_runtime.py runtime/tools/author_context_runtime.py tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
git commit -m "feat: project research preflight blockers in session status"
```

## Task 4: Tighten Freeze Group Contracts for New Research Lines

**Files:**
- Modify: `docs/guides/stage-freeze-group-field-guide.md`
- Modify: `skills/mandate/qros-mandate-author/SKILL.md`
- Modify: `skills/data_ready/qros-data-ready-author/SKILL.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- Test: `tests/docs/test_install_docs.py`
- Test: `tests/skills/test_csf_test_evidence_contract_first_guidance.py`

- [ ] **Step 1: Add failing docs/skill assertions for the new preflight contracts**

```python
def test_stage_freeze_field_guide_documents_data_viability_contract():
    content = Path("docs/guides/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")
    assert "data_viability_contract" in content
    assert "time_coverage_contract" in content
    assert "route_viability_contract" in content


def test_mandate_author_skill_requires_data_inventory_before_freeze():
    content = Path("skills/mandate/qros-mandate-author/SKILL.md").read_text(encoding="utf-8")
    assert "min_ts" in content
    assert "max_ts" in content
    assert "reviewer should not be the first discovery point" in content.lower()
```

- [ ] **Step 2: Run the focused docs/skills tests**

Run: `python -m pytest tests/docs/test_install_docs.py tests/skills/test_csf_test_evidence_contract_first_guidance.py -v`

Expected: FAIL

- [ ] **Step 3: Rewrite the docs and skills to move common blockers forward**

```markdown
- `data_viability_contract`: data source path, interval, min_ts, max_ts, symbol coverage
- `time_coverage_contract`: whether frozen train/test/backtest/holdout fit actual data inventory
- `route_viability_contract`: whether the research problem is genuinely CSF vs TSS
- `expression_identity_contract`: what must be frozen before downstream exploration
- reviewer is not the first discovery point for these facts
```

- [ ] **Step 4: Re-run the docs/skills tests**

Run: `python -m pytest tests/docs/test_install_docs.py tests/skills/test_csf_test_evidence_contract_first_guidance.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add docs/guides/stage-freeze-group-field-guide.md skills/mandate/qros-mandate-author/SKILL.md skills/data_ready/qros-data-ready-author/SKILL.md skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md tests/docs/test_install_docs.py tests/skills/test_csf_test_evidence_contract_first_guidance.py
git commit -m "docs: front-load common research blockers before review"
```

## Task 5: Narrow Reviewer Lane Expectations

**Files:**
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Test: `tests/review/test_review_preflight.py`

- [ ] **Step 1: Add failing review-preflight tests for already-known blockers**

```python
def test_review_preflight_rejects_stage_when_data_viability_contract_already_failed(tmp_path):
    payload = run_review_preflight(explicit_context={"stage_dir": tmp_path / "stage"})

    assert payload["status"] == "fail"
    assert "data viability" in " ".join(payload["content_findings"]).lower()
```

- [ ] **Step 2: Run the focused review-preflight tests**

Run: `python -m pytest tests/review/test_review_preflight.py -v`

Expected: FAIL

- [ ] **Step 3: Make review-preflight assume preflight-locked facts and reject first-pass discovery use**

```python
if preflight_status and not preflight_status.passable:
    return {
        "status": "fail",
        "content_findings": [preflight_status.blocker_reason],
        "upstream_binding_findings": [],
    }
```

- [ ] **Step 4: Re-run the review-preflight tests**

Run: `python -m pytest tests/review/test_review_preflight.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_skillgen/review_preflight.py docs/guides/qros-review-shared-protocol.md skills/core/qros-research-session/SKILL.md tests/review/test_review_preflight.py
git commit -m "feat: narrow reviewer lane to post-preflight gate questions"
```

## Task 6: Run End-to-End Verification for the Preflight Redesign

**Files:**
- Test: `tests/session/test_research_preflight_runtime.py`
- Test: `tests/session/test_idea_runtime_scripts.py`
- Test: `tests/session/test_research_session_runtime.py`
- Test: `tests/session/test_qros_progress_runtime.py`
- Test: `tests/review/test_review_preflight.py`

- [ ] **Step 1: Run the focused redesign suite**

Run:

```bash
python -m pytest \
  tests/session/test_research_preflight_runtime.py \
  tests/session/test_idea_runtime_scripts.py \
  tests/session/test_research_session_runtime.py \
  tests/session/test_qros_progress_runtime.py \
  tests/review/test_review_preflight.py -v
```

Expected: PASS

- [ ] **Step 2: Run documentation/bootstrap minimum checks**

Run:

```bash
python -m pytest \
  tests/contracts/test_agents_layout.py \
  tests/bootstrap/test_project_bootstrap.py \
  tests/docs/test_install_docs.py -v
```

Expected: PASS

- [ ] **Step 3: Run repository smoke**

Run: `python runtime/scripts/run_verification_tier.py --tier smoke`

Expected: PASS

- [ ] **Step 4: Run repository full-smoke**

Run: `python runtime/scripts/run_verification_tier.py --tier full-smoke`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_preflight.py runtime/tools/idea_runtime.py runtime/tools/mandate_admission_runtime.py runtime/tools/research_session.py runtime/tools/progress_runtime.py runtime/tools/author_context_runtime.py runtime/tools/review_skillgen/review_preflight.py docs/guides/research-preflight-contracts.md docs/guides/stage-freeze-group-field-guide.md docs/guides/qros-review-shared-protocol.md docs/guides/qros-research-session-usage.md skills/mandate/qros-mandate-author/SKILL.md skills/data_ready/qros-data-ready-author/SKILL.md skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md skills/core/qros-research-session/SKILL.md skills/core/qros-progress/SKILL.md tests/session/test_research_preflight_runtime.py tests/session/test_idea_runtime_scripts.py tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py tests/review/test_review_preflight.py tests/docs/test_install_docs.py
git commit -m "feat: front-load research preflight before reviewer lanes"
```

## Spec Coverage Check

- Front-load route/data/time/provenance facts before review: Tasks 1-4
- Distinguish runtime-derived facts from user-confirmed facts: Tasks 1-3
- Move common blockers out of reviewer lane: Tasks 3 and 5
- Narrow reviewer scope to stage-local gate / semantic drift / governance outcome: Task 5
- Make the redesign reusable for future lineages: Tasks 1-4 and 6

## Self-Review Notes

- Placeholder scan complete: no unfinished placeholders or deferred-action markers remain.
- Type consistency check complete: `ResearchPreflightStatus` and `compute_research_preflight()` are used consistently across tasks.
- Scope check complete: this plan stays focused on reusable research preflight, tighter freeze contracts, and reviewer-lane narrowing. It does not attempt to redesign unrelated QROS stages.
