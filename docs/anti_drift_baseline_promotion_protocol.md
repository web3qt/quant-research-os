# QROS Anti-Drift Baseline Promotion Protocol

This protocol defines how semantic-golden and structured regression baselines are promoted without weakening the hard-fail posture.

## Scope

Applies to:

- canonical decision snapshot goldens under `tests/fixtures/anti_drift/`
- structured JSON regression payloads produced by anti-drift tools

## Core rule

No baseline may be overwritten silently.

Any changed baseline must go through:

1. explicit diff generation
2. human review of the semantic delta
3. explicit promotion with a label and source note

## Deterministic workflow

### 1. Generate current payloads

Examples:

```bash
python scripts/run_research_session.py --outputs-root /tmp/qros_snapshot_verify --raw-idea "BTC leads high-liquidity alts after shock events" --snapshot > /tmp/current_snapshot.json
```

### 2. Compare against blessed baseline

Use the baseline management tool:

```bash
python scripts/anti_drift_baseline.py compare --baseline tests/fixtures/anti_drift --current /tmp/current_snapshots
```

If `matches=false`, the current branch is blocked until the delta is either fixed or explicitly promoted.

For nightly human-readable summaries, render a markdown report:

```bash
python scripts/render_anti_drift_nightly_report.py \
  --baseline tests/fixtures/anti_drift \
  --current /tmp/current_snapshots \
  --output /tmp/anti_drift_nightly_report.md
```

### 3. Review the semantic delta

Required review questions:

- Did `route_skill` change?
- Did `stage_id` change?
- Did `formal_decision` change?
- Did `downstream_permissions` change?
- Did `blocking_reasons` change?
- Did the delta reflect an intentional contract change, not accidental drift?

### 4. Promote only intentional deltas

Promotion command:

```bash
python scripts/anti_drift_baseline.py promote \
  --current /tmp/current_snapshots \
  --baseline tests/fixtures/anti_drift \
  --label anti-drift-<date>-<reason> \
  --source-note "why this promotion is intentional"
```

This writes a `baseline_manifest.json` alongside the promoted payloads.

## Release posture

- PRs may introduce new goldens or changed baselines only with explicit review.
- Nightly regression compares current payloads against blessed baselines.
- Nightly regression should also emit a machine-readable gate artifact via `scripts/build_anti_drift_gate_summary.py`.
- Release assembly should consume the nightly gate artifact via `scripts/build_anti_drift_release_artifact.py`.
- The repository CI entrypoint for this flow is `.github/workflows/anti-drift.yml`.
- Release is blocked if:
  - current payloads differ from blessed baselines without explicit promotion
  - promotion manifest is missing for newly blessed payloads

## Required evidence for a valid promotion

- the diff output
- the reason for the semantic change
- the promotion label
- the promotion manifest
- updated tests still passing

## Current limitations

- This protocol currently governs JSON-based anti-drift payloads only.
- It does not yet automate approval routing or PR annotations.
- Wider replay coverage still needs to be expanded beyond the first semantic golden set.
