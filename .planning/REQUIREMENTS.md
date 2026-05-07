# Requirements: Quant Research OS

**Defined:** 2026-05-07
**Core Value:** QROS must enforce stage-gated research progression from disk evidence, canonical contracts, and independent review rather than from agent confidence or local improvisation.

## v1.0 Requirements

### Installation Provenance

- [x] **PROV-01**: Maintainer can see the source repository path, source commit, install timestamp, and Python interpreter recorded in `.qros/install-manifest.json`.
- [x] **PROV-02**: Installed wrappers warn or fail when the consuming research repo is bound to a different QROS source repo than the active governance repo expected by the current session.
- [x] **PROV-03**: Installed wrappers detect source dirty-state or commit drift and present an actionable recovery path before review/session commands rely on stale runtime code.

### CSF Stage Identity

- [x] **CSF-01**: Runtime session specs use canonical `csf_*` stage ids for all CSF stages while preserving route metadata.
- [x] **CSF-02**: CSF lineage-local program path resolution maps canonical `csf_*` stages to established non-prefixed directories such as `program/cross_sectional_factor/data_ready`.
- [x] **CSF-03**: Focused tests lock CSF stage id and program path behavior across `research_session`, `stage_program_scaffold`, and `lineage_program_runtime`.

### Review Integrity

- [ ] **REV-01**: Stage-specific review flow refuses to treat `local-review-session-*` or equivalent recovery sessions as independent reviewer PASS unless explicit manual recovery metadata is present.
- [ ] **REV-02**: Review receipts and closure artifacts distinguish normal independent reviewer execution from manual recovery execution.
- [ ] **REV-03**: Reviewer handoff material lists allowed raw `review_loop_outcome` values and requires flat `list[string]` findings.
- [ ] **REV-04**: Deterministic closer errors for invalid raw reviewer files include precise repair guidance without requiring ad hoc agent interpretation.

### Wrapper Runtime

- [ ] **WRAP-01**: Installed `.qros/bin/*` wrappers prefer the Python interpreter recorded at install time when it satisfies QROS version requirements.
- [ ] **WRAP-02**: Wrapper fallback selection rejects Python versions below the repository's supported minimum and reports the selected interpreter in failure diagnostics.

### Review Preflight

- [ ] **PREF-01**: Post-mandate `*_review_confirmation_pending` stages run deterministic review preflight as a runtime gate before review launch.
- [ ] **PREF-02**: Tests are updated to require post-mandate preflight for TSS and CSF review confirmation stages, replacing the previous anti-expansion expectation.

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
| New factor or signal semantics | This milestone hardens routing, review, wrappers, and preflight gates only. |
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
| REV-01 | Phase 3 | Pending |
| REV-02 | Phase 3 | Pending |
| REV-03 | Phase 4 | Pending |
| REV-04 | Phase 4 | Pending |
| WRAP-01 | Phase 5 | Pending |
| WRAP-02 | Phase 5 | Pending |
| PREF-01 | Phase 6 | Pending |
| PREF-02 | Phase 6 | Pending |

**Coverage:**
- v1.0 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-05-07*
*Last updated: 2026-05-07 after starting milestone v1.0 QROS Hardening*
