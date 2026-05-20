# Session Author Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `qros-research-session` so the author lane uses runtime-generated `stage_author_context` files across `idea_intake`, `mandate`, `tss_*`, and `csf_*`, while reducing duplicated stage-specific author truth in the main session skill.

**Architecture:** Introduce a dedicated author-context runtime module that renders `stage_author_context.yaml` and `stage_author_context.md` from contracts and session/runtime truth. Then split `qros-research-session` conceptually into stage routing, author orchestration, review orchestration, failure orchestration, and guidance surfaces, with author orchestration consuming the generated context through a shared skeleton rather than embedding per-stage author prose.

**Tech Stack:** Python 3.13, PyYAML, existing QROS runtime helpers under `runtime/tools/`, `qros-research-session` skill under `skills/core/`, docs under `docs/guides/`, and pytest-based runtime/session/docs tests.

---

## File Structure

- Create `runtime/tools/author_context_runtime.py`
  - Own the `stage_author_context` schema, rendering, repo-relative path resolution, and markdown summary generation.
- Modify `runtime/tools/research_session.py`
  - Add author-lane helpers to load author context, resolve the next author action, and expose a context-first author skeleton.
- Modify `skills/core/qros-research-session/SKILL.md`
  - Remove long per-stage author truth sections and replace them with author-orchestrator rules plus author-context consumption.
- Modify `docs/guides/qros-research-session-usage.md`
  - Document author context as the current-stage truth entrypoint for session author orchestration.
- Create `tests/session/test_author_context_runtime.py`
  - Cover author context rendering for route-neutral and route-specific stages.
- Modify `tests/session/test_research_session_assets.py`
  - Assert the session skill points to author context instead of embedding stage-specific author truth.
- Modify `tests/docs/test_install_docs.py`
  - Keep doc assertions aligned with the thinner session skill model.

## Task 1: Add Author Context Runtime

**Files:**
- Create: `runtime/tools/author_context_runtime.py`
- Test: `tests/session/test_author_context_runtime.py`

- [ ] **Step 1: Write the failing renderer tests**

Create `tests/session/test_author_context_runtime.py` with:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.author_context_runtime import (
    STAGE_AUTHOR_CONTEXT_MD_FILENAME,
    STAGE_AUTHOR_CONTEXT_YAML_FILENAME,
    build_stage_author_context,
    render_stage_author_context_markdown,
)


def test_build_stage_author_context_for_mandate_contains_truth_and_orchestration() -> None:
    payload = build_stage_author_context(
        stage_id="mandate",
        current_stage="mandate_confirmation_pending",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/01_mandate"),
    )

    assert payload["stage_id"] == "mandate"
    assert payload["stage_name"] == "Mandate"
    assert payload["truth"]["artifact_contract"] == "contracts/artifacts/mandate_artifacts.yaml"
    assert payload["orchestration"]["requires_final_author_confirmation"] is True
    assert payload["orchestration"]["allowed_runtime_stages"] == [
        "mandate_confirmation_pending",
        "mandate_author",
    ]
    assert payload["guidance"]["author_focus"]


def test_build_stage_author_context_for_csf_stage_contains_freeze_group_order() -> None:
    payload = build_stage_author_context(
        stage_id="csf_data_ready",
        current_stage="csf_data_ready_confirmation_pending",
        lineage_id="lineage_a",
        route="cross_sectional_factor",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/02_csf_data_ready"),
    )

    assert payload["stage_id"] == "csf_data_ready"
    assert payload["orchestration"]["freeze_group_order"] == [
        "panel_contract",
        "taxonomy_contract",
        "eligibility_contract",
        "shared_feature_base",
        "delivery_contract",
    ]
    assert "qros-validate-stage --stage csf_data_ready" in payload["truth"]["validator_requirements"]


def test_render_stage_author_context_markdown_mentions_author_entrypoint() -> None:
    payload = build_stage_author_context(
        stage_id="idea_intake",
        current_stage="idea_intake_confirmation_pending",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/00_idea_intake"),
    )

    markdown = render_stage_author_context_markdown(payload)

    assert "stage_author_context" not in markdown
    assert "current-stage author truth entrypoint" in markdown
    assert "idea_intake" in markdown
    assert "confirm all" in markdown.lower()


