# 06_holdout_failure_sop

Doc ID: SOP-HOLDOUT-FAILURE-v1.0
Title: `06_holdout_failure_sop` — Holdout 阶段失败处置标准操作流程（机构级）
Date: 2026-03-23
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Reviewer / Referee / Portfolio Review
Audience:
- Research
- Quant Dev
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
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `06_holdout` 阶段未通过时，团队应如何冻结失败、判断是否属于泛化失败、隔离选择偏差影响、决定是否终止原线，并输出可审计结论。**

它不是“在最终保留样本上继续找参数”的说明书。
它是 `06_holdout` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有已经完成：

- `00_mandate`
- `01_data_ready`
- `02_signal_ready`
- `03_train_freeze`
- `04_test_evidence`
- `05_backtest`

并进入最终保留样本审计的研究线。

只要本阶段需要回答“一个已经通过 `05_backtest` 的候选，在真正未参与研发、未参与调参、未参与执行收敛的数据上是否仍然成立”，本 SOP 就适用。

---

# 3. 阶段职责

`06_holdout` 的职责不是再开发，而是：

1. 在严格隔离的最终保留样本上验证策略泛化能力；
2. 检查样本内、test、backtest 与 holdout 之间的一致性；
3. 识别选择偏差、后验调参、脆弱参数峰值与流程污染；
4. 为 `07_shadow` 提供最终样本外证据。

因此，`06_holdout` 失败通常意味着：

