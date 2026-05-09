# TSS Test Evidence CSF Parity 改造设计

## 背景

`tss_test_evidence` 已经接入了 artifact contract validation 和 TSS semantic validator hook，但当前语义校验太薄，只检查 `tss_selected_variants_test.csv` 的 selected variants 是否来自 train kept set。

这导致一个流程缺口：stage review 可以被标记为 `launcher_review_ready_status: complete`，但 handoff 里没有足够证据让 reviewer 独立验证以下阻断项：

- test window 是否独立于 train window
- test 阶段是否没有重估 train 阈值
- selected variants 是否全部来自 `04_tss_train_freeze` kept set
- 当前 stage 是否绑定了 `time_split.json`、`tss_train_freeze.yaml`、`train_variant_ledger.csv`、train closure 等上游冻结产物

BTC 测试线的 `tss_test_evidence` review 因此进入 reviewer 后才给出 `RETRY`。这类问题应在 review 前 deterministic preflight 阶段失败，而不是消耗 adversarial review。

## 决策

先做 **方案 B：CSF parity for TSS test evidence**。

本次不抽象全局 upstream binding proof 框架，只把 `csf_test_evidence` 已经比较成熟的门禁模式定向移植到 `tss_test_evidence`：

```text
author build
→ formal artifacts
→ artifact contract validation
→ TSS semantic validation
→ upstream binding preflight
→ review handoff
→ reviewer
→ qros-review closure
```

改造后的原则是：reviewer 只审机制、证据强弱和残留风险；reviewer 不应该成为第一道发现 handoff 不可审的组件。

## 非目标

- 不修改 CSF 路径行为。
- 不允许 reviewer 读取上游目录来绕过 handoff 缺口。
- 不把 `mean_forward_return > 0` 变成本阶段正式 gate。
- 不把 `tss_test_evidence` 改造成 backtest、交易成本或组合执行门禁。
- 不在本次实现里抽象所有 stage 通用的 upstream proof 框架。

## 目标行为

`tss_test_evidence` 进入 review 前必须满足：

- `author/formal` 中存在 stage-local、review-scoped 的 split/threshold/variant/upstream proof。
- `qros-validate-stage --stage tss_test_evidence` 能检查新产物 shape。
- `run_review_preflight(stage=tss_test_evidence)` 能检查新产物语义和上游绑定。
- `qros-review-cycle prepare` 写出的 `adversarial_review_request.yaml` 中，`upstream_binding_artifact_paths` 不再为空。
- 如果 proof 缺失、digest 过期、selected variant 漂移或 timestamp 越界，则不得进入 reviewer lane。

## 新增正式产物

三个产物都落在：

```text
05_tss_test_evidence/author/formal/
```

### `split_threshold_attestation.yaml`

职责：把 split independence 和 no-retuning 从自然语言声明变成机器可读证明。

建议字段：

```yaml
stage: tss_test_evidence
lineage_id: btc
research_route: time_series_signal
train_window:
  source: time_split.json::train
  start: "2024-03-01T00:00:00+00:00"
  end: "2024-08-31T23:59:59+00:00"
test_window:
  source: time_split.json::test
  start: "2024-09-01T00:00:00+00:00"
  end: "2024-10-31T23:59:59+00:00"
label_window:
  max_label_timestamp: "2024-10-31T23:59:59+00:00"
threshold_provenance:
  source_stage: tss_train_freeze
  threshold_artifact: 04_tss_train_freeze/author/formal/tss_train_freeze.yaml
  threshold_ledger: 04_tss_train_freeze/author/formal/train_threshold_ledger.csv
  no_test_window_retuning: true
```

必须校验：

- `stage == tss_test_evidence`
- `research_route == time_series_signal`
- `test_window.start > train_window.end`
- `threshold_provenance.no_test_window_retuning == true`
- `event_forward_return.parquet.timestamp` 全部落在 test window 内
- 如果存在 `label_timestamp`，必须满足 `label_timestamp > timestamp`
- 如果存在 `label_window.max_label_timestamp`，所有 `label_timestamp` 不得超过它

