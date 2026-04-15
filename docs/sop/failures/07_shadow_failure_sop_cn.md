# 07_shadow_failure_sop

Doc ID: SOP-SHADOW-FAILURE-v1.0
Title: `07_shadow_failure_sop` — Shadow 阶段失败处置标准操作流程（机构级）
Date: 2026-03-23
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Trading / Reviewer / Referee / Portfolio Review
Audience:
- Research
- Quant Dev
- Trading
- Reviewer / Referee
- Portfolio Review
Depends On:
- `research_workflow_master_spec`
- `00_mandate`
- `01_data_ready`
- `02_signal_ready`
- `03_train_freeze`
- `04_test_evidence`
- `05_backtest`
- `06_holdout`
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `07_shadow` 阶段未通过时，团队应如何冻结失败、区分研究问题与真实执行问题、决定是否允许继续孵化，以及何时必须降级、回退或停线。**

它不是“把 shadow 当成无限期优化池”的说明书。
它是 `07_shadow` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有已经通过 holdout、并进入接近真实交易条件验证的研究线，包括：

- 准实盘收益 / 风险 / 滑点 / 容量审计
- 下单、成交、撤单、风控、监控链路一致性审计
- 实时数据、时钟、延迟、API 稳定性审计
- shadow 与 `05_backtest` / `06_holdout` 的偏差归因

只要本阶段需要回答“一个已经通过 holdout 的候选，在接近真实交易条件、真实延迟、真实成交、真实容量与真实运营流程下是否仍具备上线价值”，本 SOP 就适用。

---

# 3. 阶段职责

`07_shadow` 的职责不是再研究 alpha，而是：

1. 在接近实盘的条件下验证信号、执行器、风控器、下单路径、监控链路是否一致工作；
2. 评估 shadow 与 `05_backtest / 06_holdout` 的偏差来源；
3. 检查成交质量、容量、滑点、时延、下单失败与告警是否可控；
4. 为正式 seed / production 给出运营层证据。

因此，`07_shadow` 失败通常意味着：