- holdout 纯度被破坏；
- 泛化能力不足；
- 当前结果是孤峰而不是高原；
- 或研究问题已经迁移。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `06_holdout_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- holdout 账户级 `total_return <= 0` 或 `net_pnl_sum <= 0`；
- 核心风险调整指标显著低于晋级门槛；
- 与 `05_backtest` 相比出现断崖式退化；
- holdout 上核心统计结构消失或方向反转；
- 当前冻结参数点仅在 holdout 上呈现孤峰，不形成邻域平台；
- holdout 暴露前序通过主要来自多次试错后的幸存者偏差；
- holdout 数据边界被破坏，或 holdout 被提前看过、提前用过；
- 要让 holdout 通过，必须实质性改变研究问题或策略身份。

## 4.2 软性失败（需 Referee 判断）

- holdout 主结论清楚，但 compare sidecar、purity audit、review 闭环不完整；
- reviewer 认可主结论，但 referee 无法确认 holdout 是否真的保持独立；
- 当前失败像是流程纯度问题，但尚未定位污染起点。

软性失败仍必须进入 harness，先冻结，再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

---

# 5. 失败分类

`06_holdout` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `PURITY_FAIL`

Shared layer: `INTEGRITY`

定义：holdout 的独立性、隔离性或复现性被破坏，当前结果不具审计效力。

典型表现：
- holdout 时间边界提前泄漏；
- holdout 曾被用于挑参数、挑 sibling、挑执行器；
- holdout 结果无法独立复现；
- 上游冻结对象在进入 holdout 前被替换。

## 5.2 `GENERALIZATION_FAIL`

Shared layer: `THESIS`

定义：前序阶段看起来有效，但在真正未参与研发的数据上无法泛化。

典型表现：
- `05_backtest` 尚可，但 holdout 断崖式下降；
- gross / net 同时弱化；
- 交易分布、收益结构、持仓行为与此前显著不同；
- 不是成本略恶化，而是整体边际消失。

## 5.3 `FRAGILITY_FAIL`

Shared layer: `THESIS`

定义：holdout 暴露策略依赖极窄参数点、极脆弱执行点或极偶然市场片段。

典型表现：
- 当前冻结参数稍微偏移即显著恶化；
- 邻域参数与当前参数结果断崖差异；
- 微调成本、持有期、阈值就崩；
- sibling lineages 没有稳定平台，只有孤峰。

## 5.4 `SELECTION_BIAS_FAIL`

Shared layer: `INTEGRITY`

定义：当前 holdout 结果暴露前序通过主要来自多次试错后的选择偏差。

典型表现：
- 当前赢家在 holdout 上集体失效；
- 当前版本只是此前大量变体的幸存者；
- 记录不清试过多少变体、筛过多少切片；
- holdout 排名与此前最优排序严重不一致。

## 5.5 `THESIS_FAIL`

Shared layer: `THESIS`

定义：跨样本、跨阶段地看，主假设已不具备继续价值。

典型表现：
- 多轮修复后仍然无法泛化；
- 需要大量补丁才能勉强存活；
- 当前线在最终保留样本上已不具研究价值。

## 5.6 `SCOPE_FAIL`

Shared layer: `SCOPE`

定义：若要让 holdout 成立，必须改变研究主问题、Universe、执行语义或策略身份。

典型表现：
- 把主策略降级成辅助信号；
- 改变 Universe、持有期、side contract 才能过线；
- 用 holdout 结果推动新线身份而不留痕。

---

# 6. 标准处置总原则

`06_holdout` 失败后，必须遵守下面六条原则：

1. **先冻结 holdout 失败，再讨论任何解释**；
2. **先检查 holdout 纯度，再讨论泛化能力**；
3. **不允许把 holdout 当作第二次调参集**；
4. **不允许用 holdout 结果反向改写上游冻结对象**；
5. **修复后的 holdout 必须保持真正隔离、可复现、可审计**；
6. **任何改变研究身份的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，必须冻结：

- holdout 时间边界
- 代码版本 / commit
- 数据版本
- Universe
- 所有冻结对象来源
- 执行配置
- 账户级结果
- 与 `05_backtest` 的对比结果
- 已知异常

至少产出：

- `holdout_failure_freeze.md`
- `holdout_vs_backtest_compare.parquet`
- `purity_audit.md`
- `repro_manifest.json`
- `review_notes.md`

## Step 1. 先检查流程纯度

固定顺序：

1. holdout 是否被提前接触过；
2. holdout 是否真的未参与 freeze / selection / execution tuning；
3. 时间边界是否被污染；
4. 当前 run 是否可复现；
5. 上游冻结对象是否被私下替换。

若失败：

- 优先归类为 `PURITY_FAIL`
- 当前 holdout 结果不具审计效力

## Step 2. 再做泛化归因

只有流程纯度过关，才允许继续判断：

- 前序可做，但 holdout 断崖 -> `GENERALIZATION_FAIL`
- 当前参数是孤峰，不具平台 -> `FRAGILITY_FAIL`
- 当前通过主要来自前序筛选幸存者 -> `SELECTION_BIAS_FAIL`
- 跨样本看机制已不成立 -> `THESIS_FAIL`

## Step 3. 研究边界审计

检查 holdout 是否被拿来偷偷换题：

- 是否因为 holdout 失败就改 Universe 或持有期；
- 是否把主策略降级成辅助信号；
- 是否用 holdout 结果推动新风控、新执行语义成为主问题。

若发生上述行为：

- 归类为 `SCOPE_FAIL`
- 停止原线推进

## Step 4. 映射 formal decision

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限 holdout 主结论已清楚，但 purity audit、compare sidecar 或 review 闭环不完整
- `RETRY`
  适用于 holdout 纯度 / 复现问题，或存在明确上游回退目标且修复不改变研究身份
- `NO-GO`
  适用于泛化失败、脆弱性暴露或主假设失效
- `CHILD LINEAGE`
  适用于修复动作已经改变研究问题、Universe、执行语义或策略身份

说明：

- `RESEARCH_AGAIN` 可以作为解释性 prose 出现
- 但正式输出必须翻译成 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---:|---|
| `PURITY_FAIL` | `05_backtest` 或更早 | `PASS FOR RETRY` 或 `RETRY` |
| `GENERALIZATION_FAIL` | `04_test_evidence` 或 `05_backtest` | `RETRY` 或 `NO-GO` |
| `FRAGILITY_FAIL` | `03_train_freeze` 或 `04_test_evidence` | `RETRY` 或 `NO-GO` |
| `SELECTION_BIAS_FAIL` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- 需要改变 Universe、持有期、执行语义或策略身份；
- 需要把主策略降级成辅助信号；
- 需要把 holdout 暴露出的 regime / risk filter 升格成新主问题；
- 需要改写原 freeze contract 才能“过 holdout”。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于合法回退边界内时，允许修改：

- purity audit、边界隔离、repro 链
- holdout compare 与 review sidecar
- 合法回退到 `04/05` 重审证据与交易可行性
- 合法回退到 `03` 重审参数高原与 freeze discipline

## 9.2 禁止修改

在 `06_holdout_failure_sop` 中，默认禁止：

- 在当前 holdout 上继续调参；
- 用 holdout 结果反向定义 whitelist、`best_h` 或主阈值；
- 重估原线冻结对象并宣称“只是微调”；
- 跳过失败冻结，直接覆盖旧结果；
- 把 holdout 变成第二次开发集。

---

# 10. Retry 纪律

`06_holdout` 默认不鼓励 retry。只有在以下场景才允许：

- `PURITY_FAIL`
- 明确的 artifact / reproduction 问题
- 当前 holdout run 因流程问题而不具审计效力

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
failure_class: PURITY_FAIL
root_cause_hypothesis: holdout 边界在 lineage 选择阶段被提前暴露，当前结果无审计效力
rollback_stage: 05_backtest
allowed_modifications:
  - repair_holdout_boundary
  - regenerate_purity_audit
  - rerun_holdout_with_same_frozen_contract
forbidden_modifications:
  - tune_parameters_on_holdout
  - rewrite_whitelist_from_holdout
  - change_strategy_identity
expected_improvement:
  - holdout data remains untouched before final run
  - compare artifacts are reproducible
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - time_split_except_holdout_boundary_fix
```