### `selected_variant_membership_proof.csv`

职责：把 “selected variants 来自 train kept set” 变成当前 stage 内可审的 proof table。

字段：

```csv
variant_id,horizon,status,train_kept_status,threshold_source,membership_verdict
```

必须校验：

- `tss_selected_variants_test.csv` 中每个 selected `(variant_id, horizon)` 都有 proof row
- selected proof row 必须满足 `train_kept_status=kept`
- selected proof row 必须满足 `membership_verdict=pass`
- selected `variant_id` 必须存在于 `04_tss_train_freeze/author/formal/train_variant_ledger.csv` 且 status 为 `kept`
- `(variant_id, horizon)` 不允许重复

### `upstream_binding_digest_ledger.yaml`

职责：记录本阶段声称复用的上游冻结产物和 digest，供 preflight 和 reviewer handoff 使用。

建议字段：

```yaml
stage: tss_test_evidence
lineage_id: btc
bindings:
  - logical_name: time_split
    path: 01_mandate/author/formal/time_split.json
    required: true
    digest: "<sha256>"
  - logical_name: train_freeze_contract
    path: 04_tss_train_freeze/author/formal/tss_train_freeze.yaml
    required: true
    digest: "<sha256>"
  - logical_name: train_variant_ledger
    path: 04_tss_train_freeze/author/formal/train_variant_ledger.csv
    required: true
    digest: "<sha256>"
  - logical_name: train_threshold_ledger
    path: 04_tss_train_freeze/author/formal/train_threshold_ledger.csv
    required: true
    digest: "<sha256>"
  - logical_name: train_freeze_review_closure
    path: 04_tss_train_freeze/review/closure/stage_completion_certificate.yaml
    required: true
    digest: "<sha256>"
```

必须校验：

- 所有 `required: true` 的 path 都存在
- ledger 中 digest 与当前文件内容一致
- train closure 指向 `stage: tss_train_freeze`
- train closure verdict 必须是可推进状态，不得是 `RETRY`、`NO-GO` 或 failure handling 状态

## Artifact Contract 改造

修改：

```text
contracts/artifacts/tss_test_evidence_artifacts.yaml
```

需要新增三个 artifact 条目：

- `split_threshold_attestation.yaml`
- `selected_variant_membership_proof.csv`
- `upstream_binding_digest_ledger.yaml`

需要扩展 `event_forward_return.parquet` required columns：

- `variant_id`
- `horizon`
- `asset`
- `timestamp`
- `forward_return`
- `asset_forward_return`
- `signal_direction`
- `label_timestamp`

需要扩展 `run_manifest.json` required fields，使它接近 CSF 的 provenance 形状：

- `input_roots`
- `stage_outputs`
- `program_dir`
- `program_entrypoint`
- `program_execution_manifest`
- `selected_variant_ids`
- `selection_rule`
- `primary_evidence_contract`

保留已有字段：

- `stage`
- `lineage_id`
- `research_route`
- `source_stage`
- `primary_key`
- `machine_artifacts`
- `consumer_stage`
- `replay_command`

## Runtime 改造

修改：

```text
runtime/tools/tss_test_evidence_runtime.py
```

`build_tss_test_evidence_from_train_freeze()` 必须：

- 读取 `01_mandate/author/formal/time_split.json`
- 读取 `04_tss_train_freeze/author/formal/tss_train_freeze.yaml`
- 读取 `04_tss_train_freeze/author/formal/train_variant_ledger.csv`
- 读取 `04_tss_train_freeze/author/formal/train_threshold_ledger.csv`
- 读取 `04_tss_train_freeze/review/closure/stage_completion_certificate.yaml`
- 生成 `split_threshold_attestation.yaml`
- 生成 `selected_variant_membership_proof.csv`
- 生成 `upstream_binding_digest_ledger.yaml`
- 把新产物写入 `run_manifest.stage_outputs`
- 把上游绑定写入 `run_manifest.input_roots`
- build 结束前运行 artifact contract validation 和 semantic validation

如果缺少上游 closure，本阶段 build 应失败。这样可以强制 `tss_test_evidence` 只消费已通过 review 的 `tss_train_freeze`。

