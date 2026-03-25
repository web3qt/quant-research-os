# 05_backtest_failure_sop

Doc ID: SOP-BACKTEST-FAILURE-v1.0
Title: `05_backtest_failure_sop` — Backtest 阶段失败处置标准操作流程（机构级）
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
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `05_backtest` 阶段未通过时，团队应如何冻结失败、完成归因、限定修改范围、决定回退阶段，并输出可审计结论。**

它不是“把回测调好看”的优化手册。
它是 `05_backtest` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于已经拥有冻结上游对象、并进入正式交易可行性审计的研究线，包括：

- 账户级收益 / 风险 / 成本审计
- 双引擎一致性校验
- 执行语义一致性与 replay 审计
- gross vs net、turnover、capacity、close reason 拆解

只要本阶段需要回答“冻结后的规则在账户级、成本后、可执行口径下是否仍具有交易经济性”，本 SOP 就适用。

---

# 3. 阶段职责

`05_backtest` 的职责不是重新发明信号，而是：

1. 只消费上游已冻结对象；
2. 验证冻结后的规则在账户级、成本后、可执行口径下是否具备交易经济性；
3. 交叉验证双引擎与执行语义的一致性；
4. 输出可审计的收益、费用、换手、持仓、关闭原因与风险画像。

因此，`05_backtest` 失败通常意味着：

