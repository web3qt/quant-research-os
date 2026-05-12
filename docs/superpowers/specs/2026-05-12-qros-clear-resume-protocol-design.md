# QROS Clear-Resume Protocol Design

## Context

QROS already has durable state snapshots and status projections, but the current
review handoff still leaves too much to chat memory. In Codex and Claude Code,
that is risky after a review passes:

- the user may keep typing in the same conversation context
- the model may continue from stale assumptions instead of re-reading disk truth
- the next stage handoff can be executed without an explicit boundary break

The workflow needs a hard reminder: after a pass-like review closure, the user
must clear the conversation before continuing into the next stage.

This design adds that boundary without turning QROS into a chat history system.
The only source of truth remains the repository state on disk.

## Decision

Introduce a shared clear/resume protocol with a dedicated `qros-resume`
entrypoint.

The protocol has three rules:

1. pass-like review closures that normally advance the lineage into
   `<stage>_review_complete` or the next-stage handoff must explicitly tell the
   user to `/clear` before starting the next stage
2. `qros-session` and `qros-progress` must surface the same reminder when they
   report a recoverable post-review state
3. `qros-resume` must re-read and re-validate disk state before it shows any
   continuation guidance

`qros-resume` is read-only by default. It is a recovery entrypoint, not a new
authoring lane and not a chat memory cache. Any optional `--continue` behavior
must first pass the same state checks and then delegate back to the existing
session engine.

## Goals

- Make `/clear` an explicit part of the post-review handoff.
- Keep the next-stage prompt grounded in disk truth, not conversation history.
- Reuse one canonical recovery summary across closer, status, and resume
  commands.
- Refuse resume if review state or author state has drifted.

## Non-Goals

- Do not persist chat history.
- Do not add a second workflow engine.
- Do not change review verdict semantics.
- Do not replace existing stage gates or failure handling.

## Proposed Shape

The protocol revolves around one derived resume capsule. It is computed from the
current lineage state and is never hand-authored.

The capsule should expose:

- `lineage_id`
- `current_stage`
- `gate_status`
- `blocking_reason_code`
- `next_action`
- `resume_hint`
- `clear_required`
- `clear_instruction`
- `recommended_command`

The important semantic change is `clear_required`:

- `true` when the lineage has just crossed a normal-advance review boundary and
  the user must clear the conversation before continuing
- `false` when the current state is blocked, in progress, or otherwise not a
  clear/resume boundary

The text fields should stay consistent:

- `clear_instruction` says to clear the conversation in the host client
- `resume_hint` explains why the boundary exists and what to do next
- `next_action` names the concrete next command after the clear

Example post-review wording:

```text
Review passed.
Clear the conversation in Codex or Claude Code before continuing.
Next action: run ./.qros/bin/qros-resume --lineage-id <lineage_id>
```

## Architecture

The resume protocol should reuse the existing runtime state sources instead of
creating a new persistent state file.

The shared capsule builder reads:

- current session stage and gate state
- review runtime state
- materialization digest ledger
- lineage lock ledger
- active review request / receipt / closure artifacts

From those inputs, it determines whether the lineage is safe to resume and what
the next command should be.

Consumers of the same capsule:

- `qros-review` closer output
- `qros-session`
- `qros-progress`
- `qros-resume`

This keeps the user-facing message consistent across the close boundary and the
first post-clear re-entry.

## Command Behavior

### `qros-review`

When a review closes with a normal-advance outcome, the closer must print the
clear boundary reminder and the canonical resume command.

The closer should not imply that the same conversation can be reused safely for
the next stage.

### `qros-session`

When `qros-session` reports a review-complete or next-stage handoff state after
normal advance, it must repeat the same clear boundary reminder.

This is the fallback for users who ignored the closer output and later ask for
status again in the same workspace.

### `qros-progress`

`qros-progress` must surface the same resume capsule fields, especially:

- whether a clear is required
- the exact next command
- the human-readable resume hint

It remains read-only.

### `qros-resume`

`qros-resume` is the post-clear recovery entrypoint.

Default behavior:

- validate current lineage state against the same freshness rules used by the
  status commands
- print the resume capsule
- do not mutate repository state

Optional `--continue` behavior:

- only allowed after validation succeeds
- re-enters the existing session engine instead of inventing a separate stage
  runner
- is intended for users who want a single explicit recovery command after
  `/clear`

## Validation and Stale Handling

The resume protocol must reject stale or drifting state instead of trying to
continue from it.

Required checks:

- the current review request, receipt, and closure state must agree on the same
  review cycle
- the current author digest must still match the review-bound digest
- protected review artifacts must not have unexpected drift
- the lineage lock ledger must still match the frozen facts it protects

Failure behavior:

- if the review is still in progress, do not ask the user to clear; say the
  review is still active
- if author outputs changed after review, refuse resume and point to
  `qros-review-cycle reset --archive-stale-cycle`
- if protected review state drift is detected, report the stable reason code and
  do not emit a misleading pass-like resume hint

## User Flow

1. The reviewer passes.
2. `qros-review` closes the review and prints the clear boundary reminder.
3. The user clears the conversation in Codex or Claude Code.
4. The user runs `qros-resume --lineage-id <lineage_id>`.
5. `qros-resume` re-validates state and prints the canonical next action.
6. The user continues into the next stage with the same repo truth, not stale
   chat memory.

## Testing

Add focused coverage for:

- pass-like review closure prints the `/clear` reminder and the resume command
- `qros-session` repeats the same reminder on a post-review status query
- `qros-progress` exposes the same clear-required capsule
- `qros-resume` prints the same canonical resume guidance
- stale author or review state refuses resume and points to reset
- `qros-resume --json` matches the text-mode capsule

## Notes on Scope

This design intentionally stops at recovery guidance.

It does not make QROS a chat transcript manager, and it does not allow the
runtime to trust conversation history as a substitute for disk state.
