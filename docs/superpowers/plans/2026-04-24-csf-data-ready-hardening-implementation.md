# CSF Data Ready Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `csf_data_ready` 从“能生成若干文件”升级为“formal artifacts、parquet schema、上游 mandate 绑定、placeholder/realism gate、review preflight 和 agent 行为都可回归验证”的硬门禁阶段。

**Architecture:** 先建立 `contracts/artifacts/csf_data_ready_artifacts.yaml` 作为 formal artifact shape 真值层，扩展通用 artifact validator 支持 directory/parquet，再把 stage-specific CSF semantic checks 放到独立 runtime helper 中，最后接入 build 后校验、CLI、review preflight、skill/docs 和 agent behavior eval。完整方案分 5 批执行，每批都能独立验证并产生明确能力增量。

**Tech Stack:** Python stdlib, PyYAML, PyArrow parquet, pytest, existing QROS runtime helpers under `runtime/tools/`, existing review preflight and agent eval harness.

**Execution constraints:** 不得 `git commit`、`git push`、创建 PR 或改 `main`，除非用户在看到 diff 和验证结果后明确确认。计划文档位于 `docs/superpowers/plans/`，当前该目录被 `.gitignore` 忽略。

---

## 完整终局

`csf_data_ready` 最终必须满足这条链：

```text
mandate review closure complete
→ mandate research_route.yaml.research_route == cross_sectional_factor
→ csf_data_ready freeze groups confirmed
→ lineage-local stage program exists and is valid
→ formal artifacts materialized under 02_csf_data_ready/author/formal
→ artifact contract validation passes
→ parquet schema and directory shape validation passes
→ CSF semantic realism validation passes
→ upstream mandate binding validation passes
→ review-entry preflight blocks invalid outputs before reviewer lane
→ agent behavior eval covers skill-first and no-fake-completion behavior
```

最终能力分 5 层：

1. **Artifact Contract:** `contracts/artifacts/csf_data_ready_artifacts.yaml` 定义文件、目录、JSON/Markdown/parquet shape。
2. **Runtime Gate:** `build_csf_data_ready_from_mandate()` 生成后自动 validate，`qros-validate-stage --stage csf_data_ready` 可独立运行。
3. **Semantic / Realism Gate:** 检查 parquet 非空、required columns、主键唯一、coverage floor、shared feature base 非空。
4. **Upstream Binding + Review Preflight:** 校验 mandate route/taxonomy/neutralization 绑定，并在 reviewer 进入前 fail fast。
5. **Skill / Agent Eval:** skill 不再定义字段真值；agent eval 覆盖错误触发路径。

---

## 分批路线图

| 批次 | 名称 | 能力增量 | 是否建议本轮先做 |
| --- | --- | --- | --- |
| 1 | Contract + Generic Validator + Runtime Gate | 建立 csf_data_ready formal artifact shape 真值层，支持 parquet/directory shape，build 后自动 validate | 是 |
| 2 | CSF Semantic / Realism Gate | 挡掉空 parquet、主键重复、coverage floor 不满足、shared_feature_base 空目录 | 第二步 |
| 3 | Upstream Binding + Review Preflight | 把 route/taxonomy/neutralization 绑定和 deterministic checks 接入 review-entry | 第三步 |
| 4 | Skill / Docs Thin-Out | skill/docs 指向 contract 和 validator，不再维护字段真值 | 第四步 |
| 5 | Agent Behavior Eval | 回归真实 agent 是否 skill-first、contract-first、no-placeholder | 第五步 |

每批完成后都要报告：

```text
完整 plan 进度：
- 已完成：<批次>
- 未完成：<剩余批次>
- 下一步建议：<下一批>
- 验证：<focused tests / smoke / full-smoke 是否需要>
```

---

## Batch 1: Contract + Generic Validator + Runtime Gate

### 目标

建立 `csf_data_ready` 的机器真值层，并让 runtime/CLI 都能验证它。该批不做完整语义判断，只做 shape、schema、目录和 build 后自动校验。

### 文件范围

- Create: `contracts/artifacts/csf_data_ready_artifacts.yaml`
- Create: `tests/contracts/test_csf_data_ready_artifact_contract.py`
- Create: `tests/session/test_csf_data_ready_artifact_shape.py`
- Modify: `runtime/tools/artifact_contract_runtime.py`
- Modify: `runtime/tools/csf_data_ready_runtime.py`
- Modify: `tests/runtime/test_artifact_contract_runtime.py`
- Modify: `tests/runtime/test_validate_stage_artifacts_script.py`
- Modify: `tests/runtime/test_csf_data_ready_runtime.py`
- Modify: `tests/bootstrap/test_project_bootstrap.py`

