# QROS Review Boundary Hardening Design

## Context

QROS review currently has the right high-level shape: a launcher prepares an
adversarial review cycle, a reviewer writes findings, and `qros-review` closes
the stage through deterministic checks. A real Claude Code session exposed four
remaining failure modes:

1. The launcher/main conversation can still write `reviewer_findings.raw.yaml`
   and effectively impersonate the reviewer.
2. A reviewer can inspect the wrong repository root, for example the QROS
   governance repository instead of the active research repository.
3. A hard metric gate can be described as a reservation even though the runtime
   must treat it as blocking.
4. `qros-review` can return a final non-advancing verdict while an intermediate
   review result projection still looks pass-like.

These are review credibility issues. The fix should be fail-closed: an invalid
review cycle must not produce closure artifacts, except when deterministic hard
gates legitimately close the stage as a non-advancing verdict such as `RETRY`.

## Goal

Harden the review boundary so that:

- launcher, reviewer, and closer responsibilities are machine-enforced
- reviewer output is bound to the intended active research repo and stage
- deterministic hard gates cannot be downgraded into reservations
- stdout, runtime state, canonical review result, and closure artifacts agree

## Non-Goals

- Do not introduce a new review orchestration command.
- Do not remove `qros-review-cycle prepare`, `qros-review`, or the existing
  write-scope audit.
- Do not add a general identity service. The first hardening pass should use
  existing launcher/reviewer session ids, reviewer agent ids, and canonical
  path bindings.
- Do not allow failure-class or hard-gate outcomes to continue ordinary
  next-stage progression.

## Architecture

The review flow is split into three roles with non-overlapping authority.

### Launcher

`qros-review-cycle prepare` remains the launcher-only entrypoint. It may write:

- `review/request/adversarial_review_request.yaml`
- `review/request/reviewer_receipt.yaml`
- `review/request/reviewer_handoff_manifest.yaml`
- `review/request/reviewer_write_scope_baseline.yaml`
- `review/review_cycle_trace.jsonl`

It must not write reviewer findings. The handoff prompt must explicitly state
that the launcher/main conversation is not the reviewer and must not write
`review/result/reviewer_findings.raw.yaml`.

### Reviewer

The reviewer lane may read only the request scope and formal stage artifacts
listed by the handoff. It may write only:

- `review/result/reviewer_findings.raw.yaml`

The raw findings file becomes the reviewer attestation. It must include the
reviewer's session id, reviewer agent id, and canonical paths inspected.

### Closer

`qros-review` remains the only deterministic closer. It must:

1. load the active request, receipt, raw reviewer findings, and protected state
2. validate reviewer identity and path bindings
3. run write-scope audit
4. run deterministic stage, contract, upstream binding, and metric gates
5. write a canonical merged `adversarial_review_result.yaml`
6. write closure artifacts only when the final verdict permits closure
7. update `review_runtime_state.yaml` with the same final verdict it reports

`adversarial_review_result.yaml` should represent the closer-merged canonical
result, not just the reviewer raw projection.

## Data Contract Changes

### Review Request Canonical Context

The request owns the canonical absolute paths for the active review cycle:

- `project_root`
- `lineage_root`
- `stage_dir`
- `author_formal_dir`
- `review_request_dir`
- `review_result_dir`

The existing relative paths remain useful for portable display and docs, but
the closer must validate against canonical absolute paths to prevent repo-root
drift.

The receipt continues to bind reviewer identity and must mirror the request
`project_root`, `lineage_root`, and `stage_dir` values exactly:

- `launcher_session_id`
- `launcher_thread_id`
- `requested_reviewer_session_id`
- `reviewer_agent_id`
- `handoff_manifest_digest`

### Raw Reviewer Findings

`reviewer_findings.raw.yaml` must include:

```yaml
review_cycle_id: "<cycle>"
reviewer_session_id: "<requested reviewer session id>"
reviewer_agent_id: "<reviewer agent id>"
reviewed_project_root: "<absolute active research repo root>"
reviewed_lineage_root: "<absolute lineage root>"
reviewed_stage_dir: "<absolute stage dir>"
hard_gate_findings_acknowledged: true
review_loop_outcome: CLOSURE_READY_PASS
blocking_findings: []
reservation_findings: []
info_findings: []
residual_risks: []
allowed_modifications: []
downstream_permissions: []
```

All finding fields remain lists of strings.

`hard_gate_findings_acknowledged` is not permission to override deterministic
gates. It only records that the reviewer checked the hard-gate section. The
closer still owns the final gate decision.

### Canonical Review Result

After `qros-review` runs, `review/result/adversarial_review_result.yaml` must
contain the closer-merged final state:

- final `review_loop_outcome`
- final `blocking_findings`
- final `reservation_findings`
- final `info_findings`
- deterministic gate findings
- reviewer identity fields
- canonical reviewed paths

The reviewer raw projection should be normalized into `review_findings.yaml`.
`adversarial_review_result.yaml` remains the closer-owned canonical result.

This file must not remain pass-like when `review_runtime_state.yaml` and stdout
report `RETRY`, `NO-GO`, or another non-advancing verdict.

## Fail-Closed Rules

