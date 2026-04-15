# 04_test_evidence_failure_sop

Doc ID: SOP-TESTEVIDENCE-FAILURE-v1.0
Title: `04_test_evidence_failure_sop` — Test Evidence 阶段失败处置标准操作流程（机构级）
Date: 2026-03-23
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Reviewer / Referee
Audience:
- Research
- Quant Dev
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `00_mandate`
- `01_data_ready`
- `02_signal_ready`
- `03_train_freeze`
- `stage-failure-harness`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当 research lineage 在 `04_test_evidence` 阶段未通过时，团队应如何冻结失败、区分证据缺失与治理违规、决定回退层级、限制允许修改范围，并输出可审计结论。**

它不是“继续把统计做漂亮”的说明书。
它是 `04_test_evidence` **失败后的标准处置合同**。

---

# 2. 适用范围

本 SOP 适用于所有已经完成：

- `00_mandate`
- `01_data_ready`
- `02_signal_ready`
- `03_train_freeze`

并进入 test 期正式证据验证的研究线，包括但不限于：

- 结构存在性 / 稳定性审计
- 滞后传导 / lead-lag / threshold transmission
- 均值回归 / 超涨超跌 / 单边或双边 Topic C 研究
- risk-off、breaker、状态过滤与失效条件研究

只要当前阶段需要回答“冻结后的研究对象在正式 test 期上是否仍成立”，本 SOP 就适用。

---

# 3. 阶段职责

`04_test_evidence` 的职责不是继续找理由，而是：

1. 在已冻结的 train/test 切分、阈值、白名单、参数边界上验证结构证据；
2. 冻结正式 test 期统计结论；
3. 冻结后续 `05_backtest` 允许消费的证据对象；
4. 阻止团队用 test 结果反向改写 `03_train_freeze`。

因此，`04_test_evidence` 失败通常代表：

- 证据本身不足；
- 证据脆弱；
- 证据已被多重检验或选择偏差污染；
- 或当前讨论的问题已经偏离原 mandate。

---

# 4. 失败触发条件

出现下列任一情形，即触发 `04_test_evidence_failure_sop`：

## 4.1 硬性失败（自动 FAIL）

- 核心 test 指标未达 gate；
- test 期与 train 期表现断裂；
- 证据只在极窄切片、极少 symbol、极短时间段成立；
- 样本外稳健性不足，不形成平台；
- 多次试验、重复筛选、挑切片、挑 symbol、挑 side 后才找到好看版本；
- evidence artifact 无法复现或无法追溯到原始时序；
- 当前 evidence 讨论的问题已不再是 `00_mandate` 原题。

## 4.2 软性失败（需 Referee 判断）

- 核心证据成立，但 summary、segmentation sidecar 或 artifact catalog 不完整；
- reviewer 认可主结论，但 referee 无法判断是否存在 freeze discipline 漏洞；
- 指标大体通过，但稳健性说明不足，无法直接进入 `05_backtest`。

软性失败仍必须进入 harness，先冻结，再决定是：

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

---

# 5. 失败分类

`04_test_evidence` 的失败必须先映射 shared harness，再落到 stage-specific failure class。

## 5.1 `EVIDENCE_ABSENT`

Shared layer: `THESIS`

定义：正式 test 期中，核心结构证据不存在、方向错误或不足以支撑晋级。

典型表现：
- `Q5` 没有负向回归；
- `gamma >= 0`；
- `DC_N` 未显著高于基线；
- `DownLinkGap` 不显著大于 0。

## 5.2 `EVIDENCE_FRAGILE`

Shared layer: `THESIS`

定义：证据存在，但极其脆弱，对窗口、切片、参数或 symbol 子集高度敏感。

典型表现：
- train/test 都略有边，但轻微改动就断崖；
- 统计只在少数参数点成立，不形成平台；
- 某几个 symbol 撑起总结果。

## 5.3 `REGIME_SPECIFIC_FAIL`

Shared layer: `THESIS`

定义：证据只在极窄 market regime 成立，超出该 regime 即失效。

典型表现：
- 只在低波期有用；
- 只在牛市 / 熊市 / risk-off 有效；
- 只有极端环境下才出现结构。

## 5.4 `SELECTION_BIAS_FAIL`

Shared layer: `INTEGRITY`

定义：由于多次试验、重复筛选、挑切片、挑 symbol、挑 side，导致当前 test evidence 不再可信。

典型表现：
- 记录不清试过多少变体；
- `best_h`、白名单、side、阈值看过 test 结果后才定；
- 反复切 test 窗、换 regime 分层直到结果成立。

## 5.5 `ARTIFACT_REPRO_FAIL`

Shared layer: `REPRO`

定义：test evidence 产物无法稳定复现，或无法从底层时序追溯。

典型表现：
- 同配置重跑 summary 不一致；
- 汇总表与单币时序对不上；
- `best_h` 来源路径不清楚；
- symbol summary 与 report_by_h 不可核对。

## 5.6 `SCOPE_DRIFT_FAIL`

Shared layer: `SCOPE`

