# CSF Signal Ready Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `csf_signal_ready` 从“能从 `csf_data_ready` 派生一组因子文件”升级为“factor artifact shape、因子字段来源、route inheritance、coverage、review preflight、skill 行为和 agent 行为都可确定性回归验证”的硬门禁阶段。

**Architecture:** 沿用刚完成的 `csf_data_ready` 思路：`contracts/artifacts/*` 定义 formal artifact shape，runtime 只按 contract scaffold/build，stage-specific semantic validator 校验因子语义和上游绑定，review preflight 在 reviewer lane 前 fail fast，skills/docs 只保留执行顺序和 validator discipline，agent eval 回归真实 agent 是否 skill-first / validator-first / no-placeholder。

**Tech Stack:** Python stdlib, PyYAML, PyArrow parquet, Polars parquet writer in stage runtime, pytest, existing QROS runtime helpers under `runtime/tools/`, existing review preflight, existing stage program boundary and agent behavior eval harness.

**Execution constraints:** 不得 `git commit`、`git push`、创建 PR 或改 `main`，除非用户在看到 diff 和验证结果后明确确认。计划文档位于 `docs/superpowers/plans/`，当前该目录被 `.gitignore` 忽略。

---

## 当前基线判断

`csf_signal_ready` 已经有运行时和部分 review gate：

- `runtime/tools/csf_signal_ready_runtime.py` 能从 `02_csf_data_ready/author/formal` 生成 `03_csf_signal_ready/author/formal`。
- `contracts/stages/workflow_stage_gates.yaml` 已有 `CSF-SIGNAL-STRUCT-*` 结构门禁，包括 `factor_direction`、`panel_primary_key`、`final_score_field`、`score_combination_formula`、`factor_panel` 非空和 `(date, asset)` 唯一。
- `runtime/tools/review_skillgen/upstream_binding_validator.py` 已能校验 `route_inheritance_contract.yaml` 与 mandate `research_route.yaml` 的核心字段一致。
- review tests 已覆盖部分坏路径：缺失 `factor_direction`、缺失或漂移 `route_inheritance_contract.yaml`、`factor_panel` duplicate key。

但当前仍有系统性缺口：

- 没有 `contracts/artifacts/csf_signal_ready_artifacts.yaml`，所以 formal artifact shape 没有机器真值层。
- `artifact_contract_runtime.py` 尚未注册 `csf_signal_ready`，`qros-validate-stage --stage csf_signal_ready` 不可用。
- `build_csf_signal_ready_from_data_ready()` 生成后没有自动 artifact contract validation 和 stage-specific semantic validation。
- `review_preflight.py` 目前只对 `csf_data_ready` 接入 artifact contract 和 semantic validator，`csf_signal_ready` 还没有。
- author skill 的 Required Outputs / Freeze Groups 与 runtime 真实 shape 不一致：skill 里仍出现 `factor_coverage.parquet`、`signal_gate_decision.md`、`factor_role_contract`、`factor_structure_contract`、`neutralization_policy`，而 runtime 实际是 `factor_coverage_report.parquet`、`csf_signal_ready_gate_decision.md`、`panel_contract`、`factor_expression`、`context_contract`。
- workflow gate required outputs 没完整列出 runtime 真实生成且 review checklist 已引用的 `component_factor_manifest.yaml`、`factor_group_context.parquet`、`csf_signal_ready_gate_decision.md`。
- `raw_factor_fields` 目前只是字符串列表，没有强绑定到 `csf_data_ready` 共享特征底座字段，容易出现“字段名看似冻结、来源实际不明”。

---

## 完整终局

`csf_signal_ready` 最终必须满足这条链：

```text
csf_data_ready review closure PASS
→ mandate research_route.yaml.research_route == cross_sectional_factor
→ csf_signal_ready freeze groups confirmed
→ lineage-local stage program exists and is valid
→ formal artifacts materialized under 03_csf_signal_ready/author/formal
→ artifact contract validation passes
→ factor semantic validation passes
→ upstream csf_data_ready + mandate binding validation passes
→ review-entry preflight blocks invalid outputs before reviewer lane
→ skill/docs only point to contract/runtime/validator as truth
→ agent behavior eval covers skill-first, validator-first, and no-fake-completion behavior
```

最终能力分 6 层：

1. **Artifact Contract:** `contracts/artifacts/csf_signal_ready_artifacts.yaml` 定义 formal artifact 文件、字段、parquet 静态列、markdown section 和 unknown-field policy。
2. **Runtime Gate:** `build_csf_signal_ready_from_data_ready()` 生成后自动跑 shape validator；CLI wrapper 支持 `--stage csf_signal_ready`。
3. **Semantic Gate:** 校验因子方向、主键、final score 字段、输入字段来源、coverage、group context、deterministic combination 和无 train/test leakage。
4. **Upstream Binding:** 校验 mandate route inheritance、`csf_data_ready` panel/run manifest 绑定、taxonomy / eligibility / shared feature base 来源。
5. **Review Preflight:** 在 reviewer 子代理进入前执行 artifact + semantic + upstream binding，避免把 reviewer 当第一轮 completeness checker。
6. **Skill / Agent Eval:** skill 变薄，字段真值只来自 contract；agent eval 覆盖 naive prompt 和 explicit skill trigger 的真实行为。