### Reviewer Identity

`qros-review` must fail before closure with `REVIEWER_IDENTITY_COLLISION` when:

- raw findings omit `reviewer_session_id`
- raw `reviewer_session_id` differs from receipt
  `requested_reviewer_session_id`
- raw `reviewer_session_id` equals receipt `launcher_session_id`
- raw `reviewer_agent_id` differs from receipt `reviewer_agent_id`

These errors require a fresh prepare and an independent reviewer run. The raw
findings must not be reused.

### Repo Root Binding

`qros-review` must fail before closure with `REVIEW_CONTEXT_ROOT_MISMATCH`
when:

- raw `reviewed_project_root` differs from the canonical project root
- raw `reviewed_lineage_root` differs from the canonical lineage root
- raw `reviewed_stage_dir` differs from the canonical stage dir

This blocks reviewers that inspect the QROS governance repo or another lineage
instead of the active research repo stage.

### Hard Gate Downgrade

Hard metric gates are deterministic. For CSF examples:

- `csf_test_evidence`: `standalone_alpha` requires `mean_rank_ic > 0`
- `csf_backtest_ready`: selected backtest economics must pass net-return gates
- `csf_holdout_validation`: holdout direction and economics must pass

If deterministic metric gates fail, the final canonical result must include the
gate findings in `blocking_findings`.

If a reviewer writes a pass-like raw outcome while describing a failed hard gate
only in `reservation_findings` or `info_findings`, the closer must report
`HARD_GATE_DOWNGRADED` in the canonical result and close the stage as the
appropriate non-advancing verdict, normally `RETRY`. It must not allow
`PASS` or `CONDITIONAL PASS`.

This is different from identity/path errors. A hard gate failure is a valid
stage verdict and should be recorded as a non-advancing closure so the lineage
can move into failure handling.

### Projection Drift

`qros-review` must fail with `REVIEW_RESULT_PROJECTION_DRIFT` when:

- a stale `adversarial_review_result.yaml` exists for an active cycle without
  fresh raw findings
- the canonical review result, closure artifact, stdout, and runtime state would
  disagree

The recovery path is to archive/reset the stale cycle and prepare a fresh review.

## Handoff Prompt Changes

The reviewer handoff should include a launcher-only warning before the reviewer
instructions:

```text
Launcher boundary:
- The current/main conversation is the launcher, not the reviewer.
- Do not write reviewer_findings.raw.yaml from the launcher conversation.
- Send this handoff to an independent reviewer/subagent.
```

The reviewer instructions should include canonical absolute paths:

```text
Active research repo root: /abs/path/to/research-repo
Lineage root: /abs/path/to/research-repo/outputs/<lineage_id>
Stage dir: /abs/path/to/research-repo/outputs/<lineage_id>/<stage_dir>
```

The handoff should also state that the QROS governance repo is not the active
research repo unless these canonical paths point there.

## Error Handling

Errors should be stable and searchable:

| Error code | Meaning | Recovery |
| --- | --- | --- |
| `REVIEWER_IDENTITY_COLLISION` | reviewer and launcher identity/session boundary is invalid | prepare a fresh review and launch an independent reviewer |
| `REVIEW_CONTEXT_ROOT_MISMATCH` | reviewer inspected or attested to the wrong repo/stage path | rerun reviewer in the active research repo |
| `HARD_GATE_DOWNGRADED` | deterministic hard gate failed but reviewer tried to treat it as non-blocking | record non-advancing closure and enter failure handling |
| `REVIEW_RESULT_PROJECTION_DRIFT` | stale/canonical result projection conflicts with active cycle state | archive/reset stale cycle, then prepare a fresh review |

## Test Plan

Focused tests:

- raw findings missing `reviewer_session_id` fail closure
- raw reviewer session equals launcher session fails closure
- raw reviewer session differs from receipt fails closure
- raw reviewer agent id differs from receipt fails closure
- raw reviewed lineage root points to another repo and fails with
  `REVIEW_CONTEXT_ROOT_MISMATCH`
- raw reviewed stage dir points to another stage and fails
- reviewer handoff includes canonical absolute paths and the launcher boundary
- `csf_test_evidence` with `mean_rank_ic <= 0` plus pass-like reviewer outcome
  produces final `RETRY`
- the final canonical `adversarial_review_result.yaml` includes the hard gate in
  `blocking_findings`
- stdout, `adversarial_review_result.yaml`, `review_runtime_state.yaml`, and
  closure artifacts agree on the final verdict
- stale `adversarial_review_result.yaml` without fresh raw findings fails with
  `REVIEW_RESULT_PROJECTION_DRIFT`

Regression tests:

- normal PASS review still writes closure and emits `/clear` plus
  `recommended_skill`
- `FIX_REQUIRED` still avoids closure artifacts
- failure verdicts still route to `qros-stage-failure-handler`
- write-scope audit still blocks changes to `author/formal` and
  `review/request`

Required verification for implementation:

```bash
python -m pytest tests/review/test_adversarial_review_runtime.py tests/review/test_review_engine_csf_metric_gates.py tests/session/test_run_research_session_script.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Because this changes review closure semantics and failure routing, `full-smoke`
is mandatory.
