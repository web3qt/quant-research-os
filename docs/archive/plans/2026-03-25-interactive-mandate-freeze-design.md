# Interactive Mandate Freeze Design

**Date:** 2026-03-25
**Status:** Approved
**Scope:** `mandate_confirmation_pending -> 01_mandate`

## Goal

Make the `mandate` phase explicitly interactive.

The system should no longer auto-generate `01_mandate` after a small set of missing fields is filled. Instead, `qros-research-session` should drive a grouped freeze conversation so the researcher can see and approve what is being frozen before mandate artifacts are written.

## Problem

Current behavior is still too document-centric:

- `idea_intake` qualifies the direction
- `mandate_confirmation_pending` pauses the transition
- runtime can still generate `01_mandate` from a narrow set of fields

That leaves the researcher with an unclear experience:

- they do not know which mandate contents were frozen
- they cannot review grouped freeze decisions before artifact generation
- the current mandate outputs lag behind the full `Mandate` checklist in `docs/main-flow-sop/research_workflow_sop.md`

## Design Decision

Treat `mandate` as a grouped freeze session rather than a document-generation step.

After `GO_TO_MANDATE`, the system should:

1. enter `mandate_confirmation_pending`
2. collect mandate freeze content through grouped interaction
3. write an on-disk mandate freeze draft
4. require group-level confirmations
5. require a final explicit mandate approval
6. only then generate `01_mandate/*`

## Freeze Groups

The grouped freeze contract contains four sections:

1. `research_intent`
   - research question
   - primary hypothesis
   - counter-hypothesis
   - success criteria
   - failure criteria
   - excluded topics

2. `scope_contract`
   - market
   - universe
   - target task
   - excluded scope
   - budget days
   - max iterations

3. `data_contract`
   - data source
   - bar size
   - holding horizons
   - timestamp semantics
   - no-lookahead guardrail

4. `execution_contract`
   - time split policy
   - parameter boundary policy
   - artifact contract note
   - crowding / capacity review note

## Runtime State

Add a durable draft artifact under `00_idea_intake/`:

`mandate_freeze_draft.yaml`

This file stores:

- one draft payload per group
- one `confirmed` flag per group

The runtime should derive the next required interaction from this file rather than inferring progress from chat alone.

## Stage Semantics

`mandate_confirmation_pending` remains the only pre-mandate state, but its meaning becomes richer:

- admitted by intake
- mandate groups not fully frozen yet
- or final mandate approval still missing

The runtime should report:

- which group must be confirmed next
- whether all groups are complete and only final approval is missing

## Artifact Generation Rule

`build_mandate_from_intake()` should no longer treat scope files as sufficient mandate inputs.

It should require:

- `idea_gate_decision.yaml.verdict == GO_TO_MANDATE`
- `mandate_freeze_draft.yaml` exists
- all freeze groups are confirmed
- final mandate approval exists

The mandate outputs should be generated from the confirmed freeze draft, not from opportunistic defaults.

## User Experience

The mandate flow should feel like a research contract review:

1. explain the current group
2. ask 1-2 focused questions
3. echo the freeze draft for that group
4. ask whether that group is confirmed
5. move to the next group
6. produce one final mandate summary
7. ask whether to freeze the mandate

This ensures the researcher always knows what is being frozen and why.
