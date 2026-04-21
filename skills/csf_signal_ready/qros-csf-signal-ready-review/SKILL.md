---
name: qros-csf-signal-ready-review
description: Codex review skill for CSF Signal Ready stage verification.
---

# CSF Signal Ready 审查

## 用途

将已冻结的截面研究语义实例化为可比较、可复现的因子面板合同

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 Review Session 要求

- 本 skill 必须在独立 review session 中执行，不得在当前 author 会话里自动编排 reviewer
- 进入本 skill 后，第一步应在当前 review session **内部**运行 `./.qros/bin/qros-start-review`
- `qros-start-review` 会注册 active review cycle，并写出 `review/request/*`
- review session 只允许读取 `review/request/*` 与 `author/formal/*`
- review session 只允许写入 `review/result/*`
- review session 不得修改 `author/formal/*`
- reviewer 正常只写 `reviewer_findings.raw.yaml`；`./.qros/bin/qros-review` 负责 canonical result、audit 与 closure

## Author Lane 交接前提

- author lane 在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- author lane 交给 review session 的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- 如果上一轮 verdict 是 `FIX_REQUIRED`，author lane 必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，只在 author lane 修复，再由人显式重新启动 review session
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替 author lane 猜测或补齐上下文

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_data_ready 输出
- 因子表达式或多因子组合草案
- 因子方向与时间语义提案

## 必需输出

必需输出:
- factor_panel.parquet
- factor_manifest.yaml
- route_inheritance_contract.yaml
- factor_field_dictionary.md
- factor_coverage_report.parquet
- factor_contract.md
- run_manifest.json
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Signal Ready

正式门禁摘要：
必须全部满足：
- factor_id / factor_version / factor_direction 已冻结
- factor_panel 可唯一表示同一时点不同资产的因子值
- 所有输入字段都来自 csf_data_ready
- 多因子组合公式是确定性的
- 缺失值、coverage、eligibility 传递规则已写清
- 因子方向明确，不允许到 test/backtest 再解释
以下任一情况都不得出现：
- 因子定义依赖 train/test/backtest 结果回写
- factor_panel 无法稳定重建
- 多因子组合权重在后续阶段才学习
- factor_direction 不清楚
- eligibility 与 factor computation 混成一团
- test 才知道的 quantile / cutoff 被偷写回 signal

## 审查清单

阶段检查项：
- [blocking] factor_role、factor_structure、portfolio_expression、neutralization_policy 均来自 mandate 冻结；non-standalone 具备 target_strategy_reference，group_neutral 具备 group_taxonomy_reference
- [blocking] factor_id、factor_version、factor_direction 已冻结
- [blocking] factor_panel 以统一面板主键唯一表示同一时点不同资产的因子值
- [blocking] raw_factor_fields、derived_factor_fields 和 final_score_field 已写清
- [blocking] 多因子组合公式是确定性的，不依赖 train-learned weights
- [blocking] 缺失值策略、coverage contract 和 eligibility 传递规则已冻结
- [blocking] 若需要组内排序或组中性化，factor group context 已冻结
- [blocking] 不得把过滤器语义伪装成独立 alpha 语义
- [blocking] factor_direction、panel_primary_key、final_score_field 与 score_combination_formula 均已冻结，且不允许保持空缺
- [blocking] factor_panel 非空，且在 (date, asset) 上唯一

## 仅审计项

仅审计项:
- 因子命名是否足够可读
- 多因子组合描述是否清楚

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_signal_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正因子方向与组合公式
- 以下情况必须开 child lineage：因子结构从截面改为时序
- 以下情况必须开 child lineage：因子角色发生实质变化

## 本阶段下游权限

- 可进入下游阶段：csf_train_freeze
- 下游可直接消费的冻结产物：factor_panel.parquet
- 下游可直接消费的冻结产物：factor_manifest.yaml
- 下游可直接消费的冻结产物：factor_coverage_report.parquet
- 下游不得消费 / 重估：未冻结的 train 尺子

## 执行顺序

1. 在独立 review session 中，先由本 skill 内部运行 `./.qros/bin/qros-start-review`
2. 再按共享审查协议完成 shared review loop
3. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
4. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