def test_build_stage_author_context_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="AUTHOR_CONTEXT_MISSING"):
        build_stage_author_context(
            stage_id="unknown_stage",
            current_stage="unknown_stage_confirmation_pending",
            lineage_id="lineage_a",
            route="route_neutral",
            review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/99_unknown_stage"),
        )
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_author_context_runtime.py -q
```

Expected: FAIL because `runtime.tools.author_context_runtime` does not exist.

- [ ] **Step 3: Implement the author context runtime**

Create `runtime/tools/author_context_runtime.py` with:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.artifact_contract_runtime import ARTIFACT_CONTRACTS
from runtime.tools.review_skillgen.review_engine import ROOT


STAGE_AUTHOR_CONTEXT_YAML_FILENAME = "stage_author_context.yaml"
STAGE_AUTHOR_CONTEXT_MD_FILENAME = "stage_author_context.md"


_STAGE_AUTHOR_ORCHESTRATION: dict[str, dict[str, Any]] = {
    "idea_intake": {
        "allowed_runtime_stages": ["idea_intake_confirmation_pending", "idea_intake"],
        "freeze_group_order": ["research_intent", "observation_contract", "qualification_contract"],
        "supports_confirm_all": True,
        "requires_final_author_confirmation": True,
        "next_success_stage": "mandate_confirmation_pending",
        "author_fix_reentry_stage": "idea_intake_confirmation_pending",
        "failure_handoff_skill": "qros-stage-failure-handler",
        "interaction_mode": "interactive_intake",
    },
    "mandate": {
        "allowed_runtime_stages": ["mandate_confirmation_pending", "mandate_author"],
        "freeze_group_order": [
            "research_intent",
            "scope_contract",
            "time_contract",
            "route_contract",
            "delivery_contract",
        ],
        "supports_confirm_all": True,
        "requires_final_author_confirmation": True,
        "next_success_stage": "mandate_review_confirmation_pending",
        "author_fix_reentry_stage": "mandate_author",
        "failure_handoff_skill": "qros-stage-failure-handler",
        "interaction_mode": "contract_freeze",
    },
    "csf_data_ready": {
        "allowed_runtime_stages": ["csf_data_ready_confirmation_pending", "csf_data_ready_author"],
        "freeze_group_order": [
            "panel_contract",
            "taxonomy_contract",
            "eligibility_contract",
            "shared_feature_base",
            "delivery_contract",
        ],
        "supports_confirm_all": True,
        "requires_final_author_confirmation": True,
        "next_success_stage": "csf_data_ready_review_confirmation_pending",
        "author_fix_reentry_stage": "csf_data_ready_author",
        "failure_handoff_skill": "qros-stage-failure-handler",
        "interaction_mode": "contract_freeze",
    },
}


def _repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def _artifact_contract_for_stage(stage_id: str) -> str:
    contract_path = ARTIFACT_CONTRACTS.get(stage_id)
    if contract_path is None:
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing artifact contract for stage {stage_id}")
    return _repo_relative(contract_path)


def _stage_name_for_stage(stage_id: str) -> str:
    mapping = {
        "idea_intake": "Idea Intake",
        "mandate": "Mandate",
        "csf_data_ready": "CSF Data Ready",
    }
    if stage_id not in mapping:
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing stage display metadata for stage {stage_id}")
    return mapping[stage_id]


def _truth_for_stage(stage_id: str) -> dict[str, Any]:
    validator = f"qros-validate-stage --stage {stage_id}" if stage_id != "idea_intake" else "idea_intake_validation"
    return {
        "artifact_contract": _artifact_contract_for_stage(stage_id),
        "required_inputs": [],
        "required_outputs": [],
        "validator_requirements": [validator],
        "preflight_requirements": ["deterministic_preflight"] if stage_id != "idea_intake" else [],
        "failure_route_conditions": ["validator_failed", "preflight_failed", "current_stage_mismatch"],
    }


def _guidance_for_stage(stage_id: str) -> dict[str, Any]:
    return {
        "author_focus": [
            "Confirm unresolved freeze groups before build.",
            "Do not treat placeholder outputs as complete.",
            "Run validation before claiming the stage is author-complete.",
        ],
        "user_prompt_hints": ["Summarize the next unresolved group before asking for confirmation."],
        "group_summary_template": "Show unresolved groups and confirmed groups before the next question.",
        "build_readiness_message": "All required groups are confirmed. Request final author confirmation before build.",
        "common_pitfalls": ["Do not bypass current_stage.", "Do not skip final author confirmation."],
        "do_not_claim_complete_until": ["validator passes", "preflight passes or is not required"],
    }


def build_stage_author_context(
    *,
    stage_id: str,
    current_stage: str,
    lineage_id: str,
    route: str,
    review_cycle_stage_dir: Path,
) -> dict[str, Any]:
    orchestration = _STAGE_AUTHOR_ORCHESTRATION.get(stage_id)
    if orchestration is None:
        raise ValueError(f"AUTHOR_CONTEXT_MISSING: missing author orchestration for stage {stage_id}")
    return {
        "lineage_id": lineage_id,
        "stage_id": stage_id,
        "stage_name": _stage_name_for_stage(stage_id),
        "route": route,
        "current_stage": current_stage,
        "truth": _truth_for_stage(stage_id),
        "orchestration": orchestration,
        "guidance": _guidance_for_stage(stage_id),
        "stage_dir": str(review_cycle_stage_dir),
    }


def render_stage_author_context_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['stage_name']} Author Context",
        "",
        "This file is the current-stage author truth entrypoint for session author orchestration.",
        "",
        "## Interaction Order",
    ]
    for item in payload["orchestration"]["freeze_group_order"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Author Focus",
            *[f"- {item}" for item in payload["guidance"]["author_focus"]],
            "",
            "## Notes",
            f"- supports confirm all: {payload['orchestration']['supports_confirm_all']}",
            f"- requires final author confirmation: {payload['orchestration']['requires_final_author_confirmation']}",
        ]
    )
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/session/test_author_context_runtime.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/author_context_runtime.py tests/session/test_author_context_runtime.py
git commit -m "feat: add session author context runtime"
```

