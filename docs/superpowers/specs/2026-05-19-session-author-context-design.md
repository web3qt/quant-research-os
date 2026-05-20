# Session Author Context Design

## Purpose

`qros-research-session` currently mixes five different kinds of content in one long skill body:

- stage routing truth
- author-lane interaction discipline
- review-lane discipline
- failure routing
- user-facing guidance

Within the author lane, the current skill also duplicates stage-specific truth that already exists elsewhere:

- `Required Inputs`
- `Required Outputs`
- `Freeze Groups`
- gate discipline
- validator / preflight requirements
- placeholder / realism boundaries that are already runtime-enforced or contract-derived

This makes the main session skill too long, too repetitive, and too easy to drift from stage-specific author skills, runtime contracts, and validation behavior.

This design introduces `stage_author_context` as a runtime-generated context layer for the author lane and uses it to restructure `qros-research-session` into clearer internal orchestration layers.

## Scope

In scope:

- `qros-research-session` author-lane redesign
- route-neutral author stages:
  - `idea_intake`
  - `mandate`
- route-specific author stages:
  - `tss_*`
  - `csf_*`
- runtime-generated `stage_author_context.yaml`
- runtime-generated `stage_author_context.md`
- author-lane orchestration flow inside `qros-research-session`
- session-level reduction of duplicated author truth
- tests and docs needed to keep the new session behavior aligned

Out of scope:

- rewriting stage-specific author skills in this phase
- changing stage semantics
- changing artifact schemas
- changing stage gate meaning
- changing review-lane contract truth
- changing user-facing top-level entrypoints (`qros-research-session` remains the single ordinary author entry)

## Design Principles

1. `qros-research-session` remains the ordinary author orchestrator.
2. Stage-specific author truth should not live long-term inside the main session skill body.
3. Runtime-generated author context is the current-stage truth entrypoint for session author orchestration.
4. Author context can explain and sequence; it cannot redefine contracts.
5. The author lane should use one shared skeleton across `idea_intake`, `mandate`, `tss_*`, and `csf_*`.
6. Session refactoring should improve internal boundaries without changing the external entry model.

## Proposed Internal Session Layers

`qros-research-session` should be treated as one external skill with five internal orchestration layers.

### 1. Stage Routing

Responsibilities:

- resolve or create lineage
- detect `current_stage`
- resolve route (`time_series_signal` vs `cross_sectional_factor`)
- distinguish fresh start, resume, blocked, and terminal states

Not responsible for:

- stage-specific author interaction details
- review verdict interpretation details

### 2. Author Orchestration

Responsibilities:

- load `stage_author_context.*`
- determine the next unresolved author action
- drive freeze-group confirmation order
- decide when final author confirmation is allowed
- trigger build
- trigger validator / preflight
- route to author-fix, review-confirmation, or failure handling

Not responsible for:

- redefining stage artifact truth
- redefining stage gate semantics

### 3. Review Orchestration

Responsibilities:

- load `stage_contract_context.*`
- move from review confirmation into review lane
- handle reviewer handoff lifecycle
- interpret review verdicts
- route to next-stage confirmation or failure handling

This layer is complementary to the thin generated review skill work and should remain separate from author orchestration.

### 4. Failure Orchestration

Responsibilities:

- detect `requires_failure_handling`
- detect `FAILURE_DISPOSITION_REQUIRED`
- route to `qros-stage-failure-handler`
- route to `qros-lineage-change-control` or child lineage workflows

Not responsible for:

- normal author continuation
- review execution

### 5. Guidance Surfaces

Responsibilities:

- explain why the session is blocked
- explain the recommended next step
- explain which skill is active
- explain current missing prerequisites in user-facing language

This layer should describe runtime facts, not define them.

## Author Orchestration Skeleton

The author lane should use one shared skeleton across the full author mainline.

### Step 1: `enter`

- confirm current runtime state is author-eligible
- run `qros-check-stage-entry --lane author`
- confirm the current stage is one of the allowed author entry stages for the current context

### Step 2: `load context`

- load `stage_author_context.yaml`
- load `stage_author_context.md`
- treat them as the current-stage author truth entrypoint

### Step 3: `resolve next interaction`

- determine the next unresolved freeze group
- determine whether grouped summary should be shown now
- determine whether `确认全部` is allowed
- determine whether final author confirmation is allowed

### Step 4: `collect/confirm`

- gather missing information
- write or update draft state
- confirm one or more groups
- persist freeze confirmation state

### Step 5: `final author confirmation`

- only after all required groups are confirmed
- require explicit final author confirmation before build

### Step 6: `build`

- trigger lineage-local stage program
- generate formal artifacts in the active research repo

### Step 7: `validate/preflight`

- run stage validator
- run deterministic preflight when required
- stop immediately on validator/preflight failure

### Step 8: `route outcome`

- route to `*_author` / author-fix
- route to `*_review_confirmation_pending`
- route to failure handling

## Stage Author Context Shape

Author context should exist in two forms:

```text
<stage_dir>/author/context/stage_author_context.yaml
<stage_dir>/author/context/stage_author_context.md
```

The YAML file is the machine-readable source used by session/runtime/tests.
The Markdown file is the author-lane reading surface used by `qros-research-session`.

The Markdown file is not an alternate author skill and not a second truth source. Its source must be the YAML file.

## Stage Author Context Field Layers

`stage_author_context` should separate its fields into three classes.

### 1. Truth-Backed Fields

These must come from existing contracts/runtime truth and may not be freely invented in author context:

- `stage_id`
- `stage_name`
- `route`
- `required_inputs`
- `required_outputs`
- `artifact_contract`
- `allowed_runtime_stages`
- `validator_requirements`
- `preflight_requirements`
- `failure_route_conditions`

