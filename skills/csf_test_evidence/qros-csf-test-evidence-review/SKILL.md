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

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个 Codex review session
- 进入本 skill 后，必须在**当前会话**里用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`
- 先用一个最小初始化消息创建 reviewer 子代理，要求它先等待 binding / handoff，不要在 receipt 写出前擅自写文件
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare --spawned-agent-id <child_agent_id> --reviewer-id <reviewer_identity> --reviewer-session-id <child_agent_id>`
- `qros-review-cycle prepare` 负责注册 active review cycle，写出 `review/request/*` 与 `spawned_reviewer_receipt.yaml`，并输出 reviewer handoff prompt 与 closer command
- 主线程随后必须用 `send_input` 把 request / handoff manifest / stage-specific gate 交给 reviewer 子代理
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

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