---

## 分批路线图

| 批次 | 名称 | 能力增量 | 验证层级 |
| --- | --- | --- | --- |
| 1 | Artifact Contract + Runtime Shape Gate | 建立 `csf_signal_ready` formal artifact shape 真值层，build 后自动 validate，CLI 可独立校验 | focused tests + smoke；若同步 workflow gate required outputs，跑 full-smoke |
| 2 | Factor Semantic Validator | 校验 factor panel、manifest、coverage、field source、group context、no-leakage | focused tests + smoke |
| 3 | Upstream Binding + Review Preflight | 把 mandate / csf_data_ready 绑定和 semantic validator 接入 review preflight | focused tests + full-smoke |
| 4 | Skill / Docs Thin-Out | 修正 skill/docs 漂移，skill 不再定义字段真值，只要求 scaffold/build/validate/review | focused tests + smoke |
| 5 | Agent Behavior Eval | 覆盖 explicit skill-first、naive trigger、no placeholder、validator-before-review | focused tests + smoke |
| 6 | End-to-End CSF Route Smoke | 用现有 CSF pipeline/e2e 覆盖 `csf_data_ready → csf_signal_ready → csf_train_freeze` 兼容性 | focused pipeline tests + full-smoke |

每批完成后都要报告：

```text
完整 plan 进度：
- 已完成：<批次>
- 未完成：<剩余批次>
- 本批验证：<命令与结果>
- 是否跑 smoke / full-smoke：<原因>
- 下一步建议：<下一批>
```

---

## Batch 1: Artifact Contract + Runtime Shape Gate

### 目标

把 `csf_signal_ready` 的正式产物 shape 提升成机器合同，并让 runtime 生成后自动校验。该批只负责文件、字段、类型、静态 parquet 列和 markdown section，不做跨 artifact 语义推断。

### 文件范围

- Create: `contracts/artifacts/csf_signal_ready_artifacts.yaml`
- Create: `tests/contracts/test_csf_signal_ready_artifact_contract.py`
- Create: `tests/session/test_csf_signal_ready_artifact_shape.py`
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Modify: `runtime/tools/csf_signal_ready_runtime.py`
- Modify: `runtime/scripts/validate_stage_artifacts.py` only if CLI help/tests need stage-specific copy changes
- Modify: `tests/runtime/test_artifact_contract_runtime.py`
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
- Modify: `tests/runtime/test_csf_signal_ready_runtime.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`
- Modify: `contracts/stages/workflow_stage_gates.yaml` if required output list is synced in this batch
- Modify: `contracts/review/review_checklist_master.yaml` only if evidence names need sync

### Contract Shape

新增：

```text
contracts/artifacts/csf_signal_ready_artifacts.yaml
```

Stage identity:

```yaml
schema_id: csf-signal-ready-artifacts-v1
schema_version: v1
stage: csf_signal_ready
stage_dir: 03_csf_signal_ready/author/formal
unknown_machine_top_level_fields: forbid
```

Required artifacts:

```text
factor_panel.parquet
factor_manifest.yaml
component_factor_manifest.yaml
factor_coverage_report.parquet
factor_group_context.parquet
route_inheritance_contract.yaml
factor_contract.md
factor_field_dictionary.md
csf_signal_ready_gate_decision.md
run_manifest.json
artifact_catalog.md
field_dictionary.md
```

`factor_manifest.yaml` required fields:

```text
stage: enum[csf_signal_ready]
lineage_id: string
factor_id: string
factor_version: string
factor_direction: enum[high_better, low_better]
factor_structure: enum[single_factor, multi_factor_score]
panel_primary_key: list[string]
raw_factor_fields: list[string]
derived_factor_fields: list[string]
final_score_field: string
as_of_semantics: string
coverage_min_ratio: number
coverage_contract: string
missing_value_policy: string
input_field_map: list[map]
```

`component_factor_manifest.yaml` required fields:

```text
stage: enum[csf_signal_ready]
lineage_id: string
factor_structure: enum[single_factor, multi_factor_score]
component_factor_ids: list[string]
score_combination_formula: string
combination_policy: string
```

`route_inheritance_contract.yaml` required fields:

