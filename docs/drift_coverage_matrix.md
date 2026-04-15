# QROS Skill Anti-Drift Coverage Matrix

This document records which test lane owns each drift class and what objective blocker is expected.

| Drift class | Primary lane(s) | Current owner files | Objective blocker |
| --- | --- | --- | --- |
| Wrong routing | L2, L3 | `tests/test_research_session_runtime.py`, `tests/test_anti_drift.py` | same fixture resolves to different `route_skill` / `stage_id` |
| Artifact/schema drift | L0, L1 | `tests/test_schema_loaders.py`, `tests/test_generated_skills_fresh.py`, `tests/test_generator_inputs.py` | schema key loss, required output drift, or broken generator inputs |
| Semantic behavior drift | L3 | `tests/test_anti_drift.py` | canonical decision snapshot changes without approved re-baseline |
| Stage-gate verdict drift | L0, L2, L3 | `tests/test_schema_loaders.py`, `tests/test_research_session_runtime.py`, `tests/test_anti_drift.py` | same fixture yields different formal decision / permission semantics |
| Materially different conclusion over time | L2, L3 | `tests/test_anti_drift.py` | snapshot delta across baseline windows blocks promotion |

## Canonical decision snapshot fields

- `fixture_id`
- `input_digest`
- `snapshot_version`
- `schema_version`
- `route_skill`
- `stage_id`
- `session_stage`
- `formal_decision`
- `required_artifacts`
- `downstream_permissions`
- `blocking_reasons`
- `lineage_transition`
- `evidence_refs`
- `failure_class` (optional)
- `severity` (optional)

## Immediate next gaps

1. Expand content-aware replay fixtures beyond the current snapshot smoke tests.
2. Add broader semantic goldens to the nightly lane.
3. Operationalize nightly diff reports and baseline promotion using `scripts/anti_drift_baseline.py` plus `docs/anti_drift_baseline_promotion_protocol.md`.
4. Raise CSF path coverage to parity with the mainline route.
