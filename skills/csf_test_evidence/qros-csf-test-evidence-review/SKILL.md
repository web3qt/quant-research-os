---
name: qros-csf-test-evidence-review
description: Codex review skill for CSF Test Evidence stage verification.
---

# CSF Test Evidence 审查

## 用途

在独立样本里验证截面因子排序能力或 filter / combo 条件改善能力

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
- 已冻结的 csf_train_freeze 输出
- 独立测试窗
- factor_role / target_strategy_reference

## 必需输出

必需输出:
- csf_test_gate_table.csv
- csf_selected_variants_test.csv
- csf_test_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Test Evidence

正式门禁摘要：
必须全部满足：
- 只复用 csf_train_freeze 的 frozen rules
- `standalone_alpha` 使用 Rank IC / ICIR / bucket spread / monotonicity / breadth / stability
- `regime_filter / combo_filter` 使用 gated vs ungated 改善证据
- 全量 test ledger 保留
- selected / rejected variants 有显式记账
以下任一情况都不得出现：
- test 内重估 train 尺子
- 新增未冻结 variant
- 看 backtest 后回写 selected_variants_test
- 只保留通过者，不保留全量 ledger
- 搜索量较大却不做 multiple testing 校正

## 审查清单

阶段检查项：
- [blocking] standalone_alpha 场景下，Rank IC、ICIR、分组收益、单调性、breadth 和子窗口稳定性均已检查
- [blocking] regime_filter / combo_filter 场景下，target strategy reference 和 gated vs ungated 对比已冻结
- [blocking] test 使用的 preprocess、neutralization、bucket 和 rebalance 规则全部来自 train freeze
- [blocking] selected variants 和 rejected variants 都已保留，并可追溯决策理由
- [blocking] 未在 test 重估 train 尺子，也未新增未冻结的 variant
- [blocking] 若使用 filter 语义，check 结果体现条件改善而不是独立赚钱
- [reservation] 若存在多重测试或多个候选 variant，已保留完整 ledger 而非只保留通过项
- [blocking] standalone_alpha 场景下，mean_rank_ic <= 0 不得放行到下一阶段

## 仅审计项

仅审计项:
- 证据表述是否足以让 reviewer 读懂角色差异
- 样本覆盖是否解释充分

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_test_evidence
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正证据表述
- 以下情况必须开 child lineage：factor_role 变化导致证据语义改变
- 以下情况必须开 child lineage：证据本体从截面排序改为别的任务

## 本阶段下游权限

- 可进入下游阶段：csf_backtest_ready
- 下游可直接消费的冻结产物：csf_selected_variants_test.csv
- 下游可直接消费的冻结产物：csf_test_contract.md
- 下游不得消费 / 重估：未冻结的 test 搜索轨迹

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