```text
source_route_artifact: string
source_route_digest_sha256: string
research_route: enum[cross_sectional_factor]
factor_role: enum[standalone_alpha, regime_filter, combo_filter]
factor_structure: enum[single_factor, multi_factor_score]
portfolio_expression: string
neutralization_policy: enum[none, market_beta_neutral, group_neutral]
target_strategy_reference: string
group_taxonomy_reference: string
target_strategy_reference_requirement_status: enum[not_required, required_satisfied]
group_taxonomy_reference_requirement_status: enum[not_required, required_satisfied]
inheritance_mode: enum[exact_copy]
```

`run_manifest.json` required fields:

```text
stage: enum[csf_signal_ready]
lineage_id: string
source_stage: enum[csf_data_ready]
research_route: enum[cross_sectional_factor]
factor_role: enum[standalone_alpha, regime_filter, combo_filter]
factor_structure: enum[single_factor, multi_factor_score]
portfolio_expression: string
neutralization_policy: enum[none, market_beta_neutral, group_neutral]
program_dir: string
program_entrypoint: string
program_execution_manifest: string
input_roots: list[string]
stage_outputs: list[string]
replay_command: string
```

Static parquet required columns:

```text
factor_panel.parquet: date, asset
factor_coverage_report.parquet: date, coverage_ratio, asset_count
factor_group_context.parquet: date, asset, group_context
```

`factor_panel.parquet` 的 `final_score_field` 是动态字段，不能靠静态 artifact contract 判断，放到 Batch 2 semantic validator 里判断。

Markdown sections:

```text
factor_contract.md: 因子合同
factor_field_dictionary.md: 因子字段字典
csf_signal_ready_gate_decision.md: CSF Signal Ready Gate Decision
artifact_catalog.md: 产物清单
field_dictionary.md: 字段字典
```

### Tasks

- [ ] **Task 1.1: 写 contract 失败测试**

Create `tests/contracts/test_csf_signal_ready_artifact_contract.py`.

Tests:

```text
test_csf_signal_ready_artifact_contract_exists_and_declares_stage_shape
test_csf_signal_ready_contract_locks_required_artifacts
test_csf_signal_ready_contract_locks_factor_manifest_fields
test_csf_signal_ready_contract_locks_component_manifest_fields
test_csf_signal_ready_contract_locks_route_inheritance_fields
test_csf_signal_ready_contract_locks_run_manifest_fields
test_csf_signal_ready_contract_locks_parquet_static_columns
test_csf_signal_ready_contract_field_paths_are_unique
```

Run:

```bash
python -m pytest tests/contracts/test_csf_signal_ready_artifact_contract.py -q
```

Expected RED:

```text
FAILED ... contracts/artifacts/csf_signal_ready_artifacts.yaml does not exist
```

- [ ] **Task 1.2: 新增 `csf_signal_ready_artifacts.yaml`**

Implement contract with existing validator-supported types:

```text
yaml
json
markdown
parquet
```

Run:

```bash
python -m pytest tests/contracts/test_csf_signal_ready_artifact_contract.py -q
```

Expected GREEN.

- [ ] **Task 1.3: 写 generic validator 注册测试**

Modify `tests/runtime/test_artifact_contract_runtime.py`.

Add tests:

```text
test_validate_stage_artifacts_accepts_valid_csf_signal_ready_shape
test_validate_stage_artifacts_reports_csf_signal_ready_missing_required_artifact
test_validate_stage_artifacts_reports_csf_signal_ready_factor_manifest_unknown_field
test_validate_stage_artifacts_reports_csf_signal_ready_factor_panel_missing_static_column
test_validate_stage_artifacts_reports_csf_signal_ready_empty_factor_panel
```

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py -q
```

Expected RED:

```text
unsupported artifact contract stage: csf_signal_ready
```

- [ ] **Task 1.4: 注册 `csf_signal_ready` artifact contract**

Modify `runtime/tools/artifact_contract_runtime.py`.

Required change:

```python
ARTIFACT_CONTRACTS["csf_signal_ready"] = ROOT / "contracts" / "artifacts" / "csf_signal_ready_artifacts.yaml"
```

No new dependency should be added. Existing `parquet`, `yaml`, `json`, `markdown`, `list[map]`, `number`, and unknown top-level logic should be reused.

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py -q
```

Expected GREEN.

- [ ] **Task 1.5: runtime build 后自动 shape validation**

Modify `runtime/tools/csf_signal_ready_runtime.py`.

Required changes:

```text
After writing formal artifacts:
- load_artifact_contract("csf_signal_ready")
- validate_stage_artifacts(stage_formal_dir, contract)
- raise ValueError with all validation errors if invalid
```

Also update runtime output shape to satisfy contract:

```text
factor_manifest.yaml 增加 stage, lineage_id, as_of_semantics, coverage_min_ratio, coverage_contract, missing_value_policy, input_field_map
component_factor_manifest.yaml 增加 stage, lineage_id, factor_structure, combination_policy
run_manifest.json stage_outputs 增加 component_factor_manifest.yaml, factor_group_context.parquet, csf_signal_ready_gate_decision.md
```

