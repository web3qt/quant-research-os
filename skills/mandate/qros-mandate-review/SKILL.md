---
name: qros-mandate-review
description: Codex review skill for Mandate stage verification.
---

# Mandate 审查

## 用途

冻结研究主问题、时间边界、universe、字段层级和参数边界

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
- 研究主题说明或专题草稿
- 候选 universe 与时间边界提案
- 字段族、公式模板、实现栈和并行计划提案

## 必需输出

必需输出:
- mandate.md
- research_scope.md
- time_split.json
- parameter_grid.yaml
- run_config.toml
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Mandate

正式门禁摘要：
必须全部满足：
- 研究主问题与明确禁止事项已冻结
- 正式时间窗、切分方式、time label 和 no-lookahead 约定已冻结
- 正式 universe、准入口径和字段分层已冻结
- 参数字典、公式模板、实现栈、parallelization_plan 和 non_rust_exceptions 已写清
- 后续 crowding distinctiveness review 的比较基准，以及 capacity review 的流动性代理、参与率边界和自冲击假设边界已写清
- required_outputs 全部存在，且 machine-readable artifact 都能追到 companion field documentation
以下任一情况都不得出现：
- required_outputs 缺失
- 时间窗、universe 或无前视边界未冻结
- 只有裸字段名或裸参数名，没有字段解释和参数字典
- 研究问题被后验结果倒逼修改但没有重置 mandate

## 审查清单

阶段检查项：
- [blocking] 研究主问题已冻结，且明确写清不研究什么
- [blocking] 正式时间窗与 Train/Test/Backtest/Holdout 切分已冻结
- [blocking] Universe、准入口径、主副腿角色已冻结
- [blocking] 字段分层已写清，且关键字段具有人类可读解释
- [blocking] 信号表达式模板、时间语义和无前视约定已写清
- [blocking] 参数字典、参数候选集、参数约束已写清
- [reservation] 实现栈、并行计划、非 Rust 例外说明已记录
- [blocking] 若关键字段或参数仅列名称未解释，则不得通过
- [blocking] 若 research_route = cross_sectional_factor，则 factor_role、factor_structure、portfolio_expression、neutralization_policy 已冻结；且 non-standalone 需要 target_strategy_reference，group_neutral 需要 group_taxonomy_reference

## 仅审计项

仅审计项:
- 专题样板写法是否足够清楚
- 字段命名是否优雅或便于新成员阅读

## 本阶段 Rollback 规则

- 默认 rollback stage：mandate
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正字段解释、参数字典和目录契约
- 以下情况必须开 child lineage：主问题改变
- 以下情况必须开 child lineage：universe 改变
- 以下情况必须开 child lineage：time split 改变
- 以下情况必须开 child lineage：机制模板改变

## 本阶段下游权限

- 可进入下游阶段：data_ready
- 可进入下游阶段：csf_data_ready
- 下游可直接消费的冻结产物：time_split.json
- 下游可直接消费的冻结产物：parameter_grid.yaml
- 下游可直接消费的冻结产物：run_config.toml
- 下游不得消费 / 重估：test results
- 下游不得消费 / 重估：backtest results
- 下游不得消费 / 重估：holdout results

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
