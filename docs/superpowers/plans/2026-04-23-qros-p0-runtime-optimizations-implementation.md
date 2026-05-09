# QROS P0 Runtime Optimizations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not commit unless the user explicitly asks; this repository forbids unauthorized commits.

**Goal:** Add prebuild schema gates, digest caching, and a review-cycle prepare wrapper to reduce avoidable long QROS sessions.

**Architecture:** Extend existing runtime seams rather than inventing parallel flows. `lineage_program_runtime.py` owns prebuild gate execution, `review_runtime_state.py` owns digest ledger caching, and `review_session_runtime.py` plus a new script/bin wrapper owns review-cycle prepare output.

**Tech Stack:** Python standard library, YAML/JSON, existing QROS runtime helpers, pytest.

---

## Tasks

- [ ] Add failing tests for `prebuild_schema_gate` in `tests/runtime/test_lineage_program_runtime.py`.
- [ ] Implement optional `prebuild_schema_gate` parsing and validation in `runtime/tools/lineage_program_runtime.py`.
- [ ] Add failing tests for materialization digest cache in `tests/review/test_review_runtime_state.py`.
- [ ] Implement `materialization_digest_ledger.yaml` reuse in `runtime/tools/review_skillgen/review_runtime_state.py`.
- [ ] Add failing tests for `qros-review-cycle prepare` in `tests/review/test_review_cycle_prepare.py` and install/path tests.
- [ ] Implement `prepare_review_cycle_for_handoff()` in `runtime/tools/review_session_runtime.py`.
- [ ] Add `runtime/scripts/review_cycle.py` and `runtime/bin/qros-review-cycle`.
- [ ] Update review skills/docs to point at `./.qros/bin/qros-review-cycle prepare`.
- [ ] Run focused tests, smoke, and full-smoke.

## Self-Review

The plan covers all three requested P0s while keeping Python runtime separate from Codex-only `spawn_agent`. No placeholders are required for implementation because each task maps to a concrete file and test target.