### Contract Shape

新增 `contracts/artifacts/csf_data_ready_artifacts.yaml`，stage dir 必须是：

```yaml
stage: csf_data_ready
stage_dir: 02_csf_data_ready/author/formal
```

必须锁定这些 artifacts：

```text
panel_manifest.json
asset_universe_membership.parquet
cross_section_coverage.parquet
eligibility_base_mask.parquet
shared_feature_base/
asset_taxonomy_snapshot.parquet
csf_data_contract.md
csf_data_ready_gate_decision.md
run_manifest.json
rebuild_csf_data_ready.py
artifact_catalog.md
field_dictionary.md
```

`panel_manifest.json` 必须包含：

```text
stage
lineage_id
panel_primary_key
cross_section_time_key
asset_key
shared_feature_outputs
machine_artifacts
coverage_floor_min_ratio
```

`run_manifest.json` 必须包含：

```text
stage
lineage_id
source_stage
panel_primary_key
cross_section_time_key
asset_key
universe_membership_rule
group_taxonomy_reference
eligibility_base_rule
coverage_floor_rule
shared_feature_outputs
machine_artifacts
consumer_stage
frozen_inputs_note
runtime_root_hint
runtime_module
runtime_function
source_git_revision
program_artifacts
replay_working_directory
replay_command
```

Parquet required columns：

```text
asset_universe_membership.parquet: date, asset, in_universe
eligibility_base_mask.parquet: date, asset, eligible
cross_section_coverage.parquet: date, coverage_ratio, asset_count
asset_taxonomy_snapshot.parquet: asset, date, group_taxonomy_reference, group_bucket
shared_feature_base/returns_panel.parquet: date, asset, return_1d
shared_feature_base/liquidity_panel.parquet: date, asset, dollar_volume
shared_feature_base/beta_inputs.parquet: date, asset, beta_proxy
```

### Tasks

- [ ] **Task 1.1: 写 contract 失败测试**

Create `tests/contracts/test_csf_data_ready_artifact_contract.py`.

Tests:

```text
test_csf_data_ready_artifact_contract_exists_and_declares_stage_shape
test_csf_data_ready_contract_locks_panel_manifest_fields
test_csf_data_ready_contract_locks_run_manifest_fields
test_csf_data_ready_contract_locks_parquet_columns
test_csf_data_ready_contract_field_paths_are_unique
```

Run:

```bash
python -m pytest tests/contracts/test_csf_data_ready_artifact_contract.py -q
```

Expected RED:

```text
FAILED ... contracts/artifacts/csf_data_ready_artifacts.yaml does not exist
```

- [ ] **Task 1.2: 新增 `csf_data_ready_artifacts.yaml`**

Implement the contract with artifact types:

```text
json
markdown
parquet
directory
script
```

The `script` type should only check file existence and executable/readable text in Batch 1.

Run:

```bash
python -m pytest tests/contracts/test_csf_data_ready_artifact_contract.py -q
```

Expected GREEN:

```text
all tests passed
```

- [ ] **Task 1.3: 写 generic validator 失败测试**

Modify `tests/runtime/test_artifact_contract_runtime.py`.

Add tests:

