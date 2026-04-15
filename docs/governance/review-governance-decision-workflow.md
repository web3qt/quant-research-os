# Review Governance Decision Workflow

This workflow governs how repeated review findings become governance candidates without silently mutating active policy.

## Core rule

Observations may be produced automatically. Institutional policy may not.

The review governance lane may:
- normalize repeated findings into `governance_signal.json`
- append signals to `governance/review_findings_ledger.jsonl`
- open or update `governance/candidates/*.yaml`

The lane may not:
- edit `contracts/stages/workflow_stage_gates.yaml`
- regenerate active skills/templates as policy
- bless regression baselines automatically

## Future-only boundary

Only review cycles at or after `contracts/governance/review_governance_policy.yaml: rollout_started_at` are counted.
Historical pre-rollout lineages remain historical evidence only; they are not backfilled into the governance ledger.

## Candidate classes and priority

Default review priority:
1. `hard_gate`
2. `template_constraint`
3. `regression_test`

Priority does not imply activation. It only orders governance review.

## Human decision artifact

A governance decision is recorded under `governance/decisions/*.md` with YAML front matter.

Example:

```md
---
decision_id: decision-2026-04-03-example
candidate_id: review-governance-abc123def4567890
decision_outcome: approved
planned_repo_change: contracts/stages/workflow_stage_gates.yaml + tests/...
---

Rationale for why this candidate should become planned repo work.
```

Allowed decisions:
- `approved`
- `rejected`
- `deferred`

## Agent-assisted decision recording

Users should not need to call a separate governance command.

When a candidate already exists and the human makes an explicit decision in the normal research conversation, the agent may:
- capture the human-confirmed decision into `governance/pending_decisions/<candidate_id>.yaml`
- write `governance/decisions/*.md`
- update `governance/candidates/*.yaml`

The agent may not invent the decision on its own.

## Runtime enforcement

Runtime still does not trust chat history directly.

If a human-confirmed governance decision has been captured into `governance/pending_decisions/*.yaml` but the formal decision artifact under `governance/decisions/*.md` has not yet been written, `qros-session` should block with:

- `stage_status = awaiting_governance_record`
- `blocking_reason_code = GOVERNANCE_DECISION_RECORD_REQUIRED`

That forces the agent to finish governance recording before ordinary progression continues.

## Important boundary

Even an `approved` governance decision does **not** activate policy.
It only authorizes follow-up repo work. Active gate/template/test changes still require normal reviewed commits and regression validation.