- 工程或语义实现问题；
- 执行 / 成本 / 容量问题；
- 上游证据不足以支撑交易可行性；
- 或当前研究问题已经迁移。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `05_backtest_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- 账户级 `total_return <= 0` 或 `net_pnl_sum <= 0`；
- 风险调整后收益显著低于晋级阈值；
- `gross_pnl_sum > 0` 但费用、滑点、冲击吃掉全部或大部分收益；
- 关闭原因分布与研究语义严重不符；
- 双引擎或 replay 结果不一致；
- 同一配置复跑无法稳定重现；
- 回测失败暴露上游 `04_test_evidence` 证据不稳或冻结对象不一致；
- 为了让回测通过，必须实质性改变研究问题或策略身份。

## 4.2 软性失败（需 Referee 判断）

- 账户级结果勉强过线，但 engine compare、close reason、cost sensitivity sidecar 不完整；
- gross 与 net 拆解尚未闭环，无法安全晋级；
- reviewer 认可当前结果，但 referee 无法确认当前执行器是否真正消费了冻结语义。

软性失败仍必须进入 harness，先冻结，再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

---

# 5. 失败分类

`05_backtest` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `ENG_FAIL`

Shared layer: `IMPLEMENTATION`

定义：当前失败首先来自工程、实现或 correctness 问题，而不是研究本身。

典型表现：
- 双引擎结果不一致；
- 同配置复跑不一致；
- 费用单位、名义仓位、账户预算换算错误；
- 下单 / 成交 / 持仓状态机逻辑错误；
- 时间标签或进入退出时点错位。

若主要症状是非确定性，则同时落 shared layer `REPRO`。

## 5.2 `EXEC_FAIL`

Shared layer: `THESIS`

定义：统计上可能仍有边，但被冻结规则在真实账户级语义下不具备经济性。

典型表现：
- `gross_pnl_sum > 0` 但 `net_pnl_sum < 0`；
- `gross/trade` 明显低于 `fee/trade`；
- 交易次数过多、换手过高；
- capacity 或成本稍微上调就崩；
- 当前执行更像“事件持有器”而不是原研究想要的执行器。

## 5.3 `RESEARCH_FAIL`

Shared layer: `INTEGRITY`

定义：回测失败暴露出上游证据冻结不足、sample-out discipline 失守或 evidence contract 不稳。

典型表现：
- `04_test_evidence` 只在局部切片成立；
- `best_h`、白名单或 freeze discipline 被破坏；
- 当前 backtest 与上游冻结对象不一致；
- 核心机制在交易口径下无法由上游证据支撑。

## 5.4 `THESIS_FAIL`

Shared layer: `THESIS`

定义：在合理实现、合理成本与合理执行口径下，机制本身不再成立。

典型表现：
- 边际太薄，无法覆盖合理成本；
- 多轮修复后仍无经济意义；
- 策略身份被执行摩擦挤压得面目全非；
- 继续投入已不具研究价值。

## 5.5 `SCOPE_FAIL`

Shared layer: `SCOPE`

定义：为了拯救回测，必须改变研究主问题、Universe、执行语义或策略身份。

典型表现：
- 通过新增风险过滤器把策略改成另一类问题；
- 静默改变 Universe 或持有期；
- 把 alpha 线改成 execution-only 线；
- 在原线内重写退出语义并改变身份。

---

# 6. 标准处置总原则

`05_backtest` 失败后，必须遵守下面六条原则：

1. **先冻结失败，不解释**；
2. **先排 correctness，再谈经济性**；
3. **先拆 gross vs net，再谈优化空间**；
4. **不允许用回测结果反向改写 `03/04` 冻结对象**；
5. **修复后的 backtest 必须与同一冻结合同可比较**；
6. **任何改变研究身份的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，必须冻结：

- 代码版本 / commit
- 数据版本 / artifact version
- Universe / 白名单来源
- 时间切分
- 参数
- 费用 / 滑点 / 融券 / 资金规模假设
- 回测引擎版本
- 关键账户级结果
- stage aggregate 与关键异常

建议固定目录：

```text
05_backtest/failure_packages/<failure_id>/
```

至少产出：

- `failure_freeze.md`
- `failure_classification.md`
- `rollback_decision.yaml`
- `engine_compare.csv`
- `repro_manifest.json`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

## Step 1. 先做 correctness triage

固定顺序检查：

1. 同配置复跑是否一致；
2. 双引擎 / replay 是否一致；
3. 单位、预算、名义仓位、费用尺度是否一致；
4. 成交 / 持仓 / 平仓状态机是否一致；
5. 抽样核对典型交易是否对得上冻结合同。

若失败：

- 优先归类为 `ENG_FAIL`
- 暂停经济性讨论

## Step 2. 再做交易可行性归因

只有 correctness 过关，才允许继续判断：

- gross 还有边但 net 被吃掉 -> `EXEC_FAIL`
- 当前失败暴露上游 evidence / freeze 不稳 -> `RESEARCH_FAIL`
- 机制本身不再成立 -> `THESIS_FAIL`
- 要让结果过线必须改题 -> `SCOPE_FAIL`

## Step 3. 研究边界审计

检查回测阶段是否偷偷改题：

- 是否改了 Universe；
- 是否改了 signal formula；
- 是否改了冻结阈值、白名单、`best_h`；
- 是否让新的风险过滤器改变了策略身份。

若发生上述行为：

- 归类为 `SCOPE_FAIL`
- 停止原线推进

## Step 4. 映射 formal decision

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限回测 verdict 已清楚，但 engine compare、failure package、review sidecar 不完整
- `RETRY`
  适用于当前或更早阶段可受控修复的实现、执行、evidence 问题
- `NO-GO`
  适用于机制在合理实现与合理成本下不值得继续
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
| `ENG_FAIL` | `05_backtest`、`02_signal_ready` 或 `01_data_ready` | `RETRY` |
| `EXEC_FAIL` | `05_backtest` | `RETRY` |
| `RESEARCH_FAIL` | `03_train_freeze` 或 `04_test_evidence` | `RETRY` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- 需要改变 Universe、持有期、策略身份；
- 需要把 alpha 线降级成 execution-only 线；
- 需要新增会改写主问题的风险过滤器；
- 需要在原线里引入完全不同的执行语义。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于当前或合法上游回退边界内时，允许修改：

- 回测引擎实现与 replay 语义
- 费用 / 滑点 / 预算 / 名义仓位换算
- 执行器、下单节奏、退出语义的 stage-local 实现
- engine compare、failure package、audit sidecar
- 合法回退到 `03/04` 的 evidence / freeze 闭环

## 9.2 禁止修改

在 `05_backtest_failure_sop` 中，默认禁止：

- 用回测结果反向改写 `03_train_freeze` 冻结对象；
- 静默改变信号公式、白名单、`best_h`、time split；
- 用 summary 文本替代账户级经济性判断；
- 借修执行器之名重写研究问题；
- 跳过失败冻结，直接覆盖旧结果。

---

# 10. Retry 纪律

`05_backtest` 的 retry 必须是 **controlled retry**。

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
failure_class: EXEC_FAIL
root_cause_hypothesis: 当前退出语义导致换手过高，gross 仍有边但 net 被费用吃掉
rollback_stage: 05_backtest
allowed_modifications:
  - adjust_exit_semantics_within_frozen_signal
  - rerun_cost_sensitivity_envelope
  - regenerate_engine_compare
forbidden_modifications:
  - change_signal_formula
  - change_whitelist
  - change_time_split
expected_improvement:
  - turnover declines materially
  - gross_to_net retention improves
  - close_reason distribution matches strategy intent
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - time_split
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- 若多轮修复后仍不具经济意义，应升级为 `NO-GO`；
- 不允许把 `05` 变成无限期曲线优化层。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `failure_freeze.md`
- `failure_classification.md`
- `rollback_decision.yaml`
- `engine_compare.csv`
- `repro_manifest.json`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee 审核点

Reviewer 至少要审：

1. 失败是否已被完整冻结？
2. 当前回测是否只消费了合法冻结对象？
3. 双引擎 / replay 是否一致？
4. gross、net、cost、close reason 是否能解释？
5. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 当前失败是实现问题、执行问题、上游 evidence 问题，还是机制失效？
2. 是否存在用回测结果反向改写上游的行为？
3. 是否已经达到必须开 child lineage 的条件？
4. formal decision 是否符合治理纪律？

---

# 13. 与 Topic A / Topic C 的落地备注

若当前研究为 Topic A / Topic C 线，`05_backtest` 额外必须检查：

- `topicA` 的结构证据是否被错误包装成交易收益结论；
- `topicC-3A` 的进出场语义是否真正消费了冻结信号，而不是临时新规则；
- `best_h`、白名单、quality gate 是否仍与 `04_test_evidence` 一致；
- 当前策略若需要靠极窄执行补丁存活，是否已经升级成 `THESIS_FAIL` 或 `SCOPE_FAIL`；
- 双引擎对 `ResidualZ`、`OB/OS`、持有期、close reason 的解释是否一致。

---

# 14. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示：

## 14.1 `PASS FOR RETRY`

条件：

- 回测 verdict 已清楚；
- 仅缺 engine compare、failure package 或 reviewer 闭环；
- 不需要改变研究身份。

## 14.2 `RETRY`

条件：

- 问题明确；
- 回退层级清晰；
- 修复不改变研究身份。

## 14.3 `NO-GO`

条件：

- 机制在合理实现与合理成本下不值得继续；
- 多轮受控修复后仍不具交易经济性；
- 当前线不值得继续投入。

## 14.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变 Universe、执行语义、持有期、研究主问题或策略身份；
- 需要开新谱系来保持治理清洁。

## 14.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段重做合法回测证据链 -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线交易可行性不足，不值得继续 -> `NO-GO`
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
- reviewer / referee 可以依据产物复建同一份 backtest 结论。

---

# 16. 一句话总结

`05_backtest` 失败后的标准动作，不是“继续调曲线直到赚钱”，而是：

**先冻结失败，再判断它是工程实现问题、执行经济性问题、上游证据不足、主假设失效还是已经换题；随后只在合法回退边界内受控修复，任何改变研究身份的动作都必须升级为 rollback 或 child lineage。**