```text
test_validate_stage_artifacts_reports_missing_required_directory_file
test_validate_stage_artifacts_reports_parquet_missing_required_column
test_validate_stage_artifacts_reports_empty_parquet_when_non_empty_required
test_validate_stage_artifacts_accepts_valid_csf_data_ready_shape
```

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py -q
```

Expected RED:

```text
unsupported artifact contract stage: csf_data_ready
```

or:

```text
unsupported artifact type 'parquet'
```

- [ ] **Task 1.4: 扩展 `artifact_contract_runtime.py`**

Modify `runtime/tools/artifact_contract_runtime.py`.

Required changes:

```text
ARTIFACT_CONTRACTS 增加 csf_data_ready
validate_stage_artifacts 支持 type=directory
validate_stage_artifacts 支持 type=parquet
validate_stage_artifacts 支持 type=script
parquet 校验 required_columns
parquet 支持 non_empty: true
directory 校验 required_files
```

Implementation boundary:

```text
Batch 1 不实现 unique_by、coverage floor、upstream binding。
这些放 Batch 2/3。
```

Run:

```bash
python -m pytest tests/runtime/test_artifact_contract_runtime.py tests/contracts/test_csf_data_ready_artifact_contract.py -q
```

Expected GREEN:

```text
all tests passed
```

- [ ] **Task 1.5: 写 generated shape 失败测试**

Create `tests/session/test_csf_data_ready_artifact_shape.py`.

Tests:

```text
test_generated_csf_data_ready_file_tree_matches_artifact_contract
test_generated_csf_data_ready_json_shapes_match_contract
test_generated_csf_data_ready_parquet_columns_match_contract
test_generated_csf_data_ready_passes_artifact_shape_validator
```

Use existing helpers from `tests/runtime/test_csf_data_ready_runtime.py` where safe:

```text
_prepare_mandate_stage
_csf_data_ready_draft
_write_yaml
```

Run:

```bash
python -m pytest tests/session/test_csf_data_ready_artifact_shape.py -q
```

Expected RED before runtime integration:

```text
FAILED ... unsupported artifact contract stage: csf_data_ready
```

or:

```text
FAILED ... missing required artifact / required column
```

- [ ] **Task 1.6: Build 后自动 validate**

Modify `runtime/tools/csf_data_ready_runtime.py`.

After all formal artifacts are written and before `return stage_dir`, add:

```text
load_artifact_contract("csf_data_ready")
validate_stage_artifacts(stage_formal_dir, contract)
if invalid: raise ValueError("csf_data_ready formal artifacts do not match artifact contract: ...")
```

Do not add semantic realism checks here yet.

Run:

```bash
python -m pytest tests/runtime/test_csf_data_ready_runtime.py tests/session/test_csf_data_ready_artifact_shape.py -q
```

Expected GREEN:

```text
all tests passed
```

- [ ] **Task 1.7: CLI 支持 `--stage csf_data_ready`**

Modify `tests/runtime/test_validate_stage_artifacts_script.py`.

Add tests:

```text
test_validate_stage_artifacts_script_accepts_valid_csf_data_ready
test_validate_stage_artifacts_script_reports_invalid_csf_data_ready_shape
```

Run:

```bash
python -m pytest tests/runtime/test_validate_stage_artifacts_script.py -q
```

Expected GREEN:

```text
all tests passed
```

- [ ] **Task 1.8: Bootstrap asset coverage**

Modify `tests/bootstrap/test_project_bootstrap.py`.

Assert:

```text
contracts/artifacts/csf_data_ready_artifacts.yaml exists
```

Run:

```bash
python -m pytest tests/bootstrap/test_project_bootstrap.py -q
```

Expected GREEN:

```text
all tests passed
```

### Batch 1 Verification

Run:

```bash
python -m pytest \
  tests/contracts/test_csf_data_ready_artifact_contract.py \
  tests/runtime/test_artifact_contract_runtime.py \
  tests/runtime/test_validate_stage_artifacts_script.py \
  tests/runtime/test_csf_data_ready_runtime.py \
  tests/session/test_csf_data_ready_artifact_shape.py \
  tests/bootstrap/test_project_bootstrap.py \
  -q
```

Then:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full-smoke decision:

```text
Batch 1 不改 qros-research-session flow/gate semantics，不强制 full-smoke。
```

Batch 1 completion report must say:

```text
已完成：Batch 1 Contract + Generic Validator + Runtime Gate
未完成：Batch 2-5
下一步建议：Batch 2 CSF Semantic / Realism Gate
```

---

## Batch 2: CSF Semantic / Realism Gate

### 目标

挡掉“有文件但是假完成”的 `csf_data_ready`。

### 文件范围

- Create: `runtime/tools/csf_data_ready_contract_runtime.py`
- Create: `tests/runtime/test_csf_data_ready_semantic_validation.py`
- Modify: `runtime/tools/csf_data_ready_runtime.py`
- Modify: `tests/runtime/test_csf_data_ready_runtime.py`

### Semantic Checks

Implement `validate_csf_data_ready_semantics(stage_formal_dir: Path) -> ArtifactValidationResult`.

Checks:

```text
panel_manifest.json.panel_primary_key == ["date", "asset"]
asset_universe_membership.parquet non-empty
eligibility_base_mask.parquet non-empty
eligibility_base_mask unique on (date, asset)
asset_universe_membership unique on (date, asset)
cross_section_coverage.parquet has coverage_ratio
min(cross_section_coverage.coverage_ratio) >= panel_manifest.coverage_floor_min_ratio
shared_feature_base/ has required parquet files from shared_feature_outputs
each shared_feature_base parquet is non-empty
```

If `panel_manifest.shared_feature_outputs = ["returns_panel", "liquidity_panel", "beta_inputs"]`, required files:

```text
shared_feature_base/returns_panel.parquet
shared_feature_base/liquidity_panel.parquet
shared_feature_base/beta_inputs.parquet
```

### Tests

Add tests:

```text
test_semantic_validator_accepts_generated_csf_data_ready
test_semantic_validator_rejects_empty_membership
test_semantic_validator_rejects_duplicate_eligibility_key
test_semantic_validator_rejects_coverage_floor_breach
test_semantic_validator_rejects_empty_shared_feature_base
```

### Batch 2 Verification

Run:

```bash
python -m pytest \
  tests/runtime/test_csf_data_ready_semantic_validation.py \
  tests/runtime/test_csf_data_ready_runtime.py \
  tests/session/test_csf_data_ready_artifact_shape.py \
  -q