定义：当前 test evidence 讨论的问题已经偏离原研究问题。

典型表现：
- 原题是双边结构审计，test 时只汇报对自己有利的一边；
- 原题是 structure evidence，却在这层混入执行收益优化；
- 原题是 Topic C 双边研究，却在 evidence 阶段静默改成 `3A`。

---

# 6. 标准处置总原则

`04_test_evidence` 失败后，必须遵守下面六条原则：

1. **先冻结失败，再解释统计故事**；
2. **先确认 freeze discipline，再讨论证据强弱**；
3. **先排除选择偏差，再讨论 regime 解释**；
4. **不允许用追加切片、改统计口径、挑窗口的方式救结果**；
5. **修复后的 evidence 必须能回到同一份冻结合同**；
6. **任何改变研究主问题的动作，都必须升级为 rollback 或 child lineage。**

---

# 7. 标准操作流程

## Step 0. 冻结失败

触发失败后，必须冻结：

- 当前 test evidence 产物
- 代码版本
- 数据版本
- freeze manifest 引用
- test summary / symbol summary / segment summary
- 当前 reviewer / referee 意见
- 已知异常与被排除解释

至少产出：

- `failure_freeze.md`
- `test_evidence_manifest.json`
- `evidence_summary.parquet`
- `report_by_h.parquet`
- `repro_manifest.json`
- `review_notes.md`

## Step 1. 先做 freeze discipline 审计

优先检查：

- 当前 evidence 是否只消费了 `03_train_freeze` 允许的对象；
- test 期统计是否没有反向重估阈值、白名单、`best_h`；
- train/test 边界是否无穿越；
- 当前切片与对比口径是否可追溯。

若失败：

- 优先归类为 `SELECTION_BIAS_FAIL` 或 `SCOPE_DRIFT_FAIL`

## Step 2. 再做 evidence attribution

必须按以下顺序判断：

- 证据根本不存在 -> `EVIDENCE_ABSENT`
- 证据存在但脆弱 -> `EVIDENCE_FRAGILE`
- 证据只在极窄 regime 成立 -> `REGIME_SPECIFIC_FAIL`
- 证据结论根本不可复建 -> `ARTIFACT_REPRO_FAIL`

## Step 3. 做 artifact reproducibility 审计

必须显式检查：

- summary 是否能追溯到原始时序；
- `report_by_h`、symbol summary、segment summary 是否一致；
- 同配置重跑是否稳定；
- evidence summary 是否有完整 manifest 与 artifact catalog。

若失败：

- 归类为 `ARTIFACT_REPRO_FAIL`
- 禁止进入 `05_backtest`

## Step 4. 研究边界审计

检查当前 evidence 讨论是否偷偷换题：

- 是否只汇报有利 side；
- 是否把证据层变成执行收益优化层；
- 是否因为某个 regime 好看就临时把 regime filter 升格成主问题。

若发生上述行为：

- 归类为 `SCOPE_DRIFT_FAIL`
- 停止原线推进

## Step 5. 映射 formal decision

完成审计后，只能映射到现有 formal vocabulary：

- `PASS FOR RETRY`
  仅限主证据结论成立，但 evidence sidecar 或 artifact catalog 不完整
- `RETRY`
  适用于可回退到 `03`、`02` 或当前 stage 受控修复的问题
- `NO-GO`
  适用于正式 test 证据缺失、脆弱或多轮修复后仍不成立
- `CHILD LINEAGE`
  适用于修复动作已经改变主问题、regime 条件或研究身份

说明：

- `RESEARCH_AGAIN` 可以作为解释性 prose 出现
- 但正式输出必须翻译成 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`

---

# 8. 回退与分流规则

## 8.1 标准回退阶段

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---:|---|
| `EVIDENCE_ABSENT` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `NO-GO` |
| `EVIDENCE_FRAGILE` | `03_train_freeze` | `RETRY` 或 `NO-GO` |
| `REGIME_SPECIFIC_FAIL` | `03_train_freeze` 或 `00_mandate` | `CHILD LINEAGE` 或 `NO-GO` |
| `SELECTION_BIAS_FAIL` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `ARTIFACT_REPRO_FAIL` | `04_test_evidence` | `PASS FOR RETRY` 或 `RETRY` |
| `SCOPE_DRIFT_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## 8.2 何时必须升级为 child lineage

出现以下任一情况，禁止在原线静默修复：

- regime 条件从解释性切片变成正式主假设；
- 原题是结构审计，却转成执行收益优化；
- 原题是双边研究，却静默改成单边交易线；
- 需要改变 Universe、frequency、机制定义才能“让 test 通过”。

---

# 9. 允许与禁止修改

## 9.1 允许修改

当且仅当问题属于 evidence 治理范围内时，允许修改：

- evidence summary / segment summary / symbol summary 的复现链
- 当前 stage 的 artifact catalog 与 review sidecar
- 受控回退到 `03_train_freeze` 重新冻结候选空间、阈值或白名单
- 受控回退到 `02_signal_ready` 修复上游字段合同