## Semantic Validator 改造

修改：

```text
runtime/tools/tss_test_evidence_contract_runtime.py
```

保留现有 selected subset check，并新增：

- 读取并校验 `split_threshold_attestation.yaml`
- 读取并校验 `selected_variant_membership_proof.csv`
- 读取并校验 `upstream_binding_digest_ledger.yaml`
- 校验 `signal_performance_summary.json.selected_variant_ids` 与 `tss_selected_variants_test.csv` 一致
- 校验 `tss_test_gate_table.csv` 覆盖所有 selected rows
- 校验 `event_forward_return.parquet` 只包含 selected variants 和 selected horizons
- 校验 timestamp / label_timestamp 对齐
- 校验 `run_manifest.input_roots` 包含必需上游绑定
- 校验 `run_manifest.stage_outputs` 包含所有正式产物

preflight 中错误前缀继续使用现有 hook：

```text
TSS-TEST-SEMANTIC-001
```

## Review Scope 改造

修改：

```text
runtime/tools/review_skillgen/review_scope_builder.py
```

当 `stage == "tss_test_evidence"` 时，`upstream_binding_artifact_paths` 必须包含：

```python
[
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
]
```

这不是让 reviewer 读取上游目录，而是把上游绑定证明物化到当前 `author/formal`，再交给 reviewer。

## Skill 和文档改造

需要同步更新：

```text
skills/tss_test_evidence/qros-tss-test-evidence-author/SKILL.md
skills/tss_test_evidence/qros-tss-test-evidence-review/SKILL.md
docs/sop/main-flow/05_tss_test_evidence_sop_cn.md
```

文案重点：

- author 必须真实生成三个 proof artifacts
- review 前必须通过 `ARTIFACT-CONTRACT-001` 和 `TSS-TEST-SEMANTIC-001`
- `upstream_binding_artifact_paths` 为空时不得启动 reviewer
- 缺少 proof artifacts 是 preflight failure，不是普通 reviewer finding

## 测试计划

Focused tests：

```bash
python -m pytest tests/runtime/test_tss_test_evidence_runtime.py tests/runtime/test_tss_test_evidence_semantic_validation.py tests/review/test_review_preflight_tss_test_evidence_contract.py
```

必须覆盖：

- runtime build 写出三个 proof artifacts
- `run_manifest.stage_outputs` 包含 proof artifacts
- `run_manifest.input_roots` 包含必需上游绑定
- 缺少 membership proof row 时 semantic validation 失败
- selected variant 漂移时 semantic validation 失败
- digest ledger 过期时 semantic validation 失败
- event timestamp 越出 test window 时 semantic validation 失败
- label timestamp 不晚于 signal timestamp 时 semantic validation 失败
- review preflight 在 proof 缺失时失败
- review preflight 对有效 runtime-built outputs 通过
- review scope 中 `upstream_binding_artifact_paths` 不为空

全局验证：

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

需要跑 `full-smoke`，因为本改造触及 TSS stage gate semantics、review preflight 和 next-stage eligibility。

## 验收标准

- `tss_test_evidence` 不再能以空 upstream binding scope 进入 review。
- BTC 测试线中出现过的 “reviewer 无法验证 split/threshold/membership” 问题会在 preflight 阶段失败。
- 有效 runtime-built `tss_test_evidence` 能通过 artifact contract、semantic validator、upstream binding validation 和 review preflight。
- reviewer handoff 保持隔离，只读取 `review/request/*` 与 `author/formal/*`。
- CSF 路径行为不变。

## 风险和兼容性

- 旧的 active research repo 中已有 `05_tss_test_evidence` 产物会因为缺少新 proof artifacts 而无法通过新 preflight，需要重新 build 或迁移。
- digest proof 对 fixture 顺序敏感；测试必须先写上游 fixture，再生成 digest ledger。
- artifact contract 目前禁止未知 machine top-level fields，所以 contract、runtime builder、tests 必须同批更新。
- 如果 train closure fixture 过于简化，需要给测试补最小合法 closure，而不是放松 validator。