```

Then:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full-smoke decision:

```text
Batch 2 不改 session flow/gate semantics，不强制 full-smoke。
```

---

## Batch 3: Upstream Binding + Review Preflight

### 目标

确保 `csf_data_ready` 不能脱离 mandate 重定义 route、taxonomy、neutralization 或 universe 语义，并在 reviewer lane 前 fail fast。

### 文件范围

- Modify: `runtime/tools/review_skillgen/upstream_binding_validator.py`
- Modify: `runtime/tools/review_skillgen/review_preflight.py`
- Create: `tests/review/test_review_preflight_csf_data_ready_contract.py`
- Modify: `tests/review/test_review_engine_csf_contract_gates.py`
- Possibly modify: `runtime/tools/research_session.py` only if explicitly deciding to make csf_data_ready review-entry preflight mandatory in session flow.

### Binding Checks

Enhance `_check_csf_data_ready_route_binding()` to check:

```text
mandate research_route.yaml exists
mandate research_route == cross_sectional_factor
if mandate neutralization_policy == group_neutral:
  mandate group_taxonomy_reference must be non-empty
  csf_data_ready asset_taxonomy_snapshot.parquet must exist
  asset_taxonomy_snapshot.group_taxonomy_reference must match mandate group_taxonomy_reference
panel_manifest.stage == csf_data_ready
run_manifest.source_stage == mandate
run_manifest.consumer_stage == csf_signal_ready
```

Review preflight should include:

```text
artifact contract validation
semantic realism validation
upstream binding validation
```

### Tests

Add tests:

```text
test_review_preflight_blocks_csf_data_ready_when_artifact_contract_fails
test_review_preflight_blocks_csf_data_ready_when_route_is_not_csf
test_review_preflight_blocks_csf_data_ready_when_taxonomy_snapshot_missing_for_group_neutral
test_review_preflight_blocks_csf_data_ready_when_taxonomy_reference_drifts
test_review_preflight_accepts_valid_csf_data_ready
```

### Batch 3 Verification

Run:

```bash
python -m pytest \
  tests/review/test_review_preflight_csf_data_ready_contract.py \
  tests/review/test_review_engine_csf_contract_gates.py \
  tests/runtime/test_csf_data_ready_semantic_validation.py \
  -q
```

Then smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full-smoke decision:

```text
如果只增强 standalone review_preflight，不改 research_session stage transition，可不跑 full-smoke。
如果让 csf_data_ready_review_confirmation_pending 在 session flow 中强制执行 preflight，必须跑 full-smoke。
```

---

## Batch 4: Skill / Docs Thin-Out

### 目标

把 `qros-csf-data-ready-author` 从字段真值维护者降级为执行引导者。

### 文件范围

- Modify: `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- Modify: `skills/csf_data_ready/qros-csf-data-ready-review/SKILL.md`
- Modify: `docs/guides/stage-freeze-group-field-guide.md`
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `tests/skills/test_post_mandate_program_authoring_contracts.py`
- Create or modify docs tests under `tests/docs/`

### Required Skill Text

Author skill must say:

