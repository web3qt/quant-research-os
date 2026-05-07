---
phase: 03
status: researched
created: 2026-05-07
---

# Phase 03 Research: Review Session Integrity

## Question

What needs to be true before planning Phase 3 so local/manual review recovery cannot produce an ordinary promotable PASS?

## Current Runtime Shape

The active review proof chain is centered in:

- `runtime/tools/review_session_runtime.py`
- `runtime/tools/review_skillgen/adversarial_review_contract.py`
- `runtime/tools/review_skillgen/protocol_validator.py`
- `runtime/tools/review_skillgen/review_result_writer.py`
- `runtime/tools/review_skillgen/review_engine.py`
- `runtime/tools/review_skillgen/closure_writer.py`

The normal stage review path now uses `start_review_cycle()` / `qros-review-cycle prepare`, which writes `review/request/reviewer_receipt.yaml` with:

- `execution_mode: spawned_agent`
- `reviewer_invocation_kind: codex_spawn_agent` or `claude_plugin_agent`
- `context_isolation_policy`
- `handoff_delivery_method`
- `reviewer_agent_id`

The recovery path still uses `start_review_session()` / `qros-start-review`, which writes:

- `execution_mode: review_session`
- `reviewer_agent_id == reviewer_session_id`

`run_stage_review()` currently accepts both execution modes as equivalent if the receipt/result fields match. That means a `review_session` receipt can still produce `CLOSURE_READY_PASS` -> `final_verdict: PASS` and write ordinary closure artifacts.

## Risk

The current proof chain distinguishes `execution_mode`, but it does not apply governance semantics to that distinction. As a result, local recovery can be technically well-formed while still bypassing the independent reviewer child requirement.

This is exactly the Phase 3 gap:

- `spawned_agent` should be the ordinary independent-review path.
- `review_session` should be treated as manual recovery / standalone fallback.
- Manual recovery may be useful for diagnostics or emergency closure replay, but it must not look equivalent to independent adversarial review.

## Existing Tests And Seams

Relevant focused tests already exist:

- `tests/review/test_start_review_session.py`
  - asserts `start_review_session()` writes `execution_mode: review_session`
  - currently asserts `qros-review` can close PASS from review session receipt
- `tests/review/test_adversarial_review_runtime.py`
  - covers receipt/result proof chain failures, route parity, stale cycles, write-scope audit, and closure behavior
- `tests/review/test_review_engine.py`
  - covers successful `spawned_agent` PASS and closure artifact behavior
- `tests/review/test_run_stage_review_script.py`
  - covers CLI close path
- `tests/review/test_review_result_writer.py`
  - covers raw findings normalization into canonical result

The smallest implementation seam is after `load_and_validate_protocol()` in `run_stage_review()`, because at that point runtime has:

- active request
- receipt
- canonical review result
- reviewer write-scope audit
- resolved `review_loop_outcome`

That is the right place to enforce whether the current execution mode is allowed to produce promotable closure.

## Proposed Contract

Add a deterministic manual recovery contract:

`review/request/manual_recovery_contract.yaml`

Required fields:

- `review_cycle_id`
- `execution_mode: review_session`
- `manual_recovery_authorized: true`
- `authorized_by`
- `authorized_at`
- `recovery_reason`
- `independent_review_unavailable_reason`
- `governance_downgrade_acknowledged: true`
- `allowed_review_loop_outcomes`

Governance rules:

1. `execution_mode: spawned_agent` can produce normal closure-ready PASS without manual recovery metadata.
2. `execution_mode: review_session` with `CLOSURE_READY_PASS` or `CLOSURE_READY_CONDITIONAL_PASS` must fail unless `manual_recovery_contract.yaml` validates and lists that outcome.
3. `execution_mode: review_session` with `FIX_REQUIRED` can remain allowed without a recovery contract because it does not advance the lineage.
4. Closure artifacts should expose a top-level `review_execution_governance` block so downstream readers do not have to dig into nested receipt/result payloads.

Suggested `review_execution_governance` fields:

- `execution_mode`
- `reviewer_agent_id`
- `manual_recovery_required`
- `manual_recovery_authorized`
- `manual_recovery_contract_path`
- `pass_promotion_allowed`
- `governance_status`

## Docs And Skill Surface

Active stage review skills already require `spawn_agent` and reference the shared review protocol. The docs gap is that `review_session` is still described as a supported execution mode rather than as a downgraded recovery mode.

Docs and skill surfaces to update:

- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/qros-research-session-usage.md`
- `docs/guides/codex-stage-review-skill-usage.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/using-qros/SKILL.md`
- `templates/skills/review-stage/SKILL.md.tmpl`
- `tests/review/test_adversarial_review_skill_generation.py`

## Validation Architecture

Blocking dimensions:

1. **Normal independent reviewer pass:** `spawned_agent` PASS still closes normally and records `review_execution_governance.execution_mode == spawned_agent`.
2. **Manual recovery block:** `review_session` + `CLOSURE_READY_PASS` without `manual_recovery_contract.yaml` fails before closure artifacts are written.
3. **Explicit recovery metadata:** `review_session` + valid `manual_recovery_contract.yaml` can close PASS, but closure artifacts expose `manual_recovery_authorized: true` and `governance_status: manual_recovery_authorized`.
4. **Non-promoting recovery remains usable:** `review_session` + `FIX_REQUIRED` remains able to route back to author without writing closure artifacts.
5. **Docs/skills truth:** shared protocol and generated review skill template describe `review_session` as manual recovery, not ordinary independent review.

Focused commands:

```bash
python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_engine.py tests/review/test_run_stage_review_script.py tests/review/test_review_result_writer.py
python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/docs/test_install_docs.py
```

Broader required verification:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```
