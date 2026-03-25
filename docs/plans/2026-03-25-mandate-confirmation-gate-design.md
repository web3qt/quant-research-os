# Mandate Confirmation Gate Design

**Date:** 2026-03-25
**Status:** Approved
**Scope:** `idea_intake -> mandate` transition only

## Goal

Stop silent progression from `idea_intake` into `01_mandate/`.

An intake verdict of `GO_TO_MANDATE` should mean the idea is qualified to proceed, but it should not itself authorize mandate generation. The user must explicitly confirm the transition.

## Problem

The current `qros-research-session` contract collapses two different decisions into one:

- research judgment: the idea is qualified for mandate
- governance action: freeze the formal mandate artifacts now

That makes the workflow feel too automatic. A user can end up in `mandate` without a clear, explicit checkpoint showing why the transition happened.

## Decision

Introduce a hard confirmation gate between `idea_intake` and `mandate`.

When `idea_gate_decision.yaml.verdict == GO_TO_MANDATE`, the system must:

1. persist the intake artifacts and gate decision
2. stop in a new stage named `mandate_confirmation_pending`
3. present a structured confirmation summary
4. wait for an explicit approval command before writing `01_mandate/`

## Stage Semantics

The transition changes from:

`idea_intake -> mandate_author -> mandate_review`

to:

`idea_intake -> mandate_confirmation_pending -> mandate_author -> mandate_review`

Meaning of each relevant state:

- `idea_intake`
  intake artifacts are incomplete or the gate is not admitted
- `mandate_confirmation_pending`
  intake gate is admitted, but the user has not authorized mandate freeze
- `mandate_author`
  explicit approval exists and mandate artifacts may be generated

## Confirmation Summary

When the session enters `mandate_confirmation_pending`, the reported status must include:

- `lineage`
- `current_stage`
- `gate_verdict`
- `why_now`
- `open_risks`
- `next_action`

The summary should explain why the idea qualified, which material risks remain, and that the system is waiting for explicit approval rather than silently continuing.

## Approval Commands

Only explicit, low-ambiguity commands should be accepted:

- `CONFIRM_MANDATE <lineage_id>`
- `HOLD <lineage_id>`
- `REFRAME <lineage_id>`

Natural-language replies such as "continue", "okay", or "go ahead" must not trigger mandate generation.

## Approval Artifact

Approval must be durable across sessions. Store it at:

`outputs/<lineage>/00_idea_intake/mandate_transition_approval.yaml`

Minimum fields:

- `lineage_id`
- `decision`
- `approved_by`
- `approved_at`
- `source_gate_verdict`

This artifact allows the runtime to distinguish:

- admitted but not approved
- admitted and explicitly approved
- admitted but intentionally held or reframed

## Runtime Behavior

`run_research_session.py` should no longer auto-build `01_mandate/` immediately after `GO_TO_MANDATE`.

Instead:

- default session run stops at `mandate_confirmation_pending`
- a separate explicit confirmation action writes the approval artifact
- only a later session run with recorded approval may build `01_mandate/`

## User Experience Outcome

The user should always know:

- how the idea qualified
- that mandate has not been generated yet
- what exact command is required to authorize the transition

This restores visible workflow control without undoing the deterministic disk-backed session model.