## Task 2: Add Author-Lane Context-First Helpers To Research Session

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_author_context_runtime.py`

- [ ] **Step 1: Write the failing author helper test**

Append this test to `tests/session/test_author_context_runtime.py`:

```python
from runtime.tools.research_session import (
    _author_context_for_current_stage,
    _next_author_action_from_context,
)


def test_author_context_for_current_stage_maps_confirmation_pending_to_stage_context() -> None:
    payload = _author_context_for_current_stage(
        lineage_id="lineage_a",
        current_stage="csf_data_ready_confirmation_pending",
        lineage_root=Path("/tmp/outputs/lineage_a"),
    )

    assert payload["stage_id"] == "csf_data_ready"
    assert payload["current_stage"] == "csf_data_ready_confirmation_pending"


def test_next_author_action_from_context_stops_at_final_confirmation_once_groups_are_done() -> None:
    payload = build_stage_author_context(
        stage_id="mandate",
        current_stage="mandate_author",
        lineage_id="lineage_a",
        route="route_neutral",
        review_cycle_stage_dir=Path("/tmp/outputs/lineage_a/01_mandate"),
    )
    action = _next_author_action_from_context(
        payload,
        unresolved_groups=[],
        all_groups_confirmed=True,
        final_confirmation_complete=False,
    )

    assert action["kind"] == "request_final_author_confirmation"
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_author_context_runtime.py::test_author_context_for_current_stage_maps_confirmation_pending_to_stage_context tests/session/test_author_context_runtime.py::test_next_author_action_from_context_stops_at_final_confirmation_once_groups_are_done -q
```

Expected: FAIL because the helper functions do not exist.

- [ ] **Step 3: Add author-context helpers to `research_session.py`**

In `runtime/tools/research_session.py`, add:

```python
from runtime.tools.author_context_runtime import build_stage_author_context
```

Add helper functions near the other stage-routing helpers:

```python
def _stage_id_from_author_session_stage(current_stage: str) -> str:
    if current_stage.endswith("_confirmation_pending"):
        return current_stage.removesuffix("_confirmation_pending")
    if current_stage.endswith("_author"):
        return current_stage.removesuffix("_author")
    if current_stage == "idea_intake":
        return "idea_intake"
    raise ValueError(f"unsupported author session stage: {current_stage}")