Primary sources:

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/artifacts/*.yaml`
- current stage runtime spec
- validator/preflight capabilities already present in runtime

### 2. Orchestration Fields

These are not contract truth; they define how the session author lane should run:

- `freeze_group_order`
- `supports_confirm_all`
- `requires_final_author_confirmation`
- `build_after_final_confirmation`
- `stop_if_validator_fails`
- `stop_if_preflight_fails`
- `author_fix_reentry_stage`
- `next_success_stage`
- `failure_handoff_skill`
- `interaction_mode`

These fields answer:

- what order the session should use
- when the session should stop
- when the session should ask for confirmation
- when the session should continue

### 3. Guidance Fields

These are session-facing prompts and reminders. They are not gate truth:

- `author_focus`
- `user_prompt_hints`
- `group_summary_template`
- `build_readiness_message`
- `common_pitfalls`
- `do_not_claim_complete_until`

These exist only to reduce author prose inside the session skill.

## Example Author Context Shape

```yaml
lineage_id: btc_leads_alts
stage_id: csf_data_ready
stage_name: CSF Data Ready
route: cross_sectional_factor
current_stage: csf_data_ready_confirmation_pending

truth:
  artifact_contract: contracts/artifacts/csf_data_ready_artifacts.yaml
  required_inputs:
    - 01_mandate/mandate.md
    - 01_mandate/research_scope.md
  required_outputs:
    - panel_manifest.json
    - asset_universe_membership.parquet
  validator_requirements:
    - qros-validate-stage --stage csf_data_ready
  preflight_requirements:
    - deterministic_preflight

orchestration:
  allowed_runtime_stages:
    - csf_data_ready_confirmation_pending
    - csf_data_ready_author
  freeze_group_order:
    - panel_contract
    - taxonomy_contract
    - eligibility_contract
    - shared_feature_base
    - delivery_contract
  supports_confirm_all: true
  requires_final_author_confirmation: true
  next_success_stage: csf_data_ready_review_confirmation_pending
  author_fix_reentry_stage: csf_data_ready_author
  failure_handoff_skill: qros-stage-failure-handler

guidance:
  author_focus:
    - Confirm freeze groups before build.
    - Do not treat placeholder outputs as complete.
    - Build must be followed by validate and preflight.
  do_not_claim_complete_until:
    - validator passes
    - preflight passes
```

## What Leaves `qros-research-session`

The main session skill should stop carrying long-form stage-specific author truth such as:

- complete required input lists for every stage
- complete required output lists for every stage
- complete freeze-group lists for every stage
- full stage-specific gate discipline sections
- repeated route-specific author prose for each stage

These should be loaded from `stage_author_context.*` when the runtime is actually in that stage.

## What Stays In `qros-research-session`

The main session skill should keep:

- external single-entry semantics
- routing rules
- author/review/failure/guidance layer boundaries
- shared author discipline
- shared review discipline
- shared failure-routing discipline
- current-stage guard behavior

In other words, the session skill remains the orchestrator shell, not the stage encyclopedia.

## Full-Mainline Coverage

This design covers the full author mainline:

- `idea_intake`
- `mandate`
- all `tss_*` author stages
- all `csf_*` author stages

The design does not assume route-specific stages are optional follow-ons. The author context system must be capable of representing the entire route-neutral and route-specific mainline in one consistent shape.

## Rollout Strategy

This redesign should be rolled out in four phases.

### Phase 1: Build Author Context Infrastructure

- define `stage_author_context` schema
- implement renderer for the full author mainline
- connect truth-backed fields to contracts/runtime
- encode orchestration and guidance fields in a stable form

At the end of this phase, the renderer should be able to emit context for:

- `idea_intake`
- `mandate`
- `tss_*`
- `csf_*`

### Phase 2: Convert `idea_intake` and `mandate`

- make `qros-research-session` author lane context-first for `idea_intake`
- make `qros-research-session` author lane context-first for `mandate`
- validate the shared author skeleton against the most interactive and route-neutral stages

This phase is the foundation. If the skeleton does not work for `idea_intake` and `mandate`, it will not be stable for route-specific stages.

### Phase 3: Convert Route-Specific Mainlines

Recommended order:

1. all `tss_*` author stages
2. all `csf_*` author stages

They should be converted as route groups, not as isolated stage-by-stage patches, to avoid a long-lived mixed system.

### Phase 4: Remove Old Session Prose

Only after the full author mainline is running context-first:

- remove stage-specific author prose from `qros-research-session`
- keep only shared orchestrator rules
- update docs/tests to treat author context as the current-stage truth entrypoint for session author orchestration

## Why `idea_intake` and `mandate` Come First

`idea_intake` and `mandate` should be converted before route-specific stages because they validate the shared skeleton across two different author styles:

- high-interaction discovery and clarification
- frozen contract authoring before route split

If the skeleton works there, it is credible for downstream route-specific author stages.

## Non-Goals

- This does not rewrite stage-specific author skills in the same phase.
- This does not change artifact schemas.
- This does not change route semantics.
- This does not merge author and review contexts into one file.
- This does not replace `qros-research-session` as the ordinary entrypoint.

## Success Criteria

- `qros-research-session` becomes materially shorter.
- Stage-specific author truth is no longer duplicated in the session skill body.
- The session author lane runs through a shared skeleton for `idea_intake`, `mandate`, `tss_*`, and `csf_*`.
- `stage_author_context.yaml` and `.md` exist as the current-stage truth entrypoint for author orchestration.
- `idea_intake` and `mandate` validate the new skeleton before route-specific rollout.
- TSS and CSF author stages are converted in route groups, not as isolated patches.
