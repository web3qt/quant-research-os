---
name: qros-csf-train-freeze-review
description: Codex review skill for CSF Train Freeze stage verification.
---

# CSF Train Freeze 审查

## 用途

冻结截面因子的预处理、中性化、分组、再平衡和 admissible variants

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 子代理执行要求

- 本 skill 必须由独立 reviewer 子代理执行，不得由当前 author 线程或启动 review 的主线程直接执行
- 在当前 `Codex-only` 版本里，发起 review 的主线程必须先通过 native `spawn_agent` 启动一个不继承 author 历史的 reviewer 子代理，再由该子代理执行本 skill
- 当前主线程只允许准备 `review/request/*`、等待 reviewer 子代理落 `review/result/*`，不得自己撰写 `adversarial_review_result.yaml` 或 `review_findings.yaml`
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/*`
- 若没有独立 reviewer 子代理，必须停在 review pending / launch blocked，不得退化成同线程 review

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_signal_ready 输出
- 预处理 / neutralization / bucket 提案
- rebalance 与 eligibility 提案

## 必需输出

必需输出:
- csf_train_freeze.yaml
- train_factor_quality.parquet
- train_variant_ledger.csv
- train_variant_rejects.csv
- train_bucket_diagnostics.parquet
- csf_train_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Train Freeze

正式门禁摘要：
必须全部满足：
- preprocess、standardize、neutralize、bucket、rebalance、eligibility 全部冻结
- signal-ready 已冻结的表达轴不再被当作 train 搜索轴
- 所有 train variant 都有身份记录
- reject 不是静默丢弃，而是显式记账
- downstream test 只能复用 frozen train rules
- neutralization 如存在，必须有独立合同和诊断
以下任一情况都不得出现：
- 根据 test/backtest 结果回写 train 口径
- 只有保留者，没有 reject ledger
- quantile / bucket 规则未冻结
- 已冻结的 signal expression 轴被重新当作 train 搜索轴
- neutralization 存在但没有独立合同
- rebalance / lag / overlap 口径未冻结
- 在 train 内直接用收益最大化选 final winner

## 审查清单

阶段检查项：
- [blocking] winsorize、standardize、missing fill 和 coverage floor 口径已冻结
- [blocking] neutralization policy、beta estimation window 和 group taxonomy reference 已冻结
- [blocking] bucket schema、quantile count、tie-break rule 和 min names per bucket 已冻结
- [blocking] rebalance frequency、signal lag 和 overlap policy 已冻结
- [blocking] train variant ledger 与 reject ledger 均已保存，且可解释拒绝原因；若 inherited variant 试图改变已冻结的 signal axis，reject ledger 必须显式说明应重开 csf_signal_ready
- [blocking] 未根据 test/backtest 结果回写 train freeze
- [blocking] frozen_signal_contract_reference、train_governable_axes、non_governable_axes_after_signal 与非可调轴拒绝规则已冻结
- [reservation] search governance 只用于排除荒谬区间或不可研究 variant，不得以收益最大化方式选胜者
- [blocking] candidate_variant_ids、kept_variant_ids 与 train_governable_axes 均已显式冻结，不能空着进入 test
- [blocking] train_factor_quality 非空，且 train_variant_ledger 在 variant_id 上唯一

## 仅审计项

仅审计项:
- train 尺子命名是否清楚
- reject ledger 是否可追踪

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_train_freeze
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正 train 口径与 reject 记账
- 以下情况必须开 child lineage：预处理语义改变
- 以下情况必须开 child lineage：neutralization 大类改变

## 本阶段下游权限

- 可进入下游阶段：csf_test_evidence
- 下游可直接消费的冻结产物：csf_train_freeze.yaml
- 下游可直接消费的冻结产物：train_factor_quality.parquet
- 下游可直接消费的冻结产物：train_variant_ledger.csv
- 下游不得消费 / 重估：未冻结的 train 搜索轨迹

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