If `coverage_min_ratio` is not yet present in freeze draft, add it to `panel_contract.draft` with deterministic default `1.0` in tests and require user confirmation in real authoring.

Run:

```bash
python -m pytest tests/runtime/test_csf_signal_ready_runtime.py -q
```

Expected GREEN.

- [ ] **Task 1.6: CLI wrapper coverage**

Modify `tests/runtime/test_validate_stage_artifacts_script.py`.

Add tests:

```text
test_validate_stage_artifacts_script_accepts_csf_signal_ready
test_validate_stage_artifacts_script_rejects_invalid_csf_signal_ready
```

Run:

```bash
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py -q
```

Expected GREEN.

- [ ] **Task 1.7: shape snapshot / session artifact list**

Modify `tests/session/test_csf_signal_ready_artifact_shape.py` or add it if missing.

Tests:

```text
test_csf_signal_ready_scaffold_shape_is_stable
test_csf_signal_ready_build_shape_matches_contract
test_csf_signal_ready_yaml_key_shape_is_stable
```

Also update existing session expected output lists if workflow gate required outputs are synced.

Run:

```bash
python -m pytest tests/session/test_csf_signal_ready_artifact_shape.py tests/session/test_research_session_runtime.py -q
```

- [ ] **Task 1.8: sync workflow gate output names**

Modify `contracts/stages/workflow_stage_gates.yaml`.

Required alignment:

```text
required_outputs 增加 component_factor_manifest.yaml
required_outputs 增加 factor_group_context.parquet
required_outputs 增加 csf_signal_ready_gate_decision.md
machine_artifacts 增加 component_factor_manifest.yaml
machine_artifacts 增加 factor_group_context.parquet
human_artifacts 增加 csf_signal_ready_gate_decision.md
```

This touches stage gate semantics, so run full-smoke after focused tests:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

---

## Batch 2: Factor Semantic Validator

### 目标

建立 `csf_signal_ready` 专属语义 validator。Artifact contract 保证“有哪些字段”，semantic validator 保证“这些字段之间彼此一致、来自正确上游、不是 placeholder 或后验泄漏”。

### 文件范围

- Create: `runtime/tools/csf_signal_ready_contract_runtime.py`
- Create: `tests/runtime/test_csf_signal_ready_semantic_validation.py`
- Modify: `runtime/tools/csf_signal_ready_runtime.py`
- Modify: `tests/runtime/test_csf_signal_ready_runtime.py`
- Modify: `tests/helpers/stage_fixtures.py`
- Modify: `tests/pipeline/test_csf_pipeline.py`

### Semantic Checks

`validate_csf_signal_ready_semantics(author_formal_dir: Path, lineage_root: Path | None = None)` should return a result object with `errors: list[str]` and `valid`.

Required checks:

```text
CSF-SIGNAL-SEMANTIC-001:
factor_manifest.panel_primary_key must be non-empty and equal upstream csf_data_ready panel_manifest.panel_primary_key when lineage_root is available.

CSF-SIGNAL-SEMANTIC-002:
factor_panel.parquet must be non-empty and unique on factor_manifest.panel_primary_key.

CSF-SIGNAL-SEMANTIC-003:
factor_panel.parquet must contain factor_manifest.final_score_field.

CSF-SIGNAL-SEMANTIC-004:
factor_manifest.final_score_field values must be numeric or null; at least one non-null score must exist.

CSF-SIGNAL-SEMANTIC-005:
factor_manifest.raw_factor_fields must be bound through input_field_map to upstream csf_data_ready shared_feature_base artifacts and source columns.

CSF-SIGNAL-SEMANTIC-006:
Every input_field_map.source_artifact must live under 02_csf_data_ready/author/formal/shared_feature_base or another explicitly allowed csf_data_ready formal artifact.

CSF-SIGNAL-SEMANTIC-007:
factor_coverage_report.parquet must be non-empty, coverage_ratio must be numeric in [0, 1], and every coverage_ratio must be >= factor_manifest.coverage_min_ratio.

CSF-SIGNAL-SEMANTIC-008:
factor_coverage_report dates must cover factor_panel dates.

CSF-SIGNAL-SEMANTIC-009:
factor_group_context.parquet must be non-empty and unique on the same panel key when neutralization_policy == group_neutral or group_context_fields is non-empty.

CSF-SIGNAL-SEMANTIC-010:
component_factor_manifest.score_combination_formula must be deterministic; reject empty strings and obvious train-learned wording such as learned_weight, optimize_on_test, backtest_selected.

CSF-SIGNAL-SEMANTIC-011:
single_factor requires either component_factor_ids == [] or a single self-reference; multi_factor_score requires component_factor_ids non-empty.

CSF-SIGNAL-SEMANTIC-012:
factor_direction must be high_better or low_better and must match route role constraints when future role-specific constraints are added.

CSF-SIGNAL-SEMANTIC-013:
factor_manifest, component_factor_manifest, route_inheritance_contract, and run_manifest must agree on factor_structure.

CSF-SIGNAL-SEMANTIC-014:
run_manifest.source_stage must be csf_data_ready and input_roots must reference 02_csf_data_ready plus 01_mandate research_route.yaml.
```

