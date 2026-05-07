# Roadmap: v1.0 QROS Hardening

**Created:** 2026-05-07
**Milestone goal:** Close the governance and runtime gaps exposed by the `btc_alt` CSF session audit.
**Phase numbering:** Starts at Phase 1 because no previous GSD milestone state exists in this repo.

## Summary

| Phase | Name | Goal | Requirements |
|-------|------|------|--------------|
| 1 | Install Provenance Guard | Prevent active research repos from silently using the wrong QROS source clone or stale runtime source. | PROV-01, PROV-02, PROV-03 |
| 2 | Canonical CSF Stage Identity | Align CSF stage ids, scaffold specs, and program directory resolution. | CSF-01, CSF-02, CSF-03 |
| 3 | Review Session Integrity | Prevent local/manual review recovery from producing an ordinary promotable PASS. | REV-01, REV-02 |
| 4 | Raw Review Schema Hardening | Make reviewer raw schema expectations and closer repair guidance deterministic. | REV-03, REV-04 |
| 5 | Python Wrapper Selection | Make installed wrappers use a stable, supported Python interpreter. | WRAP-01, WRAP-02 |
| 6 | Post-Mandate Preflight Gate | Promote post-mandate preflight from agent discipline to runtime gate. | PREF-01, PREF-02 |

## Phase Details

### Phase 1: Install Provenance Guard

**Goal:** Installed QROS runtimes detect and explain source repo path, commit, dirty-state, and interpreter drift before session/review commands rely on the wrong framework source.

**Requirements:** PROV-01, PROV-02, PROV-03

**Success criteria:**
1. `.qros/install-manifest.json` includes source repo path, source commit, install timestamp, and selected Python interpreter.
2. Runtime wrappers or shared wrapper helper detect source repo mismatch and emit actionable diagnostics.
3. Dirty-state or commit drift is surfaced before review/session actions can claim a clean framework basis.
4. Focused bootstrap/install tests cover the manifest and drift behavior.

**Validation:** focused bootstrap/install tests + smoke + full-smoke.

### Phase 2: Canonical CSF Stage Identity

**Goal:** Keep canonical CSF stage ids as `csf_*` while preserving established lineage-local program directories.

**Requirements:** CSF-01, CSF-02, CSF-03

**Success criteria:**
1. `SESSION_STAGE_PROGRAM_SPECS` and `STAGE_PROGRAM_SPECS` use canonical `csf_*` ids for all CSF stages.
2. `stage_program_relative_dir()` maps canonical CSF ids to non-prefixed program directories such as `data_ready`.
3. Review/preflight program identity checks accept canonical CSF identity and established CSF program paths.
4. Focused tests fail on the old `csf_data_ready -> data_ready` identity drift.

**Validation:** focused runtime/review tests + smoke + full-smoke.

### Phase 3: Review Session Integrity

**Goal:** Make independent adversarial review materially enforceable and make manual recovery visibly non-equivalent.

**Requirements:** REV-01, REV-02

**Success criteria:**
1. Closure logic refuses promotable PASS from `local-review-session-*` unless an explicit manual recovery contract is present.
2. Review receipts and closure artifacts record reviewer execution mode clearly.
3. Skills/docs describe manual recovery as downgraded governance, not a replacement for independent reviewer spawn.
4. Tests cover normal reviewer PASS, local recovery block, and explicit recovery metadata.

**Validation:** focused review runtime tests + smoke + full-smoke.

### Phase 4: Raw Review Schema Hardening

**Goal:** Prevent invalid reviewer raw files from requiring improvised human/agent schema repair.

**Requirements:** REV-03, REV-04

**Success criteria:**
1. Reviewer handoff manifests list the exact allowed raw `review_loop_outcome` values.
2. Stage review skills instruct flat `list[string]` findings and reject structured finding objects.
3. Deterministic closer error messages identify invalid enum values and expected replacements where unambiguous.
4. Tests cover invalid `PASS`, invalid `REJECT`, and structured finding object errors.

**Validation:** focused review result writer/protocol tests + smoke + full-smoke.

### Phase 5: Python Wrapper Selection

**Goal:** Ensure installed `.qros/bin/*` wrappers select a supported, stable Python interpreter.

**Requirements:** WRAP-01, WRAP-02

**Success criteria:**
1. Install records the Python interpreter used to install/copy runtime assets.
2. Wrappers prefer that interpreter when it exists and satisfies Python >=3.11.
3. Fallback interpreter probing rejects unsupported versions with clear diagnostics.
4. Tests simulate incompatible `python3` and verify wrappers do not silently use it.

**Validation:** focused bootstrap/wrapper tests + smoke + full-smoke.

### Phase 6: Post-Mandate Preflight Gate

**Goal:** Require deterministic preflight before launching review for every post-mandate review confirmation stage.

**Requirements:** PREF-01, PREF-02

**Success criteria:**
1. Runtime invokes review preflight for TSS and CSF post-mandate `*_review_confirmation_pending` stages.
2. Preflight failure blocks review progression with a machine-readable blocking reason.
3. Existing tests that locked "no post-mandate preflight" are replaced with tests requiring preflight.
4. Stage-specific skills and docs stop describing post-mandate preflight as merely self-discipline.

**Validation:** focused session/review tests + smoke + full-smoke.

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROV-01 | Phase 1 | Pending |
| PROV-02 | Phase 1 | Pending |
| PROV-03 | Phase 1 | Pending |
| CSF-01 | Phase 2 | Pending |
| CSF-02 | Phase 2 | Pending |
| CSF-03 | Phase 2 | Pending |
| REV-01 | Phase 3 | Pending |
| REV-02 | Phase 3 | Pending |
| REV-03 | Phase 4 | Pending |
| REV-04 | Phase 4 | Pending |
| WRAP-01 | Phase 5 | Pending |
| WRAP-02 | Phase 5 | Pending |
| PREF-01 | Phase 6 | Pending |
| PREF-02 | Phase 6 | Pending |

**Coverage:** 14/14 requirements mapped.

## Next Step

Start with Phase 1 because source provenance drift can invalidate every later runtime/review result.

`$gsd-plan-phase 1`
