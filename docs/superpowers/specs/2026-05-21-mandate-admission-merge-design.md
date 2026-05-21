# Mandate Admission Merge Design

**Date:** 2026-05-21  
**Status:** Draft for user review  
**Scope:** Breaking redesign of the QROS first-stage workflow from `idea_intake -> mandate` into a single `mandate` stage with an internal admission subflow.

## Purpose

QROS currently treats `idea_intake` and `mandate` as two separate stages. In real use, this creates too many visible gates before the user reaches the first formal research contract:

- `idea_intake_confirmation_pending`
- incomplete qualification repair
- `mandate_confirmation_pending`
- mandate freeze group confirmation
- final mandate approval

The user experience is fragmented, and the runtime truth is hard to explain. The first-stage workflow should instead feel like one coherent mandate-forming conversation: qualify the idea, choose the route, freeze the research contract, and then generate formal mandate artifacts.

The new design removes `idea_intake` as an independent normal-path stage and folds its responsibilities into `mandate`.

## Decision

Replace the normal first-stage chain:

```text
idea_intake -> idea_intake_confirmation_pending -> mandate_confirmation_pending -> mandate_author -> mandate_review_confirmation_pending
```

with:

```text
mandate_admission -> mandate_freeze_confirmation_pending -> mandate_author -> mandate_review_confirmation_pending
```

There is no normal-path `CONFIRM_IDEA_INTAKE`. The only pre-authoring user confirmation is the final mandate freeze approval.

This is a breaking workflow change. The new runtime does not need to preserve automatic continuation for old lineages that are still parked in `00_idea_intake/` or `mandate_confirmation_pending`.

## Stage Semantics

### `mandate_admission`

The lineage is in the first mandate stage, but admission evidence is incomplete or the idea has not been accepted for mandate.

This substate is responsible for:

- capturing the raw idea
- writing the observation
- writing the primary hypothesis and counter-hypothesis
- defining scope, data source, bar size, universe, target task, and excluded scope
- scoring qualification dimensions
- choosing the route
- recording kill criteria and reframe actions
- producing the admission verdict

The admission verdict is machine-readable:

```yaml
admission_decision:
  verdict: ACCEPT_FOR_MANDATE | NEEDS_REFRAME | DROP
```

Only `ACCEPT_FOR_MANDATE` permits mandate freeze confirmation.

### `mandate_freeze_confirmation_pending`

Admission passed, and the runtime has enough information to present the complete mandate freeze draft. The user reviews one consolidated summary and gives one final approval to freeze mandate.

This state replaces the old split between intake confirmation and mandate confirmation. It should expose one clear user question:

```text
是否确认冻结 mandate？
```

After approval, the runtime writes the durable mandate transition approval and enters `mandate_author`.

### `mandate_author`

The mandate stage program consumes draft inputs and generates the formal mandate artifacts under `01_mandate/author/formal/`.

The author lane must not consume chat history as proof. It consumes the machine-readable draft files on disk.

### `mandate_review_confirmation_pending`

Formal mandate artifacts exist and pass deterministic preflight. The runtime asks for explicit review confirmation before launching the independent reviewer lane.

## Artifact Layout

The new first-stage disk layout is:

```text
outputs/<lineage>/
  01_mandate/
    author/
      draft/
        mandate_admission.yaml
        mandate_freeze_draft.yaml
        mandate_transition_approval.yaml
      formal/
        mandate.md
        research_scope.md
        research_route.yaml
        time_split.json
        parameter_grid.yaml
        run_config.toml
        artifact_catalog.md
        field_dictionary.md
```

No new lineage should create `00_idea_intake/` in the normal path.

## Compressed Admission Contract

The old `00_idea_intake` shape had too many separate files for what is conceptually one admission record. The new design compresses admission evidence into one machine-readable file:

```text
01_mandate/author/draft/mandate_admission.yaml
```

It replaces the normal-path use of:

- `idea_brief.md`
- `intake_interview.md`
- `observation_hypothesis_map.md`
- `research_question_set.md`
- `scope_canvas.yaml`
- `qualification_scorecard.yaml`
- `idea_gate_decision.yaml`

Suggested shape:

```yaml
lineage_id: ""
raw_idea: ""
observation: ""
primary_hypothesis: ""
counter_hypothesis: ""
research_questions: []
scope:
  market: ""
  instrument_type: ""
  universe: ""
  data_source: ""
  bar_size: ""
  holding_horizons: []
  target_task: ""
  excluded_scope: []
  budget_days: 0
  max_iterations: 0
qualification:
  summary: ""
  dimensions:
    observability:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
    mechanism_plausibility:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
    tradeability:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
    data_feasibility:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
    scoping_clarity:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
    distinctiveness:
      score: 0
      evidence: []
      uncertainty: []
      kill_reason: []
route_assessment:
  candidate_routes: []
  recommended_route: ""
  why_recommended: []
  why_not_other_routes: {}
  route_risks: []
  route_decision_pending: true
admission_decision:
  verdict: NEEDS_REFRAME
  why: []
  kill_criteria: []
  required_reframe_actions: []
```

The contract should forbid unknown top-level fields. Runtime validators should require:

- non-empty `raw_idea`
- non-empty `observation`
- non-empty `primary_hypothesis`
- non-empty `counter_hypothesis`
- non-empty `scope.market`
- non-empty `scope.universe`
- non-empty `scope.data_source`
- non-empty `scope.bar_size`
- non-empty `scope.target_task`
- route assessment complete before `ACCEPT_FOR_MANDATE`
- at least one kill criterion before `ACCEPT_FOR_MANDATE`