- 运营 / 基础设施 / 流程问题；
- 执行质量不足；
- 容量不足；
- 或真实世界条件下主假设不再成立。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `07_shadow_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- shadow 账户级收益显著偏离 `06_holdout` 预期分布；
- 净收益为负或显著低于上线门槛；
- 风险指标显著恶化；
- 实际滑点显著高于回测 / holdout 假设；
- 订单未成交、部分成交、排队损失显著；
- 容量稍放大即明显劣化；
- 数据链路、风控链路、监控链路频繁异常；
- shadow 实际交易行为与 backtest / holdout 合同严重不一致；
- 为了让 shadow 成立，必须改变研究主问题、执行语义或策略身份。

## 4.2 软性失败（需 Referee 判断）

- shadow 主结论已清楚，但 execution drift、ops incident 或 compare sidecar 不完整；
- reviewer 认可主要问题，但 referee 无法区分当前偏差是运营问题还是研究问题；
- 当前失败看起来可修，但未形成清晰 rollback 边界。

软性失败仍必须进入 harness，先冻结，再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

同时必须给出一个运行状态：

- `continue_shadow`
- `pause_shadow`
- `terminate_shadow`

---

# 5. 失败分类

`07_shadow` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `OPS_FAIL`

Shared layer: `IMPLEMENTATION`

定义：当前失败首先来自运营、基础设施或流程问题，而不是策略本身。

典型表现：
- 数据源抖动、消息丢失、时钟不同步；
- API 不稳定、下单失败率高、状态回报异常；
- 监控告警失灵；
- 订单 / 成交日志无法完整复原；
- 同策略逻辑在 replay 中正常，但 shadow 中异常。

## 5.2 `EXECUTION_FAIL`

Shared layer: `IMPLEMENTATION`

定义：研究与 holdout 仍有一定依据，但真实执行质量不足以支撑上线。

典型表现：
- 实际滑点显著高于假设；
- 队列损失、部分成交、撤单成本明显；
- 下单路径导致交易延迟错过主要 alpha 窗口；
- 实际净收益被执行损耗吃掉。

## 5.3 `CAPACITY_FAIL`

Shared layer: `THESIS`

定义：策略在小规模影子仓位下可行，但在接近目标规模时容量不足，无法经济上线。

典型表现：
- shadow 小规模正常，稍放大后明显恶化；
- 某些时段或 symbol 无法承接目标仓位；
- 市场冲击、排队与流动性约束显著超出预期；
- 容量瓶颈而非 alpha 消失。

## 5.4 `GENERALIZATION_FAIL`

Shared layer: `THESIS`

定义：策略在 holdout 通过，但在接近真实交易环境后，alpha 行为本身无法重现。

典型表现：
- 不是单纯执行或容量问题，而是连 gross 也明显弱化；
- 实时环境中 trade distribution 与 holdout 差异过大；
- 真实盘口、真实延迟条件下核心结构消失；
- shadow 暴露出 holdout 仍高估了可实现 alpha。

## 5.5 `THESIS_FAIL`

Shared layer: `THESIS`

定义：shadow 表明该策略在接近真实世界条件下不具备上线价值，主假设实质失效。

典型表现：
- 多轮修复后仍不具经济意义；
- alpha 太薄，无法覆盖真实执行摩擦；
- 需要大量补丁才能勉强存活；
- 当前线在运营层已不具继续价值。

## 5.6 `SCOPE_FAIL`

Shared layer: `SCOPE`

定义：若要让 shadow 成立，必须改变研究主问题、执行语义、风控角色或策略身份。

典型表现：
- 从 alpha 线改成 execution-only 线；
- 从主策略改成组合辅助信号；
- 从原下单语义改成完全不同执行器；
- 从“风险过滤器”变成“主信号门控器”。

---

# 6. 标准处置总原则

`07_shadow` 失败后，必须遵守下面六条原则：

1. **先冻结 shadow 失败，再解释偏差来源**；
2. **先区分运营问题与策略问题，再讨论继续孵化**；
3. **不允许把 shadow 当成第三次开发层**；
4. **不允许用 shadow 结果反向改写 `03/04/05/06` 冻结对象**；
5. **修复后的 shadow 必须与同一冻结合同可比较**；
6. **任何改变研究身份的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，必须冻结：

- shadow 时间边界
- 代码 / 配置 / 模型版本
- 实时数据版本与订阅源
- 下单参数
- 风控参数
- 资金规模
- 订单日志、成交日志、告警日志
- 与 `05_backtest / 06_holdout` 的偏差对比
- 已知异常

至少产出：

- `shadow_failure_freeze.md`
- `shadow_vs_holdout_compare.parquet`
- `execution_drift_report.md`
- `ops_incident_log.md`
- `repro_manifest.json`
- `review_notes.md`

## Step 1. 先排运营与执行 correctness

固定顺序检查：

1. 数据链路是否完整；
2. 下单与成交日志是否可重建；
3. 时钟 / 延迟 / API / 风控是否正常；
4. 订单状态机是否符合合同；
5. 关键交易样本是否可复盘；
6. 当前偏差是运营问题、执行问题还是策略问题。

若失败：

- 基础设施 / 流程问题 -> `OPS_FAIL`
- 执行器 / 下单质量问题 -> `EXECUTION_FAIL`

## Step 2. 再做运营层归因

只有 correctness 过关，才允许继续判断：

- 放大后劣化、目标规模不可行 -> `CAPACITY_FAIL`
- 真实环境下连 gross 都明显弱化 -> `GENERALIZATION_FAIL`
- 多轮后仍无上线价值 -> `THESIS_FAIL`

## Step 3. 研究边界审计

检查 shadow 是否被拿来偷偷换题：

- 是否把主策略降级成辅助信号；
- 是否改写执行语义、风控角色或策略身份；
- 是否让新的过滤器成为主 gate；
- 是否以“运营修复”为名重写 alpha 身份。

若发生上述行为：

- 归类为 `SCOPE_FAIL`
- 停止原线推进

## Step 4. 映射 formal decision 与 shadow status

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限 shadow 主结论已清楚，但 ops / drift sidecar 或 review 闭环不完整
- `RETRY`
  适用于当前或更早阶段可受控修复的运营、执行或 compare 问题
- `NO-GO`
  适用于真实世界条件下不具上线价值
- `CHILD LINEAGE`
  适用于修复动作已经改变研究主问题、执行语义或策略身份

同时必须给出一个 shadow status：

- `continue_shadow`
- `pause_shadow`
- `terminate_shadow`

说明：

- `RESEARCH_AGAIN` 可以作为解释性 prose 出现
- 但正式输出必须翻译成 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 默认 formal decision | 默认 shadow_status |
|---|---:|---|---|
| `OPS_FAIL` | `07_shadow` | `PASS FOR RETRY` 或 `RETRY` | `pause_shadow` |
| `EXECUTION_FAIL` | `07_shadow` | `RETRY` | `pause_shadow` |
| `CAPACITY_FAIL` | `07_shadow` 或 `00_mandate` | `RETRY`、`NO-GO` 或 `CHILD LINEAGE` | `pause_shadow` 或 `terminate_shadow` |
| `GENERALIZATION_FAIL` | `05_backtest` 或 `06_holdout` | `RETRY` 或 `NO-GO` | `pause_shadow` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` | `terminate_shadow` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` | `terminate_shadow`（原线） |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- 需要把 alpha 线改成 execution-only 线；
- 需要把主策略降级成辅助信号；
- 需要改写执行语义、风控角色或策略身份；
- 需要用同一份 shadow 结果同时证明两条不同策略。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于合法回退边界内时，允许修改：

- 数据链路、下单链路、监控告警、日志与复盘工具
- 下单节奏、订单类型、撤单与重试策略
- 成本模型与 execution drift 审计
- 容量门槛、session / liquidity bucket 约束
- 合法回退到 `05/06` 重审真实可执行条件与样本外证据

## 9.2 禁止修改

在 `07_shadow_failure_sop` 中，默认禁止：

- 用 shadow 结果反向定义 alpha；
- 静默替换 `03/04/05/06` 冻结对象；
- 把 shadow 当成无限优化池；
- 借运营修复之名重写策略身份；
- 跳过失败冻结，直接覆盖旧结果。

---

# 10. Retry 纪律

`07_shadow` 允许 retry，但必须更严格。

每次 retry 必须写明：

1. `failure_class`
2. `root_cause_hypothesis`
3. `rollback_stage`
4. `allowed_modifications`
5. `forbidden_modifications`
6. `expected_improvement`
7. `unchanged_contracts`

示例：

```yaml
failure_class: EXECUTION_FAIL
root_cause_hypothesis: 实际滑点显著高于假设，当前失败主因是执行质量而非 alpha 失效
rollback_stage: 07_shadow
allowed_modifications:
  - adjust_order_type
  - tune_submission_pacing
  - regenerate_execution_drift_report
