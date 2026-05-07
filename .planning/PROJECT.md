# Quant Research OS

## What This Is

QROS is a local, agentic governance framework for quantitative research workflows. It provides contracts, runtime wrappers, stage-local program boundaries, adversarial review discipline, and tests that help active research repos move from idea intake through staged evidence without treating placeholders or chat claims as completed research.

This repository is the workflow, tool, contract, and documentation source of truth. Live strategy implementation and lineage outputs belong in consuming research repos.

## Core Value

QROS must enforce stage-gated research progression from disk evidence, canonical contracts, and independent review rather than from agent confidence or local improvisation.

## Current Milestone: v1.0 QROS Hardening

**Goal:** Close the governance and runtime gaps exposed by the `btc_alt` CSF session audit so installed QROS research repos cannot silently drift across source clones, CSF stage identities, review lanes, Python runtimes, or preflight gates.

**Target features:**
- Source-repo provenance guard for installed `.qros` wrappers and manifests.
- Canonical CSF stage id and lineage-local program path resolution.
- Independent reviewer enforcement and manual recovery downgrade semantics.
- Strict raw reviewer schema guidance and actionable closer errors.
- Stable Python interpreter selection for installed wrappers.
- Runtime-enforced post-mandate deterministic preflight gates.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet - this milestone establishes the first GSD-tracked hardening baseline.)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Installed QROS wrappers detect source-repo path, commit, and dirty-state drift before runtime actions can be trusted.
- [ ] CSF stage ids remain canonical as `csf_*` while lineage-local program directories keep established non-prefixed names such as `data_ready` and `signal_ready`.
- [ ] Review closure cannot produce promotable PASS from a local/manual recovery session unless that recovery mode is explicit and audited.
- [ ] Reviewer handoffs and closer validation prevent or clearly repair invalid raw outcomes such as `PASS`, `REJECT`, or structured finding objects.
- [ ] Installed wrappers use a stable Python interpreter compatible with QROS requirements instead of whichever `python3` appears first.
- [ ] Post-mandate review confirmation stages run deterministic preflight as a runtime gate, not merely as agent self-discipline.

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Rebuilding a specific live trading strategy - QROS governs workflow and artifacts; active research repos remain the source of lineage execution outputs.
- Broad `research_session.py` decomposition - important maintainability work, but this milestone targets concrete session-audit failures.
- New stage semantics beyond CSF identity/preflight hardening - avoid mixing remediation with feature expansion.
- External domain research - the failure evidence is local to QROS runtime, skills, and installed wrapper behavior.

## Context

The audited Codex session `019e00c7-0b34-7a62-914b-062f206506fb` progressed a CSF lineage through `csf_data_ready` and `csf_signal_ready`. It exposed several framework gaps:

- The consuming research repo was installed from `/Users/mac08/workspace/quant-research-os`, while the active governance repo under review is `/Users/mac08/workspace/web3qt/quant-research-os`.
- CSF session specs mapped canonical stages like `csf_data_ready` to legacy base ids like `data_ready`, which conflicted with review/preflight expectations.
- CSF program path resolution looked for `program/cross_sectional_factor/csf_data_ready`, while existing lineage-local programs use `program/cross_sectional_factor/data_ready`.
- A later `csf_signal_ready` review used `local-review-session-*` recovery rather than a true independent reviewer child, weakening adversarial review guarantees.
- Reviewer raw findings repeatedly used invalid outcomes or structured objects before manual schema repair.
- Installed wrappers selected `python3`, causing one environment to use Python 3.9 while QROS expects Python 3.11+ and CI uses Python 3.13.
- Post-mandate deterministic preflight remained partly dependent on agent behavior rather than runtime enforcement.

## Constraints

- **Repository boundary**: Do not store live strategy implementation in this repo - preserve QROS as workflow/governance infrastructure.
- **Compatibility**: Preserve established lineage-local CSF program directories (`data_ready`, `signal_ready`, etc.) while making canonical stage identity machine-readable.
- **Review integrity**: Independent adversarial review must stay materially separate from authoring; recovery paths must be visibly weaker than normal review.
- **Runtime portability**: Wrapper behavior must be deterministic across Codex/Claude hosts and Python environments.
- **Verification**: Changes touching research-session flow, review orchestration, CSF routing, or wrapper runtime require focused tests, smoke, and full-smoke.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep CSF artifact stages canonical as `csf_*` | Review, preflight, gates, and docs already treat CSF stages as route-specific contracts | - Pending |
| Keep CSF program directories non-prefixed | Existing lineage-local programs and user-facing paths already use `program/cross_sectional_factor/data_ready` style paths | - Pending |
| Treat local review session PASS as non-promotable unless explicitly recovered | Prevent silent self-review from masquerading as independent adversarial review | - Pending |
| Skip external research for this milestone | The scope is remediation from local audit evidence, not discovery of a new product feature | - Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-07 after starting milestone v1.0 QROS Hardening*