### Tasks

- [ ] **Task 2.1: 写 semantic validator 失败测试**

Create `tests/runtime/test_csf_signal_ready_semantic_validation.py`.

Tests:

```text
test_csf_signal_semantics_accepts_runtime_built_outputs
test_csf_signal_semantics_rejects_missing_final_score_column
test_csf_signal_semantics_rejects_duplicate_factor_panel_key
test_csf_signal_semantics_rejects_non_numeric_final_score
test_csf_signal_semantics_rejects_unbound_raw_factor_field
test_csf_signal_semantics_rejects_input_field_map_outside_csf_data_ready
test_csf_signal_semantics_rejects_coverage_below_declared_min_ratio
test_csf_signal_semantics_rejects_missing_group_context_when_group_neutral
test_csf_signal_semantics_rejects_train_learned_combination_formula
test_csf_signal_semantics_rejects_factor_structure_drift
```

Run:

```bash
python -m pytest tests/runtime/test_csf_signal_ready_semantic_validation.py -q
```

Expected RED:

```text
ModuleNotFoundError: runtime.tools.csf_signal_ready_contract_runtime
```

- [ ] **Task 2.2: 实现 `csf_signal_ready_contract_runtime.py`**

Implementation notes:

```text
Use pyarrow parquet readers for validation.
Do not add new dependencies.
Keep error codes stable and human-readable.
Avoid enforcing content equality; enforce structure, key consistency, enum, type, required references, and deterministic source binding.
```

Run:

```bash
python -m pytest tests/runtime/test_csf_signal_ready_semantic_validation.py -q
```

Expected GREEN.

- [ ] **Task 2.3: runtime build 后接入 semantic validator**

Modify `runtime/tools/csf_signal_ready_runtime.py`.

Build order:

```text
write formal artifacts
→ artifact contract validation
→ semantic validation
→ return stage_dir
```

If validation fails, raise `ValueError("csf_signal_ready semantic validation failed: ...")`.

Run:

```bash
python -m pytest tests/runtime/test_csf_signal_ready_runtime.py tests/runtime/test_csf_signal_ready_semantic_validation.py -q
```

- [ ] **Task 2.4: 修正 fixtures 的真实字段来源**

Update fixture drafts and helper outputs so `raw_factor_fields` align with actual upstream shared feature columns:

```text
return_1d
dollar_volume
beta_proxy
```

Add `input_field_map` examples that bind each raw field to:

```text
shared_feature_base/returns_panel.parquet.return_1d
shared_feature_base/liquidity_panel.parquet.dollar_volume
shared_feature_base/beta_inputs.parquet.beta_proxy
```

Run:

```bash
python -m pytest tests/helpers tests/pipeline/test_csf_pipeline.py -q
```

- [ ] **Task 2.5: smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

---

## Batch 3: Upstream Binding + Review Preflight

### 目标

把 `csf_signal_ready` 的 artifact contract、semantic validator 和 upstream binding 全部接进 review-entry preflight。reviewer 子代理只做 adversarial review，不承担第一层 shape/completeness/route-binding 检查。

### 文件范围

- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Modify: `runtime/tools/review_skillgen/upstream_binding_validator.py`
- Create: `tests/review/test_review_preflight_csf_signal_ready_contract.py`
- Modify: `tests/review/test_review_engine_csf_contract_gates.py`
- Modify: `tests/review/test_review_preflight.py`
- Modify: `tests/review/test_review_preflight_program_identity.py`

### Binding Checks

Extend `upstream_binding_validator.py` for `csf_signal_ready`:

```text
CSF-SIGNAL-BIND-001:
route_inheritance_contract.yaml must exactly match mandate research_route.yaml on research_route, factor_role, factor_structure, portfolio_expression, neutralization_policy, target_strategy_reference, group_taxonomy_reference.

CSF-SIGNAL-BIND-002:
route_inheritance_contract.source_route_digest_sha256 must match sha256 of mandate research_route.yaml text.

CSF-SIGNAL-BIND-003:
run_manifest.source_stage must be csf_data_ready and input_roots must include 02_csf_data_ready/author/formal references.

CSF-SIGNAL-BIND-004:
When neutralization_policy == group_neutral, factor_group_context.parquet group_context values must come from csf_data_ready asset_taxonomy_snapshot.parquet group_bucket values.

CSF-SIGNAL-BIND-005:
When target_strategy_reference is required by factor_role, requirement status must be required_satisfied and reference must be non-empty.

CSF-SIGNAL-BIND-006:
When group_taxonomy_reference is required by neutralization_policy, requirement status must be required_satisfied and reference must be non-empty.

CSF-SIGNAL-BIND-007:
factor_panel keys must be subset of csf_data_ready eligible universe keys, not a new independently invented asset/date universe.
```