def _route_for_author_stage(stage_id: str) -> str:
    if stage_id.startswith("csf_"):
        return "cross_sectional_factor"
    if stage_id.startswith("tss_"):
        return "time_series_signal"
    return "route_neutral"


def _author_context_for_current_stage(
    *,
    lineage_id: str,
    current_stage: str,
    lineage_root: Path,
) -> dict[str, Any]:
    stage_id = _stage_id_from_author_session_stage(current_stage)
    return build_stage_author_context(
        stage_id=stage_id,
        current_stage=current_stage,
        lineage_id=lineage_id,
        route=_route_for_author_stage(stage_id),
        review_cycle_stage_dir=lineage_root / f"{_stage_dir_name_for_stage_id(stage_id)}",
    )


def _next_author_action_from_context(
    context: dict[str, Any],
    *,
    unresolved_groups: list[str],
    all_groups_confirmed: bool,
    final_confirmation_complete: bool,
) -> dict[str, Any]:
    if unresolved_groups:
        return {"kind": "resolve_next_freeze_group", "group_id": unresolved_groups[0]}
    if all_groups_confirmed and not final_confirmation_complete:
        return {"kind": "request_final_author_confirmation"}
    return {"kind": "build_and_validate"}
```

Also add:

```python
def _stage_dir_name_for_stage_id(stage_id: str) -> str:
    mapping = {
        "idea_intake": "00_idea_intake",
        "mandate": "01_mandate",
        "csf_data_ready": "02_csf_data_ready",
    }
    if stage_id not in mapping:
        raise ValueError(f"missing stage dir mapping for author context stage {stage_id}")
    return mapping[stage_id]
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run:

```bash
python -m pytest tests/session/test_author_context_runtime.py::test_author_context_for_current_stage_maps_confirmation_pending_to_stage_context tests/session/test_author_context_runtime.py::test_next_author_action_from_context_stops_at_final_confirmation_once_groups_are_done -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_author_context_runtime.py
git commit -m "feat: add context-first author helpers to session runtime"
```

## Task 3: Thin The Main Session Skill’s Author Sections

**Files:**
- Modify: `skills/core/qros-research-session/SKILL.md`
- Test: `tests/session/test_research_session_assets.py`

- [ ] **Step 1: Write the failing thin-session-skill test**

Add this test to `tests/session/test_research_session_assets.py`:

```python
def test_session_skill_documents_stage_author_context_as_author_truth_entrypoint() -> None:
    content = Path("skills/core/qros-research-session/SKILL.md").read_text(encoding="utf-8")

    assert "stage_author_context.yaml" in content
    assert "stage_author_context.md" in content
    assert "current-stage author truth entrypoint" in content
    assert "Use the CSF-specific grouped confirmations and ask for these frozen contract groups in order:" not in content
    assert "Use the TSS-specific grouped confirmations and ask for these frozen contract groups in order:" not in content
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py::test_session_skill_documents_stage_author_context_as_author_truth_entrypoint -q
```

Expected: FAIL because the main session skill still embeds route-specific author group lists.

- [ ] **Step 3: Update the session skill**

In `skills/core/qros-research-session/SKILL.md`, replace the route-specific author-lane group sections with a shared author-orchestrator description:

```md
## Author Context

When runtime places the session in an author-eligible stage, do not reconstruct stage-specific author truth from this skill body.
Load:

- `stage_author_context.yaml`
- `stage_author_context.md`

Treat them as the current-stage author truth entrypoint for session author orchestration.

## Author Orchestration Skeleton

For any author-eligible stage:

1. enter
2. load context
3. resolve next interaction
4. collect/confirm
5. final author confirmation
6. build
7. validate/preflight
8. route outcome
```

