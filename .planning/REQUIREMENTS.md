# Requirements: Quant Research OS

**Defined:** 2026-05-07
**Core Value:** QROS must enforce stage-gated research progression from disk evidence, canonical contracts, and independent review rather than from agent confidence or local improvisation.

## v1.0 Requirements

### Installation Provenance

- [x] **PROV-01**: Maintainer can see the source repository path, source commit, install timestamp, and Python interpreter recorded in `.qros/install-manifest.json`.
- [x] **PROV-02**: Installed wrappers warn or fail when the consuming research repo is bound to a different QROS source repo than the active governance repo expected by the current session.
- [x] **PROV-03**: Installed wrappers detect source dirty-state or commit drift and present an actionable recovery path before review/session commands rely on stale runtime code.
- [ ] **PROV-04**: Installed `.qros/install-manifest.json` verifies that the source repo path matches the current user-selected QROS checkout before session/review commands trust installed assets.

### CSF Stage Identity

- [x] **CSF-01**: Runtime session specs use canonical `csf_*` stage ids for all CSF stages while preserving route metadata.
- [x] **CSF-02**: CSF lineage-local program path resolution maps canonical `csf_*` stages to established non-prefixed directories such as `program/cross_sectional_factor/data_ready`.
- [x] **CSF-03**: Focused tests lock CSF stage id and program path behavior across `research_session`, `stage_program_scaffold`, and `lineage_program_runtime`.

### Runtime Entry Discipline

- [x] **ENTRY-01**: `qros-research-session` is the canonical normal entrypoint for stage progression from idea intake through holdout.
- [x] **ENTRY-02**: Stage-specific author skills refuse to continue when the runtime current stage does not match the requested author stage.
- [x] **ENTRY-03**: Stage-specific review skills refuse to launch review when the runtime current stage does not match the requested review stage.
- [x] **ENTRY-04**: Refusal messages route the user to the exact `qros-research-session` or recovery command needed to realign runtime state.

### Mandate Data Range Preflight

- [ ] **DATA-01**: Mandate freeze or review preflight scans declared source data and records observed min/max timestamps before accepting `time_split.json`.
- [ ] **DATA-02**: Train/test/backtest/holdout windows outside observed source data bounds are blocking findings, not reservations.
- [ ] **DATA-03**: The data-range preflight produces machine-readable evidence that downstream review can inspect.
- [ ] **DATA-04**: Tests cover an unavailable holdout window and require a deterministic blocker before downstream authoring.

### Review Integrity

- [ ] **REV-01**: Stage-specific review flow refuses to treat `local-review-session-*` or equivalent recovery sessions as independent reviewer PASS unless explicit manual recovery metadata is present.
- [ ] **REV-02**: Review receipts and closure artifacts distinguish normal independent reviewer execution from manual recovery execution.
- [ ] **REV-03**: Reviewer handoff material lists allowed raw `review_loop_outcome` values and requires flat `list[string]` findings.
- [ ] **REV-04**: Deterministic closer errors for invalid raw reviewer files include precise repair guidance without requiring ad hoc agent interpretation.

### Generated Review Artifacts

- [ ] **CLOS-01**: `review/request/*` artifacts are generated only by `qros-review-cycle prepare` or an equivalent runtime-owned command.
- [ ] **CLOS-02**: `review/result/adversarial_review_result.yaml` is generated only by `qros-review` from reviewer raw findings.
- [ ] **CLOS-03**: `review/closure/*` artifacts are generated only by `qros-review` after write-scope audit and result normalization.
- [ ] **CLOS-04**: Review request, result, and closure artifacts carry digests or writer metadata that detect launcher-lane hand edits before promotion.

### Severity Escalation

- [ ] **SEV-01**: High-severity reservations for factor direction reversal escalate to `CONDITIONAL_PASS` or `FIX_REQUIRED` according to stage gate policy.
- [ ] **SEV-02**: High-severity monotonicity failures cannot remain ordinary PASS without explicit conditional semantics and downstream restrictions.
- [ ] **SEV-03**: Concentrated backtest contribution or weak breadth/capacity findings above policy thresholds escalate beyond ordinary reservation.
- [ ] **SEV-04**: Insufficient holdout sample size or statistical power triggers conditional/failure routing rather than silent review PASS.

### Wrapper Runtime and Dependencies