## Freeze Draft

`mandate_freeze_draft.yaml` remains separate because it has a different lifecycle. Admission evidence is the agent's qualification record; freeze draft is the user-facing contract to be approved.

```text
01_mandate/author/draft/mandate_freeze_draft.yaml
```

It keeps the existing four groups:

- `research_intent`
- `scope_contract`
- `data_contract`
- `execution_contract`

The runtime may derive a first draft from `mandate_admission.yaml`, but confirmation belongs to the freeze draft. Once the user approves, the author program turns the draft into formal artifacts.

## Why Keep `draft/`

The `draft/` layer is intentional. It separates mutable pre-freeze material from frozen formal outputs.

Before user approval, admission and freeze data can still be refined. After approval, formal mandate outputs are generated and become the inputs for review and downstream stages. Mixing mutable admission records with formal artifacts would make it unclear which files are still negotiable and which files are frozen.

The boundary is:

```text
author/draft/   mutable, pre-freeze, user-confirmed before build
author/formal/  frozen, reviewable, downstream-consumable
```

## Runtime Behavior

### New lineage

When `qros-research-session` receives a raw idea and no lineage exists:

1. Derive or assign a lineage id.
2. Create `01_mandate/author/draft/mandate_admission.yaml`.
3. Create `01_mandate/author/draft/mandate_freeze_draft.yaml`.
4. Report current stage as `mandate_admission`.
5. Ask only for missing admission facts that cannot be inferred safely.

### Admission completion

When `mandate_admission.yaml` has `admission_decision.verdict = ACCEPT_FOR_MANDATE`, runtime validates:

- route assessment
- qualification dimensions
- scope completeness
- kill criteria
- freeze draft readiness

If validation passes, the stage becomes `mandate_freeze_confirmation_pending`.

### User approval

When the user approves mandate freeze, runtime writes:

```text
01_mandate/author/draft/mandate_transition_approval.yaml
```

Then `detect_session_stage()` returns `mandate_author`.

### Author build

The mandate stage program consumes:

- `01_mandate/author/draft/mandate_admission.yaml`
- `01_mandate/author/draft/mandate_freeze_draft.yaml`
- `01_mandate/author/draft/mandate_transition_approval.yaml`

It writes the existing formal artifact set.

### Review entry

`mandate_review_confirmation_pending` remains explicit. Review still requires user approval and independent reviewer isolation.

## Breaking Change Policy

No automatic compatibility layer is required.

The implementation should remove `idea_intake` from the ordinary session stage machine. Old in-progress lineages that depend on `00_idea_intake/` may fail with a clear message. The message should tell the operator that the lineage uses the retired first-stage model and must be completed with the previous runtime or restarted under the merged mandate model.

The repo may keep legacy contracts or skills as archived reference, but they must not appear as normal recommended next skills.

## Documentation Impact

Update active user docs to say:

- QROS starts with `mandate`, not `idea_intake`.
- The old intake responsibilities now live in `mandate_admission`.
- The first visible user approval freezes the mandate.
- `00_idea_intake/` is not created for new lineages.
- `qros-idea-intake-author` is no longer a normal-path skill.

Docs that currently explain `idea_intake -> mandate` must be rewritten or archived.

## Test Plan

Focused tests:

- `slugify_idea` accepts non-English raw ideas or uses a fallback lineage id instead of failing on Chinese-only input.
- A new raw idea creates `01_mandate/author/draft/mandate_admission.yaml`.
- New lineage initial stage is `mandate_admission`.
- Missing admission fields keep the stage in `mandate_admission`.
- `ACCEPT_FOR_MANDATE` with incomplete route assessment does not advance.
- `ACCEPT_FOR_MANDATE` with complete admission evidence and freeze draft advances to `mandate_freeze_confirmation_pending`.
- Confirming mandate freeze writes `mandate_transition_approval.yaml` under `01_mandate/author/draft/`.
- Confirmed freeze advances to `mandate_author`.
- `mandate_author` consumes the new draft paths and still writes the existing formal artifacts.
- Normal-path runtime no longer recommends `qros-idea-intake-author`.

Workflow tests:

- Update `tests/session/test_research_session_runtime.py` stage detection expectations.
- Update `tests/session/test_run_research_session_script.py` CLI output expectations.
- Update artifact contract tests for the new `mandate_admission.yaml` contract.
- Update anti-drift snapshot expectations for canonical first-stage naming.

Required verification:

```bash
python -m pytest <focused tests>
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

`full-smoke` is required because this changes stage flow, gate semantics, canonical stage naming, and first-stage artifact contracts.

## Open Risks

- Removing compatibility simplifies the runtime but forces old unfinished lineages to restart or stay on an older runtime.
- Compressing admission into one YAML file improves maintainability but makes that file semantically dense. The schema and docs must be precise enough that reviewers can still audit each admission decision.
- Keeping formal mandate artifacts unchanged reduces downstream blast radius, but it leaves file-count pressure in `author/formal/` for a future design.

## Non-Goals

- Do not redesign post-mandate TSS or CSF stages in this change.
- Do not merge `author/formal/*` into a single mandate artifact in this change.
- Do not change reviewer isolation or review cycle semantics.
- Do not add automatic migration for old `00_idea_intake/` lineages.
