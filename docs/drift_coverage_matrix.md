# QROS Skill Anti-Drift 覆盖矩阵

这份文档记录每类 drift 由哪条 test lane 负责，以及预期的 objective blocker 是什么。

| Drift 类型 | 主要 lane | 当前 owner 文件 | Objective blocker |
| --- | --- | --- | --- |
| Wrong routing | L2, L3 | `tests/test_research_session_runtime.py`, `tests/test_anti_drift.py` | same fixture resolves to different `route_skill` / `stage_id` |
| Artifact/schema drift | L0, L1 | `tests/test_schema_loaders.py`, `tests/test_generated_skills_fresh.py`, `tests/test_generator_inputs.py` | schema key loss, required output drift, or broken generator inputs |
| Semantic behavior drift | L3 | `tests/test_anti_drift.py` | canonical decision snapshot changes without approved re-baseline |
| Stage-gate verdict drift | L0, L2, L3 | `tests/test_schema_loaders.py`, `tests/test_research_session_runtime.py`, `tests/test_anti_drift.py` | same fixture yields different formal decision / permission semantics |
| Materially different conclusion over time | L2, L3 | `tests/test_anti_drift.py` | snapshot delta across baseline windows blocks promotion |

## Canonical Decision Snapshot 字段

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

## 当前缺口

1. 把 content-aware replay fixtures 扩展到当前 snapshot smoke tests 之外。
2. 在 nightly lane 增加更广的 semantic goldens。
3. 使用 `runtime/scripts/anti_drift_baseline.py` 与 `docs/anti_drift_baseline_promotion_protocol.md` 把 nightly diff reports 和 baseline promotion 操作化。
4. 把 CSF path coverage 提升到与主 route 对齐。
