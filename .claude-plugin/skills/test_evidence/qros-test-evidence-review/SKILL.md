---
name: qros-test-evidence-review
description: Claude Code review skill for Test Evidence stage verification.
---

# Test Evidence 审查

## 用途

用独立测试窗验证冻结后的统计结构，并冻结白名单与 best_h

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个独立 review session
- 进入本 skill 后，必须在**当前会话**里用 通过 `.claude-plugin/agents/qros-reviewer.md` 创建 task 拉起独立 reviewer 子代理，子代理上下文由 Claude Code 平台隔离保证
- 先用一个最小初始化消息创建 reviewer 子代理，要求它先等待 binding / handoff，不要在 receipt 写出前擅自写文件
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare --reviewer-agent-id <child_agent_id> --reviewer-id <reviewer_identity> --reviewer-session-id <child_agent_id> --host claude-code`
- `qros-review-cycle prepare` 负责注册 active review cycle，写出 `review/request/*` 与 `reviewer_receipt.yaml`，并输出 reviewer handoff prompt 与 closer command
- 主线程随后必须用 将 handoff manifest 作为 task prompt 传入 把 request / handoff manifest / stage-specific gate 交给 reviewer 子代理
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/reviewer_findings.raw.yaml`
- reviewer 子代理不得修改 `author/formal/*`
- reviewer 子代理完成后，主线程必须运行 `./.qros/bin/qros-review`；它负责 canonical result、audit 与 closure

## 主线程交接前提

- 主线程在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- 主线程交给 reviewer 子代理的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- handoff 必须与 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths` 一致
- 如果上一轮 verdict 是 `FIX_REQUIRED`，主线程必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，只在 author lane 修复，再显式重新进入本 stage review skill
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替主线程猜测或补齐上下文
- 进入 reviewer lane 前必须先完成 deterministic review-ready 自查；若 preflight 有 blocking finding，必须先修 author outputs。

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- signal_ready frozen timeseries
- train_thresholds.json
- train_param_ledger.csv
- data_ready aligned bars
- mandate time_split.json

## 必需输出

必需输出:
- report_by_h.parquet
- symbol_summary.parquet
- admissibility_report.parquet
- test_gate_table.csv
- crowding_review.md
- selected_symbols_test.csv
- selected_symbols_test.parquet
- frozen_spec.json
- test_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Test Evidence

正式门禁摘要：
必须全部满足：
- 仅使用 Train 已冻结的 thresholds、regime cuts 和保留对象
- formal gate 与 audit gate 已显式分开记录
- selected_symbols_test 与 best_h 已冻结
- 若 formal gate 直接引用 t 值、p 值、回归显著性或残差型证据，已记录稳健推断口径或免做理由
- 若 formal gate 依赖残差近似独立、原始 OLS 误差设定，或用“未见明显 serial correlation”支撑结论，已记录自相关诊断 protocol 或免做理由
- 若 formal gate 依赖多变量回归里单个系数的符号、显著性或增量解释，已记录多重共线性诊断 protocol 或免做理由
- 若 formal gate 把跨窗口关系连续性、回归系数稳定性、lead-lag 结构或 threshold 机制延续作为通过依据，已记录结构突变检验 protocol 或免做理由
- 若 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，已记录防虚假回归 protocol 或免做理由
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 在 test 窗里重估 train 阈值
- 看了 backtest 再回写 test 白名单但没有 retry 记账
- 把未经说明的原始 OLS 显著性直接作为 formal gate 通过依据
- 把残差近似独立、原始 OLS 误差设定或“未见明显 serial correlation”直接作为 formal gate 通过依据，却没有说明自相关诊断 protocol 或免做理由
- 把多变量回归里单个系数的符号、显著性或增量解释直接作为 formal gate 通过依据，却没有说明多重共线性诊断 protocol 或免做理由
- 把跨窗口关系连续性或系数稳定性直接作为 formal gate 通过依据，却没有说明结构突变检验 protocol 或免做理由
- 把可能非平稳的 level-series 回归、长期均衡关系或 spread mean-reversion 直接作为 formal gate 通过依据，却没有说明防虚假回归 protocol 或免做理由
- 没有 frozen_spec 就把对象交给 Backtest

## 审查清单

阶段检查项：
- [blocking] Test 使用的阈值完全来自 Train 冻结对象
- [blocking] formal gate 与 audit-only 已分开记录
- [blocking] 统计证据在独立样本上计算，未在 test 重估训练尺子
- [blocking] 白名单、best_h 或后续候选集已冻结
- [blocking] 未看了 Backtest 再回写 Test 白名单
- [blocking] 若 formal gate 引用了 t 值、p 值、回归显著性或残差型证据，已写明稳健推断口径或免做理由
- [blocking] 若 formal gate 依赖残差近似独立、原始 OLS 误差设定，或用“未见明显 serial correlation”支撑结论，已记录自相关诊断 protocol 或免做理由
- [blocking] 若 formal gate 依赖多变量回归里单个系数的符号、显著性或增量解释，已记录多重共线性诊断 protocol 或免做理由
- [blocking] 若 formal gate 把跨窗口关系连续性、回归系数稳定性或 lead-lag 结构延续作为通过依据，已记录结构突变检验 protocol 或免做理由
- [blocking] 若 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，已记录防虚假回归 protocol 或免做理由
- [reservation] 若有条件分层分析，其定位为 audit evidence 或已明确冻结为正式 gate
- [reservation] 若做了自相关诊断，已说明 Durbin-Watson、Breusch-Godfrey LM、Ljung-Box 或同类方法的适用边界与结论
- [reservation] 若做了多重共线性诊断，已说明 VIF、condition number 或同类方法的适用边界与结论
- [reservation] 若做了结构突变或参数稳定性审计，已区分 regime mismatch、样本问题与机制失效
- [reservation] 若做了单位根、协整或防虚假回归诊断，已说明 ADF、Phillips-Perron、KPSS、Engle-Granger、Johansen 或同类方法的适用边界与结论

## 仅审计项

仅审计项:
- HAC t 值
- 异方差/自相关稳健性说明（例如 Newey-West、White、Breusch-Pagan）
- 自相关诊断（例如 Durbin-Watson、Breusch-Godfrey LM、Ljung-Box）
- 多重共线性诊断（例如 VIF、condition number、pairwise correlation matrix）
- 结构突变检验或参数稳定性审计（例如 Chow、Bai-Perron、CUSUM、rolling coefficient stability）
- 防虚假回归与非平稳处理说明（例如 ADF、Phillips-Perron、KPSS、Engle-Granger、Johansen、returns/differencing）
- monotonic score
- 条件分层分析
- crowding overlap 与 factor distinctiveness 审计
- 高低波与下跌切片

## 本阶段 Rollback 规则

- 默认 rollback stage：test_evidence
- 允许修改：统计检验实现
- 允许修改：frozen spec 生成
- 允许修改：admissibility 聚合
- 以下情况必须开 child lineage：升级新的辅助条件层为正式机制
- 以下情况必须开 child lineage：想改变 formal gate 本身

## 本阶段下游权限

- 可进入下游阶段：backtest_ready
- 下游可直接消费的冻结产物：selected_symbols_test.csv
- 下游可直接消费的冻结产物：selected_symbols_test.parquet
- 下游可直接消费的冻结产物：frozen_spec.json
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h
- 下游不得消费 / 重估：formal gate thresholds

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 通过 `.claude-plugin/agents/qros-reviewer.md` 创建 task 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 将 handoff manifest 作为 task prompt 传入 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