- [ ] **WRAP-01**: Installed `.qros/bin/*` wrappers prefer the Python interpreter recorded at install time when it satisfies QROS version requirements.
- [ ] **WRAP-02**: Wrapper fallback selection rejects Python versions below the repository's supported minimum and reports the selected interpreter in failure diagnostics.
- [ ] **DEP-01**: QROS commands use a fixed venv or runtime dependency bundle rather than asking agents to install packages into the system environment.
- [ ] **DEP-02**: Runtime diagnostics reject or warn on ad hoc `--break-system-packages` dependency installation during normal QROS workflows.

### Review Preflight

- [ ] **PREF-01**: Post-mandate `*_review_confirmation_pending` stages run deterministic review preflight as a runtime gate before review launch.
- [ ] **PREF-02**: Tests are updated to require post-mandate preflight for TSS and CSF review confirmation stages, replacing the previous anti-expansion expectation.

### Failure Routing

- [ ] **FAIL-01**: Stage final verdict `FAIL` automatically routes to `qros-stage-failure-handler` instead of allowing normal downstream progression.
- [ ] **FAIL-02**: User-facing progress output clearly distinguishes review-process PASS from stage final verdict PASS/FAIL.
- [ ] **FAIL-03**: Holdout failure closure records the next valid actions: stop lineage, child lineage, or explicit failure triage.
- [ ] **FAIL-04**: Tests cover review PASS with stage final verdict FAIL and require failure-handler routing.

## Future Requirements

### Maintainability

- **MAINT-01**: `research_session.py` is decomposed into focused modules for transition detection, closure checks, approvals, and scaffolding.
- **MAINT-02**: CSF/TSS runtime duplication is reduced through route configuration abstractions.

### Review Automation

- **RAUTO-01**: A host-neutral reviewer launch adapter exposes the same independent-review guarantees in Codex and Claude Code.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Strategy research implementation | QROS is the governance/runtime framework, not the live lineage execution repo. |
| Broad session-state-machine refactor | Valuable but too large for this remediation milestone. |
| New factor or signal semantics | This milestone hardens gates, routing, review, wrappers, dependencies, and failure semantics only. |
| External ecosystem research | Audit evidence is already local and concrete. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROV-01 | Phase 1 | Complete |
| PROV-02 | Phase 1 | Complete |
| PROV-03 | Phase 1 | Complete |
| CSF-01 | Phase 2 | Complete |
| CSF-02 | Phase 2 | Complete |
| CSF-03 | Phase 2 | Complete |
| ENTRY-01 | Phase 3 | Complete |
| ENTRY-02 | Phase 3 | Complete |
| ENTRY-03 | Phase 3 | Complete |
| ENTRY-04 | Phase 3 | Complete |
| REV-01 | Phase 4 | Pending |
| REV-02 | Phase 4 | Pending |
| CLOS-01 | Phase 4 | Pending |
| CLOS-02 | Phase 4 | Pending |
| CLOS-03 | Phase 4 | Pending |
| CLOS-04 | Phase 4 | Pending |
| REV-03 | Phase 5 | Pending |
| REV-04 | Phase 5 | Pending |
| SEV-01 | Phase 5 | Pending |
| SEV-02 | Phase 5 | Pending |
| SEV-03 | Phase 5 | Pending |
| SEV-04 | Phase 5 | Pending |
| DATA-01 | Phase 6 | Pending |
| DATA-02 | Phase 6 | Pending |
| DATA-03 | Phase 6 | Pending |
| DATA-04 | Phase 6 | Pending |
| PREF-01 | Phase 6 | Pending |
| PREF-02 | Phase 6 | Pending |
| PROV-04 | Phase 7 | Pending |
| WRAP-01 | Phase 7 | Pending |
| WRAP-02 | Phase 7 | Pending |
| DEP-01 | Phase 7 | Pending |
| DEP-02 | Phase 7 | Pending |
| FAIL-01 | Phase 8 | Pending |
| FAIL-02 | Phase 8 | Pending |
| FAIL-03 | Phase 8 | Pending |
| FAIL-04 | Phase 8 | Pending |

**Coverage:**
- v1.0 requirements: 37 total
- Mapped to phases: 37
- Unmapped: 0

---
*Requirements defined: 2026-05-07*
*Last updated: 2026-05-07 after expanding milestone v1.0 from Claude Code session audit*