## 9.2 禁止修改

在 `04_test_evidence_failure_sop` 中，默认禁止：

- 因为 test 不好看而追加新切片直到结果成立；
- 用 test 结果反向重估 `03_train_freeze` 冻结对象；
- 把 regime 解释临时升级成主问题；
- 用执行收益或 backtest 曲线替代 test evidence；
- 跳过失败冻结，直接覆盖旧结果。

---

# 10. Retry 纪律

`04_test_evidence` 的 retry 必须是 **controlled retry**。

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
failure_class: SELECTION_BIAS_FAIL
root_cause_hypothesis: best_h 与 whitelist 的选择纪律不完整，当前 test 结论被多次筛选污染
rollback_stage: 03_train_freeze
allowed_modifications:
  - rebuild_trial_log
  - regenerate_train_only_freeze_objects
  - rerun_test_evidence_review
forbidden_modifications:
  - slice_test_until_it_looks_good
  - rewrite_freeze_objects_from_test_results
  - change_research_question
expected_improvement:
  - freeze objects are traceable to train-only inputs
  - test evidence can be reproduced from the same contract
unchanged_contracts:
  - mandate
  - time_split
  - signal_family
  - data_contract
```

纪律要求：

- 同一 failure class 连续 retry 不得超过 2 次；
- 若正式 test 证据多轮后仍不成立，应升级为 `NO-GO`；
- 不允许把 `04` 变成无限切片优化层。

---

# 11. 标准产物

每次触发本 SOP，至少应产出以下标准件：

- `failure_freeze.md`
- `test_evidence_manifest.json`
- `evidence_summary.parquet`
- `report_by_h.parquet`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若决定 `PASS FOR RETRY` 或 `RETRY`）

---

# 12. Reviewer / Referee 审核点

Reviewer 至少要审：

1. 失败是否已被完整冻结？
2. 当前 evidence 是否只消费了合法 freeze 对象？
3. summary、symbol summary、segment summary 是否能互相校对？
4. 是否存在选择偏差、切片挑选或 side 选择？
5. retry 修改范围是否被严格限制？

Referee 至少要审：

1. 正在验证的到底还是不是原研究问题？
2. 证据是缺失、脆弱、regime-specific，还是治理失守？
3. 是否已经达到必须开 child lineage 的条件？
4. formal decision 是否符合治理纪律？

---

# 13. 正式决策输出格式

本 SOP 执行完后，只允许输出下面四种 formal decision，外加一个 prose-only 提示：

## 13.1 `PASS FOR RETRY`

条件：

- 核心证据结论已成立；
- 仅缺 artifact sidecar、catalog 或 reviewer 闭环；
- 不需要改变研究身份。

## 13.2 `RETRY`

条件：

- 存在明确回退目标；
- 修复不改变研究身份；
- 证据仍值得在合法边界内重审。

## 13.3 `NO-GO`

条件：

- 正式 test 证据缺失或脆弱；
- 多轮受控修复后仍不足以支撑晋级；
- 当前线不值得继续投入。

## 13.4 `CHILD LINEAGE`

条件：

- 修复动作实质改变 regime 条件、研究主问题、Universe、frequency 或策略身份；
- 需要开新谱系来保持治理清洁。

## 13.5 Prose-only: “research again”

如果团队直觉上想写 “research again”，必须进一步翻译为：

- 回到当前或更早阶段重做合法证据链 -> `PASS FOR RETRY` 或 `RETRY`
- 原研究线证据不足，不值得继续 -> `NO-GO`
- 修复已经变成新问题 -> `CHILD LINEAGE`

---

# 14. 与 Topic A / Topic C 的落地备注

若当前研究为 Topic A / Topic C 线，`04_test_evidence` 额外必须检查：

- `topicA` 结构证据是否仍然只是结构证据，而非被静默包装成交易 alpha；
- `DC_down`、`DownLinkGap`、条件同向率等指标是否在 test 期仍保持方向一致；
- `ResidualZ`、`OB/OS`、`best_h` 的 test 期 evidence 是否只消费合法 freeze 对象；
- `topicC-3A` 是否仍保持原单边 / 双边合同，而非因为 test 结果临时换题；
- quality gate 是否被错误地当作 alpha enhancer 使用。

若这些未通过，不得进入 `05_backtest`。

---

# 15. DoD（完成定义）

本 SOP 被视为完成，至少要满足：

- 已冻结失败版本；
- 已完成 failure classification；
- 已明确 rollback stage；
- 已写明 allowed / forbidden modifications；
- 已输出 formal decision；
- 若允许 retry，已提供受控 retry 计划；
- reviewer / referee 可以依据产物复建同一份 evidence 结论。

---

# 16. 一句话总结

`04_test_evidence` 失败后的标准动作，不是“继续调统计直到显著”，而是：

**先冻结失败，再判断它是证据缺失、证据脆弱、regime 特异、选择偏差、artifact 不可复现还是已经换题；随后只在合法回退边界内受控修复，任何改变研究主问题的动作都必须升级为 rollback 或 child lineage。**