```text
contracts/artifacts/csf_data_ready_artifacts.yaml 是 formal artifact shape 真值层
不得把 SKILL.md 作为字段真值
必须先确认 freeze groups
必须使用 lineage-local stage program
必须通过 qros-validate-stage --stage csf_data_ready
validator/preflight 不通过，不得进入 csf_data_ready review
```

Review skill must say:

```text
reviewer 不替 runtime 重定义字段
先看 deterministic preflight 结果
再审查机制和残留风险
```

### Tests

Add/extend tests to assert:

```text
qros-csf-data-ready-author references csf_data_ready_artifacts.yaml
qros-csf-data-ready-author references qros-validate-stage --stage csf_data_ready
docs mention contract-first rule
docs do not claim placeholder parquet can satisfy csf_data_ready
```

### Batch 4 Verification

Run:

```bash
python -m pytest \
  tests/skills/test_post_mandate_program_authoring_contracts.py \
  tests/docs/test_post_mandate_program_boundary_docs.py \
  tests/docs/test_lineage_local_program_docs.py \
  -q
```

Then smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full-smoke decision:

```text
Pure skill/docs/test updates do not require full-smoke unless stage-display/session semantics are changed.
```

---

## Batch 5: Agent Behavior Eval

### 目标

测试真实 agent 行为是否遵守 `csf_data_ready` 的 stage gate，而不是只测试 runtime 函数。

### 文件范围

- Modify: `contracts/agent_eval/qros_agent_behavior_eval_cases.yaml`
- Modify: `runtime/tools/agent_behavior_eval.py` only if transcript/event assertions need a new artifact or validator check.
- Create: `tests/agent_eval/fixtures/fake_csf_data_ready_*.jsonl`
- Create: `tests/agent_eval/test_csf_data_ready_agent_behavior_cases.py`
- Modify: `docs/guides/qros-agent-behavior-eval.md`

### Cases

Add cases:

```text
explicit_csf_data_ready_author_skill_first
csf_data_ready_rejects_non_csf_mandate
csf_data_ready_rejects_unreviewed_mandate
csf_data_ready_rejects_unconfirmed_freeze_groups
csf_data_ready_rejects_placeholder_parquet_completion
csf_data_ready_runs_validator_before_review
```

Assertions:

```text
expected_skill == qros-csf-data-ready-author
forbid tool calls before expected skill
absent artifacts when gate not satisfied
present validator call or result marker when build succeeds
no review transition if validator/preflight fails
```

### Batch 5 Verification

Run deterministic agent eval tests:

```bash
python -m pytest tests/agent_eval tests/docs/test_agent_behavior_eval_docs.py -q
```

Run one manual/live dry-run only after deterministic tests pass:

```bash
qros-agent-eval \
  --case explicit_csf_data_ready_author_skill_first \
  --work-root /tmp/qros-agent-eval \
  --agent-command-template '<codex exec --json template>'
```

Full-smoke decision:

```text
Agent eval harness changes do not require full-smoke unless session flow/gate semantics are changed.
```

---

## Recommended Immediate Execution

下一次实现建议只执行 **Batch 1**，并在最终报告里明确：

```text
已完成：Batch 1 Contract + Generic Validator + Runtime Gate
未完成：Batch 2 Semantic / Realism Gate
未完成：Batch 3 Upstream Binding + Review Preflight
未完成：Batch 4 Skill / Docs Thin-Out
未完成：Batch 5 Agent Behavior Eval
下一步建议：Batch 2
```

这不是缩小完整方案，而是因为 Batch 2-5 都依赖 Batch 1 的 contract 和 parquet/directory validator。

---

## Verification Policy

每批最低要求：

```text
focused tests + smoke
```

需要 full-smoke 的情况：

```text
改 qros-research-session stage flow / gate semantics
改 review / display / next-stage orchestration
改 route split / CSF routing
改 anti-drift snapshots 或 canonical session stage naming
改 stage-display supported stage contract
改 lineage-local stage-program auto-author seams
```

如果只新增 contract、runtime validator、shape tests，不触碰 session transition，通常不需要 full-smoke。

---

## Self-Review

**Coverage:** 覆盖 artifact contract、parquet schema、runtime gate、CLI、semantic realism、upstream binding、review preflight、skill/docs、agent eval、verification tiers。

**No hidden scope:** 明确 Batch 1 只做 shape/schema/runtime gate，不宣称完成 semantic realism、review preflight 或 agent behavior eval。

**Next-step clarity:** 每批完成后都有下一批建议，避免“做完一段后不知道接下来干嘛”。
