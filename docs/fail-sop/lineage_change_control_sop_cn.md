
# Lineage Change Control SOP（机构级中文版）

- doc_id: SOP-LINEAGE-CHANGE-CONTROL-v1.0
- title: Lineage Change Control SOP — 谱系变更治理与分流控制规范
- date: 2026-03-23
- timezone: Asia/Tokyo
- status: Active
- owner: Strategy Research / Quant Dev / Referee / Portfolio Review
- audience:
  - Research
  - Quant Dev
  - Referee
  - Portfolio Review
  - Trading
- depends_on:
  - 00_mandate
  - 01_data_ready_failure_sop
  - 02_signal_ready_failure_sop
  - 03_train_freeze_failure_sop
  - 04_test_evidence_failure_sop
  - 05_backtest_failure_sop
  - 06_holdout_failure_sop
  - 07_shadow_failure_sop

---

## 1. 文档目的

本规范定义：

**在机构级策略研发体系中，任何阶段出现问题后，如何判断当前修改究竟属于原谱系内的小修、受控 retry、阶段回退、研究重开，还是必须新开 child lineage。**

本规范解决的核心问题不是“能不能改”，而是：

1. 当前修改是否改变了研究主问题？
2. 当前修改是否改变了冻结对象的身份？
3. 当前修改是否仍属于同一条证据链？
4. 当前修改是否会污染既有 stage gate 结论？
5. 当前修改应记在原线，还是必须独立成新谱系？

一句话：

**本规范是整套 stage-gate 体系的总闸门，专门防止“在原线里偷偷换题”。**

---

## 2. 适用范围

本规范适用于以下所有变更请求：

- 研究主问题变化
- Universe 变化
- 主副腿角色变化
- 信号表达式变化
- 风险字段角色变化
- 执行语义变化
- 时间切分变化
- 冻结对象变化
- 产物合同变化
- 从主策略降级为辅助信号
- 从双边变单边，或从单边变双边
- 从结构层变执行层，或从执行层变组合层

---

## 3. 核心原则

### 3.1 谱系优先于参数
机构治理中，最重要的不是某个参数值，而是：

- 你在研究哪一个问题
- 这个问题的边界是否冻结
- 当前证据属于哪一条谱系

因此：

**参数变化不一定是小改；问题身份变化一定不是小改。**

### 3.2 原线失败结论不得被静默覆盖
任何已经形成正式 stage 结论的原线，不得因为后续“改得更合理”而被默默覆盖。

允许的是：
- 原线保留结论；
- 新线重开并重新审计。

不允许的是：
- 在原线里改题，然后把新结果说成原线也成立。

### 3.3 变更粒度必须与审计粒度一致
如果一个改动会改变：
- 研究问题
- 统计证据口径
- 交易语义
- 晋级标准
- 风险职责

那么这个改动的治理粒度必须提升到谱系级，而不是 run 级。

### 3.4 原线只能承载“同问题下的受控修改”
原谱系允许承载：
- bug 修复
- schema 修复
- 执行层微调
- 明确不改变主问题的受控 retry

原谱系不得承载：
- 研究问题迁移
- 风险角色重写
- Universe 身份变化
- alpha 语义变化
- 组合定位变化

---

## 4. 正式变更类型

所有变更请求，必须被归类为以下五类之一：

### 4.1 `PATCH`
定义：不改变研究主问题、不改变冻结对象身份、不改变交易语义的局部修复。

典型例子：
- parser 修复
- schema 修复
- artifact 路径修复
- bug fix
- 文档澄清
- 不改变逻辑的计算效率优化

### 4.2 `CONTROLLED_RETRY`
定义：在当前 stage 允许范围内，围绕一个明确假设做一次受控修改，不改变研究主问题。

典型例子：
- 在 `05_backtest` 中只调整执行器退出语义
- 在 `07_shadow` 中只调整订单节奏
- 在 `01/02` 中修复已识别的数据/时点问题

### 4.3 `STAGE_ROLLBACK`
定义：当前问题说明原 stage 不能继续，必须回退到更早 stage 补证据或重做冻结，但研究主问题尚未改变。

典型例子：
- `05_backtest` 暴露 `04_test_evidence` 不稳
- `04_test_evidence` 暴露 `03_train_freeze` 被污染
- `03_train_freeze` 暴露 `02_signal_ready` 前视问题

### 4.4 `CHILD_LINEAGE`
定义：当前修改已经改变研究主问题、交易语义、Universe 身份或风控角色，必须新开谱系。

典型例子：
- 从双边策略改成单边策略
- 从 `topicA` 结构白名单改成执行白名单
- 从 `OB/OS` 双边研究改成 `OB short only`
- 从风险过滤器变成主信号 gate
- 从策略线改成组合辅助子信号线