Keep:

- stage-entry discipline
- failure-routing discipline
- review discipline
- external single-entry semantics

Remove long-form route-specific author group enumerations and repeated stage-specific author output truth.

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py::test_session_skill_documents_stage_author_context_as_author_truth_entrypoint -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/core/qros-research-session/SKILL.md tests/session/test_research_session_assets.py
git commit -m "refactor: thin session author lane prose"
```

## Task 4: Document The New Session Author Model

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `tests/docs/test_install_docs.py`

- [ ] **Step 1: Write the failing docs test**

Add this test to `tests/docs/test_install_docs.py`:

```python
def test_qros_research_session_usage_documents_stage_author_context() -> None:
    content = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    assert "stage_author_context.yaml" in content
    assert "stage_author_context.md" in content
    assert "author truth entrypoint" in content
    assert "author orchestration" in content
```

- [ ] **Step 2: Run the focused docs test to verify it fails**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_qros_research_session_usage_documents_stage_author_context -q
```

Expected: FAIL because the usage guide does not yet describe author context.

- [ ] **Step 3: Update the session usage guide**

In `docs/guides/qros-research-session-usage.md`, add a section near the author/review orchestration explanation:

```md
`qros-research-session` now treats the author lane as a context-first orchestration flow.
When runtime enters an author-eligible stage, the session should consume:

- `stage_author_context.yaml`
- `stage_author_context.md`

These files are the current-stage author truth entrypoint for session author orchestration.
They carry truth-backed fields, orchestration fields, and session-facing guidance, while the main session skill remains the single ordinary author entrypoint.
```

- [ ] **Step 4: Run the focused docs test to verify it passes**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_qros_research_session_usage_documents_stage_author_context -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/guides/qros-research-session-usage.md tests/docs/test_install_docs.py
git commit -m "docs: describe session author context model"
```

## Task 5: Run Session/Docs Verification For The New Author Layer

**Files:**
- Test: `tests/session/test_author_context_runtime.py`
- Test: `tests/session/test_research_session_assets.py`
- Test: `tests/docs/test_install_docs.py`
- Test: `tests/contracts/test_agents_layout.py`
- Test: `tests/bootstrap/test_project_bootstrap.py`

- [ ] **Step 1: Run the focused session/docs suite**

Run:

```bash
python -m pytest \
  tests/session/test_author_context_runtime.py \
  tests/session/test_research_session_assets.py \
  tests/docs/test_install_docs.py \
  tests/contracts/test_agents_layout.py \
  tests/bootstrap/test_project_bootstrap.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run required verification tiers**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS, because this work changes session author orchestration and skill/runtime contract surfaces.

- [ ] **Step 3: Commit**

```bash
git add runtime/tools/author_context_runtime.py runtime/tools/research_session.py skills/core/qros-research-session/SKILL.md docs/guides/qros-research-session-usage.md tests/session/test_author_context_runtime.py tests/session/test_research_session_assets.py tests/docs/test_install_docs.py
git commit -m "feat: make session author lane context first"
```

## Spec Coverage Check

- Internal session layering: covered by Tasks 2 and 3.
- Shared author-lane skeleton: covered by Tasks 2 and 3.
- `stage_author_context.yaml/.md`: covered by Task 1.
- Truth/orchestration/guidance field split: covered by Task 1.
- Full-mainline coverage intent: represented in Task 1’s renderer shape and Task 2’s session helpers; downstream route expansions are scaffolded by the shared context model.
- `idea_intake` and `mandate` as first-class author stages: explicitly covered in Tasks 1 and 2.
- Session docs updated to describe author context as the current-stage entrypoint: covered by Task 4.

## Placeholder Scan

- No `TBD`, `TODO`, or deferred placeholders remain.
- Each task includes exact file paths, concrete code, test commands, and expected outcomes.

## Type Consistency Check

- `stage_author_context.yaml` and `.md` are referenced consistently across tasks.
- `truth`, `orchestration`, and `guidance` remain the consistent top-level sections in the author context shape.
- The author-lane helper names in `research_session.py` are used consistently across the plan.