forbidden_modifications:
  - redefine_alpha_in_shadow
  - change_whitelist_or_best_h
  - change_strategy_identity
expected_improvement:
  - realized slippage returns inside approved envelope
  - fill rate improves materially
  - net pnl retention improves without changing strategy identity
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - shadow_risk_role
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- 超过次数仍无改善，应升级为 `NO-GO` 或 `CHILD LINEAGE`；
- 不允许让 shadow 变成另一个 backtest。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `shadow_failure_freeze.md`
- `shadow_vs_holdout_compare.parquet`
- `execution_drift_report.md`
- `ops_incident_log.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee / Trading 审核点

Reviewer / Trading 至少要审：

1. shadow 失败是否已被完整冻结？
2. 是否已区分运营故障与策略故障？
3. 是否已区分执行质量问题与 alpha 泛化问题？
4. 容量问题是否被单独识别？
5. 实际滑点与假设偏差是否量化？
6. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 当前失败是运营问题、执行问题、容量问题、泛化问题还是主假设失效？
2. shadow 是否被误用为调参池？
3. 是否已经达到必须开 child lineage 的条件？
4. formal decision 与 shadow status 是否符合治理纪律？

---

# 13. 与 Topic A / Topic C 的落地备注

若当前研究为 Topic A / Topic C 线，`07_shadow` 额外必须检查：

- `topicA` 的结构结论是否被错误当成实时交易结论；
- `topicC-3A` 在 shadow 上失败究竟是执行质量、容量问题，还是主假设失效；
- 当前退出语义与风控器是否仍保持 `05/06` 冻结身份；
- 若要把策略降级成“组合辅助子信号”或“小容量专用线”，是否已经承认这是新谱系；
- 若真实成交质量长期显著差于假设，是否应升级为 `THESIS_FAIL`。

---

# 14. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示。

同时必须输出一个 shadow status。

## 14.1 `PASS FOR RETRY`

条件：

- shadow 主结论已清楚；
- 仅缺 execution drift、ops incident 或 reviewer 闭环；
- 不需要改变研究身份。

## 14.2 `RETRY`

条件：

- 问题明确；
- 回退层级清晰；
- 修复不改变研究身份。

## 14.3 `NO-GO`

条件：

- 接近真实世界条件下不具备上线价值；
- 多轮合法修复后仍无继续价值；
- 当前线不值得继续投入。

## 14.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变研究主问题、执行语义、风控角色或策略身份；
- 需要开新谱系来保持治理清洁。

## 14.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段重做合法运营 / 执行证据链 -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线真实可执行性不足，不值得继续 -> `NO-GO`
- 修复已经变成新问题 -> `CHILD LINEAGE`

## 14.6 Shadow Status

- `continue_shadow`
  仅限偏差轻微、问题边界清晰且不需要暂停运行
- `pause_shadow`
  当前需要暂停孵化，先修复再继续
- `terminate_shadow`
  原线 shadow 终止，不再继续运行

---

# 15. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出 formal decision 与 shadow status；
- 若允许 retry，已提供受控 retry 计划；
- reviewer / referee / trading 可以依据产物复建同一份 shadow 结论。

---

# 16. 一句话总结

`07_shadow` 失败后的标准动作，不是“继续把模拟盘跑着顺手优化”，而是：

**先冻结失败，再判断它是运营故障、执行质量不足、容量不足、泛化失败、主假设失效还是已经换题；随后只在合法回退边界内受控修复，任何把 shadow 变成第三次开发层的动作都必须被拒绝。**
