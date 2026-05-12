# QROS Post-Clear Skill Entry Design

## Context

QROS added a clear/resume protocol so PASS-like review boundaries tell Codex or
Claude Code to run `/clear` before continuing. The first implementation exposed
`./.qros/bin/qros-resume --lineage-id <lineage_id>` as the primary next action.

That is correct as a backend recovery primitive, but it is wrong as the user
experience. After `/clear`, users should re-enter the workflow through a QROS
skill, not through a shell command.

## Goal

After a normal PASS-like review closure, QROS should tell the user:

1. run `/clear`
2. in the new session, enter the next stage author skill

Example:

```text
This is a mandatory context boundary.

Run /clear in Codex or Claude Code.

Then in the new session enter:
qros-csf-data-ready-author
```

`qros-resume` remains available, but only as an agent/backend recovery and debug
command. It should not be the primary user-facing recommendation at a PASS-like
boundary.

## Non-Goals

- Do not introduce short slash aliases such as `/csf_data_ready`.
- Do not remove `qros-resume`; it is still useful for deterministic recovery.
- Do not let stage author skills become free-form jump points.
- Do not bypass next-stage confirmation, stage-entry guards, protected state
  checks, stale review detection, or lineage lock validation.

## User-Facing Entry

The review boundary should recommend the existing long QROS skill name for the
next author stage.

Examples:

| Closed review boundary | Recommended skill after `/clear` |
| --- | --- |
| `mandate` PASS, CSF route | `qros-csf-data-ready-author` |
| `mandate` PASS, TSS route | `qros-tss-data-ready-author` |
| `csf_data_ready` PASS | `qros-csf-signal-ready-author` |
| `csf_signal_ready` PASS | `qros-csf-train-freeze-author` |
| `csf_train_freeze` PASS | `qros-csf-test-evidence-author` |
| `csf_test_evidence` PASS | `qros-csf-backtest-ready-author` |
| `csf_backtest_ready` PASS | `qros-csf-holdout-validation-author` |
| `tss_data_ready` PASS | `qros-tss-signal-ready-author` |
| `tss_signal_ready` PASS | `qros-tss-train-freeze-author` |
| `tss_train_freeze` PASS | `qros-tss-test-evidence-author` |
| `tss_test_evidence` PASS | `qros-tss-backtest-ready-author` |
| `tss_backtest_ready` PASS | `qros-tss-holdout-validation-author` |

For terminal holdout review completion, no downstream author skill should be
recommended.

## Stage Skill Entry Semantics

The recommended author skill is a user-facing re-entry point. It is not a
permission to write artifacts blindly.

On post-clear entry, a stage author skill must first re-read disk truth and
validate the boundary:

1. Identify the active lineage from explicit input or repo-local runtime state.
2. Confirm the previous stage has a PASS-like review closure.
3. Confirm the requested author skill matches the next allowed stage.
4. Confirm protected review state and lineage locks are intact.
5. Detect whether the lineage is still at `*_next_stage_confirmation_pending`.
6. If next-stage handoff is still pending, route through the normal QROS
   confirmation path before authoring.
7. If state does not match, stop without writing author artifacts and direct the
   user back to `qros-research-session` / status recovery.

This preserves QROS's single source of truth: the new session is cleaner, but
disk state still decides what is allowed.

## Runtime Capsule Shape

The shared clear/resume capsule should stop using `recommended_command` as the
primary user action.

Preferred shape:

```json
{
  "clear_required": true,
  "clear_instruction": "Run /clear in Codex or Claude Code before continuing.",
  "recommended_skill": "qros-csf-data-ready-author",
  "recommended_skill_reason": "mandate PASS allows CSF data_ready authoring after next-stage handoff.",
  "backend_resume_command": "./.qros/bin/qros-resume --lineage-id cross_sectional_momentum_ranking"
}
```

Text renderers should show only:

- `clear_instruction`
- `recommended_skill`
- a short reason when useful

JSON may include `backend_resume_command` for agents and debugging, but user
documentation must not present it as the ordinary next step.

## Review Output Rules

For `PASS` and `CONDITIONAL PASS`:

- print the `/clear` instruction
- print the recommended next stage author skill
- do not print `qros-resume` as the recommended user action
- keep backend resume data available in JSON/status payloads

For `FIX_REQUIRED`:

- do not recommend a downstream author skill
- keep the user in the author-fix loop

For failure-class closures such as `RETRY`, `NO-GO`, or `CHILD LINEAGE`:

- do not recommend a downstream author skill
- route to failure handling as before

## Documentation Updates

Update:

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/qros-progress/SKILL.md`
- stage author skill entry discipline where needed

Docs should say that `qros-resume` is a backend/debug recovery command. The
ordinary user path after `/clear` is the recommended QROS skill.

## Test Coverage

Focused tests should lock:

- `qros-review` PASS output contains `/clear` and the next author skill.
- `qros-review` PASS output does not present `qros-resume` as the recommended
  user action.
- `qros-session` and `qros-progress` repeat the same recommendation at the same
  PASS-like boundary.
- JSON payload exposes `recommended_skill` and `backend_resume_command`.
- `FIX_REQUIRED` and failure-class verdicts do not expose a downstream author
  skill.
- Install/bootstrap tests still verify `qros-resume` exists as backend runtime.

Because this changes review/session handoff semantics, validation must include
focused tests, smoke, and full-smoke.