### 4.5 `NO_GO`
定义：当前谱系不应继续，且没有合理受控修改空间。

典型例子：
- 主假设不成立
- 多轮 retry 后仍无改进
- 跨样本泛化失败
- 需要大量补丁才能存活

---

## 5. 变更判定四问

任何变更请求都必须先回答四个问题：

### 问题 1：研究主问题变了吗？
如果变了，直接判定为：
- `CHILD_LINEAGE`

### 问题 2：冻结对象身份变了吗？
例如：
- whitelist 来源变了
- `best_h` 的角色变了
- risk filter 从附属变主 gate
- `OS` 从审计字段变正式入场条件

如果变了，通常至少是：
- `STAGE_ROLLBACK`
- 或 `CHILD_LINEAGE`

### 问题 3：交易语义变了吗？
例如：
- 从均值回归退出改成固定 horizon 事件交易
- 从对冲相对价值变成裸方向策略
- 从主策略改成组合增强器

如果变了，通常是：
- `CHILD_LINEAGE`

### 问题 4：当前修改是否还能沿用原证据链？
如果不能继续沿用：
- 原 `04_test_evidence`
- 原 `05_backtest`
- 原 `06_holdout`

则不得算作原线小修，必须：
- `STAGE_ROLLBACK`
- 或 `CHILD_LINEAGE`

---

## 6. 判定矩阵

| 变更内容 | 是否改变主问题 | 是否改变冻结对象身份 | 是否改变交易语义 | 结论 |
|---|---:|---:|---:|---|
| parser/schema/bug 修复 | 否 | 否 | 否 | PATCH |
| 同 stage 内单一执行器微调 | 否 | 否 | 否/轻微 | CONTROLLED_RETRY |
| 需要回到更早阶段补证据 | 否 | 可能 | 否 | STAGE_ROLLBACK |
| 双边改单边 | 是 | 是 | 是 | CHILD_LINEAGE |
| 风险过滤改成主 gate | 是/通常是 | 是 | 是 | CHILD_LINEAGE |
| Universe 来源变化 | 通常是 | 是 | 可能 | CHILD_LINEAGE |
| 从主策略降级成子信号 | 是 | 是 | 是 | CHILD_LINEAGE |
| 多轮失败后停止 | n/a | n/a | n/a | NO_GO |

---

## 7. 各类变更的正式规则

## 7.1 `PATCH`

### 允许范围
- 不改变研究问题
- 不改变 stage contract
- 不改变冻结对象
- 不改变交易语义
- 不改变晋级标准

### 需要产物
- `patch_note.md`
- `repro_manifest.json`

### 不需要
- 新开谱系
- 重写 `00_mandate`

---

## 7.2 `CONTROLLED_RETRY`

### 允许范围
- 同一 stage 内
- 单一假设驱动
- 单一修改集
- 明确成功判据
- 修改后仍属于同一研究问题

### 必须写清
- `retry_hypothesis`
- `allowed_modifications`
- `forbidden_modifications`
- `retry_count`
- `success_criteria`

### 次数纪律
- 同一失败类型默认最多 `1-2` 次
- 超过次数仍无改善，不得继续原地 retry
- 必须升级为：
  - `STAGE_ROLLBACK`
  - `CHILD_LINEAGE`
  - 或 `NO_GO`

---

## 7.3 `STAGE_ROLLBACK`

### 允许范围
- 研究主问题不变
- 但当前 stage 不能继续
- 必须回到更早阶段补证据、修 freeze、重审稳健性

### 必须写清
- `rollback_stage`
- `rollback_reason`
- `re-entry_gate`
- `objects_to_refreeze`
- `objects_frozen_unchanged`

### 纪律
- 回退不等于自由重开
- 只允许在明确 rollback 范围内重做
- 原线先前阶段的正式结论必须保留历史版本

---

## 7.4 `CHILD_LINEAGE`

### 触发条件
满足任一条，必须开新谱系：

1. 研究主问题变了
2. Universe 身份变了
3. 主副腿角色变了
4. 信号边从双边改成单边
5. 风险过滤从附属变主 gate
6. 执行语义改变到无法沿用原证据链
7. 策略从“独立主策略”变成“组合子信号”
8. 策略频率、交易身份或 portfolio role 被实质重写

### 必须产出
- 新的 `00_mandate`
- 新的 `research_scope.md`
- 新的 `artifact_catalog.md`
- 新的 lineage id
- 与父谱系的关系说明 `lineage_relation.md`

### 原线必须保留
- 原线失败或当前阶段结论
- 原线不得被覆盖或重命名成新题

---

## 7.5 `NO_GO`