### Review Preflight Integration

Modify `review_preflight.py`:

```python
def _check_artifact_contract(stage, author_formal_dir):
    if stage in {"csf_data_ready", "csf_signal_ready"}:
        ...

def _check_stage_semantics(stage, author_formal_dir, lineage_root):
    if stage == "csf_data_ready":
        ...
    if stage == "csf_signal_ready":
        validate_csf_signal_ready_semantics(author_formal_dir, lineage_root)
```

Error prefixes:

```text
ARTIFACT-CONTRACT-001
CSF-SIGNAL-SEMANTIC-001
CSF-SIGNAL-BIND-001
```

### Tasks

- [ ] **Task 3.1: 写 review preflight 失败测试**

Create `tests/review/test_review_preflight_csf_signal_ready_contract.py`.

Tests:

```text
test_review_preflight_blocks_csf_signal_ready_missing_contract_artifact
test_review_preflight_blocks_csf_signal_ready_missing_final_score_column
test_review_preflight_blocks_csf_signal_ready_route_digest_drift
test_review_preflight_blocks_csf_signal_ready_factor_panel_outside_eligible_universe
test_review_preflight_blocks_csf_signal_ready_group_context_taxonomy_drift
test_review_preflight_passes_runtime_built_csf_signal_ready_outputs
```

Run:

```bash
python -m pytest tests/review/test_review_preflight_csf_signal_ready_contract.py -q
```

Expected RED until integration exists.

- [ ] **Task 3.2: 接入 `review_preflight.py`**

Add `csf_signal_ready` to artifact and semantic preflight.

Run:

```bash
python -m pytest tests/review/test_review_preflight_csf_signal_ready_contract.py tests/review/test_review_preflight.py -q
```

- [ ] **Task 3.3: 强化 upstream binding validator**

Add route digest, input roots, eligible universe, taxonomy binding checks.

Run:

```bash
python -m pytest tests/review/test_review_preflight_csf_signal_ready_contract.py tests/review/test_review_engine_csf_contract_gates.py -q
```

- [ ] **Task 3.4: review engine regression**

Ensure existing `qros-review` path still produces `RETRY` for invalid artifacts and `PASS` for valid fixtures.

Run:

```bash
python -m pytest tests/review/test_review_engine_csf_contract_gates.py tests/review/test_review_preflight_program_identity.py -q
```

- [ ] **Task 3.5: full-smoke**

This batch touches review / next-stage orchestration and CSF routing gates. Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

---

## Batch 4: Skill / Docs Thin-Out

### 目标

修正 `qros-csf-signal-ready-author` 与 review skill 的漂移，让 skill 从“字段真值定义者”降级为“执行引导者”。字段和 artifact shape 只以 `contracts/artifacts/csf_signal_ready_artifacts.yaml`、runtime validator、workflow gate 为准。

### 文件范围

- Modify: `skills/csf_signal_ready/qros-csf-signal-ready-author/SKILL.md`
- Modify: `skills/csf_signal_ready/qros-csf-signal-ready-review/SKILL.md`
- Modify: `skills/core/qros-research-session/SKILL.md` if stage wording references old shape
- Modify: `docs/guides/stage-freeze-group-field-guide.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/codex-stage-review-skill-usage.md`
- Modify: `tests/skills/*`
- Modify: `tests/docs/*`

### Author Skill Target Wording

The author skill should say:

```text
不得手写或自行扩展 formal artifact shape。
必须先使用 runtime scaffold 创建 03_csf_signal_ready author layout。
必须读取 contracts/artifacts/csf_signal_ready_artifacts.yaml。
必须确认 5 个 runtime-facing freeze groups:
- factor_identity
- panel_contract
- factor_expression
- context_contract
- delivery_contract
必须从已 review closure PASS 的 csf_data_ready formal artifacts 派生 factor panel。
必须物化 factor_panel.parquet、factor_manifest.yaml、component_factor_manifest.yaml、factor_coverage_report.parquet、factor_group_context.parquet、route_inheritance_contract.yaml、run_manifest.json。
完成 build 后必须运行 qros-validate-stage --stage csf_signal_ready。
完成 build 后必须通过 csf_signal_ready semantic validator。
validator 不通过，不得进入 csf_signal_ready review。
```

Remove or replace old drifted names:

```text
factor_coverage.parquet → factor_coverage_report.parquet
signal_gate_decision.md → csf_signal_ready_gate_decision.md
factor_role_contract / factor_structure_contract / neutralization_policy → route inheritance from mandate plus runtime-facing freeze groups
```

### Review Skill Target Wording

The review skill should say:

```text
reviewer 不是第一轮 artifact completeness checker。
launcher 必须在 handoff 前完成 artifact contract / semantic / upstream binding preflight。
若 preflight 失败，不得 spawn reviewer。
stage-specific review 只审已通过 deterministic preflight 的 formal artifacts。
```

### Tasks

- [ ] **Task 4.1: 写 skill drift 测试**

Add or update tests:

```text
test_csf_signal_ready_author_skill_names_runtime_freeze_groups
test_csf_signal_ready_author_skill_does_not_reference_old_output_names
test_csf_signal_ready_author_skill_requires_artifact_contract
test_csf_signal_ready_author_skill_requires_validate_stage_before_review
test_csf_signal_ready_review_skill_mentions_preflight_before_reviewer
```

Run:

```bash
python -m pytest tests/skills -q
```

- [ ] **Task 4.2: 修改 author/review skill**

Keep skill concise. Do not paste the full schema into `SKILL.md`; link to contract and validator instead.

Run:

```bash
python -m pytest tests/skills -q
```

- [ ] **Task 4.3: docs sync**

Docs must explain why fields exist and use exact runtime-facing names.

Required doc sync:

```text
stage-freeze-group-field-guide.md: csf_signal_ready freeze groups and fields
qros-research-session-usage.md: csf_signal_ready validator/preflight behavior
qros-review-shared-protocol.md: csf_signal_ready deterministic preflight before reviewer
codex-stage-review-skill-usage.md: route_inheritance_contract and contract validator
```

Run:

```bash
python -m pytest tests/docs -q
```

- [ ] **Task 4.4: smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

---

## Batch 5: Agent Behavior Eval

### 目标

把 `csf_signal_ready` 的真实 agent 行为纳入 eval，重点不测“内容是否写得像”，而测 agent 是否按正确行为顺序执行：

```text
explicit skill trigger → skill first before any other tool
naive prompt → should trigger qros-csf-signal-ready-author
validator before review
reject missing upstream review closure
reject placeholder parquet
reject route drift / unconfirmed freeze groups
```

### 文件范围

- Modify: `contracts/agent_eval/qros_agent_behavior_eval_cases.yaml`
- Add: `tests/fixtures/agent_behavior/csf_signal_ready_*.jsonl`
- Modify: `tests/agent_eval/test_qros_agent_behavior_eval.py`
- Modify: `docs/guides/qros-agent-behavior-eval.md` if current docs mention case inventory

### Cases

Add deterministic transcript cases:

```text
explicit_csf_signal_ready_author_skill_first
naive_csf_signal_ready_prompt_triggers_author_skill
csf_signal_ready_rejects_missing_csf_data_ready_review_closure
csf_signal_ready_rejects_non_csf_mandate_route
csf_signal_ready_rejects_unconfirmed_freeze_groups
csf_signal_ready_rejects_placeholder_factor_panel_completion
csf_signal_ready_runs_artifact_validator_before_review
csf_signal_ready_runs_semantic_validator_before_review
csf_signal_ready_rejects_route_inheritance_drift
csf_signal_ready_rejects_raw_field_without_input_binding
```

Expected event patterns:

```text
required:
- qros-csf-signal-ready-author skill read/invoked
- scaffold/build runtime command or helper
- qros-validate-stage --stage csf_signal_ready
- semantic validation before review

forbidden before skill:
- qros-review
- editing formal artifacts
- running train/test/backtest
- committing code

forbidden completion:
- claiming csf_signal_ready done with placeholder factor_panel
- entering csf_train_freeze before csf_signal_ready review closure
```

### Tasks

- [ ] **Task 5.1: 写 eval case tests**

Run:

```bash
python -m pytest tests/agent_eval/test_qros_agent_behavior_eval.py -q
```

Expected RED until cases and fixtures exist.

- [ ] **Task 5.2: Add fake transcripts**

Add compact JSONL transcripts that cover pass/fail event ordering. These are deterministic tests of the harness, not real LLM eval.

Run:

```bash
python -m pytest tests/agent_eval/test_qros_agent_behavior_eval.py -q
```

- [ ] **Task 5.3: Optional live eval command**

Only run when user provides a real agent command template:

```bash
python runtime/scripts/run_agent_behavior_eval.py --case-id explicit_csf_signal_ready_author_skill_first --agent-command-template '<template>'
```

If no real template is available, report that only deterministic fake transcript eval was run.

- [ ] **Task 5.4: smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

---

## Batch 6: End-to-End CSF Route Smoke

### 目标

确认前 5 批不会只让单点测试通过，而是仍然支持完整 CSF route 从 data 到 signal 再到 train 的正常推进。

### 文件范围

- Modify tests only if previous batches expose fixture drift:
  - `tests/pipeline/test_csf_pipeline.py`
  - `tests/e2e/test_csf_agent_session.py`
  - `tests/session/test_research_session_runtime.py`
  - `tests/anti_drift/test_anti_drift_replay.py`
  - `tests/fixtures/anti_drift/*.json`