纪律要求：

- 同一问题默认最多允许 1 次 retry；
- retry 后仍失败，不得继续在 holdout 上做受控优化；
- 若 holdout 真正暴露了泛化问题，应升级为 `NO-GO` 或合法回退。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `holdout_failure_freeze.md`
- `holdout_vs_backtest_compare.parquet`
- `purity_audit.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee 审核点

Reviewer 至少要审：

1. holdout 失败是否已被完整冻结？
2. holdout 是否真正保持独立？
3. 当前 run 是否严格消费冻结对象？
4. 是否已区分泛化失败与成本轻微恶化？
5. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 当前失败是流程污染、泛化失败、参数脆弱、选择偏差还是主假设失效？
2. 是否错误地把 holdout 当调参集？
3. 是否已经达到必须开 child lineage 的条件？
4. formal decision 是否符合治理纪律？

---

# 13. 与 Topic A / Topic C 的落地备注

若当前研究为 Topic A / Topic C 线，`06_holdout` 额外必须检查：

- `topicA` 的结构诊断价值是否被误当成交易可做性结论；
- `topicC-3A` 在 holdout 上失败究竟是执行问题、泛化问题还是主假设失效；
- 是否有少数 symbol 或少数 regime 撑起结果；
- 是否因为 holdout 失败就想重写 `entry_z / exit_z / whitelist`；
- 若要把策略降级成辅助信号，是否已经承认这是新谱系。

---

# 14. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示：

## 14.1 `PASS FOR RETRY`

条件：

- holdout 主结论已清楚；
- 仅缺 purity audit、compare sidecar 或 reviewer 闭环；
- 不需要改变研究身份。

## 14.2 `RETRY`

条件：

- 问题明确；
- 回退层级清晰；
- 修复不改变研究身份；
- 且通常只限 purity / reproducibility 一类问题。

## 14.3 `NO-GO`

条件：

- 泛化失败、脆弱性暴露或主假设失效；
- 当前线在最终保留样本上不值得继续；
- 多轮合法回退后仍无继续价值。

## 14.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变研究主问题、Universe、执行语义或策略身份；
- 需要开新谱系来保持治理清洁。

## 14.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段重做合法样本外证据链 -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线泛化不足，不值得继续 -> `NO-GO`
- 修复已经变成新问题 -> `CHILD LINEAGE`

---

# 15. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出 formal decision；
- 若允许 retry，已提供受控 retry 计划；
- reviewer / referee 可以依据产物复建同一份 holdout 结论。

---

# 16. 一句话总结

`06_holdout` 失败后的标准动作，不是“继续在最终保留样本上找能过的版本”，而是：

**先冻结失败，再判断它是 holdout 纯度破坏、泛化失败、参数脆弱、选择偏差还是主假设失效；随后只在合法回退边界内受控修复，任何把 holdout 变成开发集的动作都必须被拒绝。**