### 触发条件
- 主假设不成立
- 多轮 retry / rollback 后仍无合理修复空间
- holdout / shadow 证伪
- 经济性长期不成立
- 继续投入不符合资源配置纪律

### 必须产出
- `closure_note.md`
- `failure_summary.md`
- `lessons_learned.md`

### 纪律
- 停线不是失败治理的例外，而是正式结论之一
- 不允许把 `NO_GO` 伪装成“后续再看看”

---

## 8. 何时必须开 Child Lineage

以下情况最容易被误判成“小优化”，实际上必须开子谱系：

### 8.1 从结构研究线变成执行研究线
例如：
- `topicA` 原本是结构白名单
- 后来想把它改成逐 bar 执行 gate

这已经不是原题。

### 8.2 从双边研究线变成单边执行线
例如：
- 原 `topicC` 研究 `OB/OS`
- 后来只做 `topicC-3A / OB short only`

这不是参数变化，是策略身份变化。

### 8.3 从原 Universe 变成执行白名单
例如：
- 原本所有通过结构门槛的币都进研究池
- 后来只留“交易成本更低的一小撮币”作为正式执行池

如果这是正式身份变化，必须开新线。

### 8.4 从风险过滤器变成主 alpha gate
例如：
- 原本 `topicD` 只做风险过滤
- 后来变成只在 `RiskOff=0 & StateX=1` 时才算入场

若这已经决定策略 identity，就必须开新线。

### 8.5 从主策略变成组合辅助子信号
例如：
- 单独做不成立
- 但低相关、可做 ensemble

这在研究治理上是新身份，不应继续伪装成原主策略线。

---

## 9. 原线与子线的关系要求

每条 child lineage 必须明确：

- `parent_lineage_id`
- `difference_from_parent`
- `inherited_objects`
- `re-frozen_objects`
- `why_parent_cannot_absorb_this_change`

必须明确写清：

**为什么这个变化不能作为原线 patch/retry/rollback 吸收，而必须独立成新线。**

---

## 10. 文档与审计要求

每次正式变更请求至少产出：

### 10.1 `change_request.md`
记录：
- 当前问题
- 提议变更
- 触发原因
- 预期分类

### 10.2 `change_classification.md`
记录：
- 判定为 `PATCH / CONTROLLED_RETRY / STAGE_ROLLBACK / CHILD_LINEAGE / NO_GO`
- 判定理由
- 被排除的其他类别

### 10.3 `impact_assessment.md`
记录：
- 对研究主问题的影响
- 对冻结对象的影响
- 对交易语义的影响
- 对已有证据链的影响

### 10.4 `approval_record.md`
记录：
- 提出人
- Reviewer
- Referee
- 批准时间
- 正式决策

---

## 11. Reviewer / Referee 审核清单

审查人至少确认：

1. 当前变更是否改变研究主问题
2. 当前变更是否改变 Universe 身份
3. 当前变更是否改变主副腿角色
4. 当前变更是否改变交易语义
5. 当前变更是否改变风险字段职责
6. 当前变更是否仍可沿用原证据链
7. 当前变更应记在原线还是必须开新线
8. 原线结论是否会被静默覆盖
9. retry 次数是否超限
10. 正式分类是否合理

---

## 12. 对 Topic A / Topic C / Topic D 的落地说明

### 12.1 `topicA`
`topicA` 的正式职责是结构诊断与研究池筛查。若后续想让 `topicA` 承担逐 bar 状态 gate、执行 gate 或交易级过滤，这通常不是 patch，而是：

- `CHILD_LINEAGE`

### 12.2 `topicC`
从双边 `topicC` 到 `topicC-3A`，属于典型的：

- 研究主问题变化
- 信号边变化
- 交易语义变化

因此必须是：
- `CHILD_LINEAGE`

### 12.3 `topicD`
若 `topicD` 原本只是风险过滤层，后续想让它决定主信号有效性，则已经改变 risk role，通常也必须：

- `CHILD_LINEAGE`

---

## 13. 正式输出格式

每次变更请求，结论页必须只输出一种状态：

### `PATCH`
- 原线小修
- 不改变研究身份

### `CONTROLLED_RETRY`
- 原线受控重试
- 不改变研究身份

### `STAGE_ROLLBACK`
- 原线回退补证据
- 不改变研究身份

### `CHILD_LINEAGE`
- 研究身份变化
- 新开谱系

### `NO_GO`
- 停止原线
- 不再继续

---

## 14. 一句话总结

**机构级策略研发不是只有 stage gate，还必须有谱系变更总控。任何看似“只是优化一下”的改动，都必须先判断它究竟是在修原问题，还是已经换了一个新问题。**

这条纪律的本质是：

**原线只能承载同一研究问题下的受控修改；一旦问题身份变化，就必须开新谱系，而不能在原线里偷偷换题。**