### Tasks

- [ ] **Task 6.1: Pipeline focused tests**

Run:

```bash
python -m pytest tests/pipeline/test_csf_pipeline.py tests/e2e/test_csf_agent_session.py -q
```

- [ ] **Task 6.2: Session and anti-drift tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/anti_drift/test_anti_drift_replay.py -q
```

If snapshots fail because output shape intentionally changed, update snapshots in the same batch and document the exact reason.

- [ ] **Task 6.3: Full smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

---

## 关键设计决策

### 不合并 `csf_signal_ready` 文件

不建议把 `factor_manifest.yaml`、`component_factor_manifest.yaml`、`route_inheritance_contract.yaml` 合并成一个大 YAML。原因：

- `factor_manifest.yaml` 是下游 train/test/backtest 消费的因子身份和字段合同。
- `component_factor_manifest.yaml` 是多因子组合的独立合同，后续 `csf_train_freeze` 要判断哪些 signal axes 不可再搜索。
- `route_inheritance_contract.yaml` 是 mandate route 的继承凭证，属于 upstream binding，不应混入 factor 内容本身。
- `factor_panel.parquet`、`factor_coverage_report.parquet`、`factor_group_context.parquet` 是不同粒度的机器表，合并会降低 validator 精度。

可以做的是让 docs 变薄、catalog 更清晰，而不是合并 machine artifacts。

### 字段一致与内容一致的边界

强制保证：

```text
文件存在
字段存在
类型正确
枚举合法
主键唯一
动态字段绑定
输入字段来源
coverage 不低于声明阈值
route inheritance 不漂移
review 前 validator 必须通过
```

不强制保证：

```text
同一个 raw idea 每次得到完全相同的 factor score 数值
agent 生成的 markdown 文案逐字一致
用户选择的因子表达内容完全一致
```

### `input_field_map` 是本阶段最重要的新字段

只冻结 `raw_factor_fields` 不够，因为 agent 可以写出不存在或来源不明的字段名。`input_field_map` 应成为 `csf_signal_ready` 的字段来源合同：

```yaml
input_field_map:
  - raw_field: return_1d
    source_artifact: shared_feature_base/returns_panel.parquet
    source_column: return_1d
  - raw_field: dollar_volume
    source_artifact: shared_feature_base/liquidity_panel.parquet
    source_column: dollar_volume
  - raw_field: beta_proxy
    source_artifact: shared_feature_base/beta_inputs.parquet
    source_column: beta_proxy
```

Validator 只检查来源绑定和列存在，不判断因子公式是否“聪明”。

### `coverage_min_ratio` 应机器可读

当前 `coverage_contract` 是自由文本，不能可靠校验。保留它作为人类说明，但新增 `coverage_min_ratio: number` 作为机器门禁字段。

### 先做哪部分

第一批应该做 Batch 1，不是因为它是 MVP，而是因为后续所有 semantic/review/skill/eval 都依赖稳定 artifact contract。没有 `csf_signal_ready_artifacts.yaml`，后面只能继续把字段散落在 runtime、workflow gate、skill 和测试里。

---

## 总体验证矩阵

Focused tests:

```bash
python -m pytest tests/contracts/test_csf_signal_ready_artifact_contract.py -q
python -m pytest tests/runtime/test_artifact_contract_runtime.py -q
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py -q
python -m pytest tests/runtime/test_csf_signal_ready_runtime.py -q
python -m pytest tests/runtime/test_csf_signal_ready_semantic_validation.py -q
python -m pytest tests/review/test_review_preflight_csf_signal_ready_contract.py -q
python -m pytest tests/review/test_review_engine_csf_contract_gates.py -q
python -m pytest tests/skills -q
python -m pytest tests/docs -q
python -m pytest tests/agent_eval/test_qros_agent_behavior_eval.py -q
python -m pytest tests/pipeline/test_csf_pipeline.py tests/e2e/test_csf_agent_session.py -q
```

Smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full-smoke required when a batch touches workflow gate semantics, review orchestration, CSF routing, anti-drift snapshots, or next-stage behavior:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

---

## Acceptance Criteria

Implementation is complete only when:

- `contracts/artifacts/csf_signal_ready_artifacts.yaml` exists and is tested.
- `qros-validate-stage --stage csf_signal_ready` passes on runtime-built outputs and fails on invalid shape.
- `build_csf_signal_ready_from_data_ready()` fails before returning if shape or semantic validation fails.
- `review_preflight.py` blocks invalid `csf_signal_ready` before reviewer handoff.
- `qros-csf-signal-ready-author` no longer contains old output names or old freeze group names.
- Docs use runtime-facing artifact and field names exactly.
- Agent behavior eval includes `csf_signal_ready` cases for skill-first, validator-before-review, and no-placeholder behavior.
- Focused tests, smoke, and all required full-smoke runs are reported with command and result.
