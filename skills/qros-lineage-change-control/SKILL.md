---
name: qros-lineage-change-control
description: Use after stage-specific failure classification is complete, to run the 4-question framework, classify the change type, enforce per-type disciplines, and produce formal change control artifacts.
---

# QROS Lineage Change Control

## Purpose

本 skill 是谱系变更总闸门。

在 `qros-stage-failure-handler` 路由、且各 stage failure skill 完成 failure classification 之后，由本 skill 运行：

1. 变更判定四问
2. 变更类型分类（`PATCH / CONTROLLED_RETRY / STAGE_ROLLBACK / CHILD_LINEAGE / NO_GO`）
3. 各类型的正式纪律与产物要求
4. Retry 次数限制
5. Change audit 文档要求

本 skill 只判断"这个修改应该记在哪条谱系上"，不做 stage-specific triage。

## Entry Condition

只能由以下入口触发：

- `qros-stage-failure-handler` 路由完成后；
- 且对应 stage failure skill 已输出 `failure_class` 与初步 `disposition` 草案。

## 变更判定四问

任何变更请求，必须先依次回答：

### 问题 1：研究主问题变了吗？

如果变了：直接判定为 `CHILD_LINEAGE`，无需继续。

### 问题 2：冻结对象身份变了吗？

例如：whitelist 来源变了 / `best_h` 角色变了 / risk filter 从附属变主 gate / `OS` 从审计字段变正式入场条件

如果变了：至少是 `STAGE_ROLLBACK`，通常是 `CHILD_LINEAGE`。

### 问题 3：交易语义变了吗？

例如：均值回归退出改成固定 horizon / 对冲相对价值变成裸方向 / 主策略改成组合增强器

如果变了：通常是 `CHILD_LINEAGE`。

### 问题 4：当前修改是否还能沿用原证据链？

如果原 `04_test_evidence`、`05_backtest`、`06_holdout` 不再适用：
- `STAGE_ROLLBACK` 或 `CHILD_LINEAGE`

## 判定矩阵

| 变更内容 | 改变主问题 | 改变冻结对象身份 | 改变交易语义 | 结论 |
|---|---|---|---|---|
| parser/schema/bug 修复 | 否 | 否 | 否 | PATCH |
| 同 stage 内单一执行器微调 | 否 | 否 | 否/轻微 | CONTROLLED_RETRY |
| 需要回到更早阶段补证据 | 否 | 可能 | 否 | STAGE_ROLLBACK |
| 双边改单边 | 是 | 是 | 是 | CHILD_LINEAGE |
| 风险过滤改成主 gate | 是/通常是 | 是 | 是 | CHILD_LINEAGE |
| Universe 来源变化 | 通常是 | 是 | 可能 | CHILD_LINEAGE |
| 从主策略降级成子信号 | 是 | 是 | 是 | CHILD_LINEAGE |
| 多轮失败后停止 | n/a | n/a | n/a | NO_GO |

## 正式变更类型与纪律

### `PATCH`

**允许范围：**
- 不改变研究问题、stage contract、冻结对象、交易语义、晋级标准

**必须产出：**
- `patch_note.md`
- `repro_manifest.json`

---

### `CONTROLLED_RETRY`

**允许范围：**
- 同一 stage 内、单一假设驱动、单一修改集、明确成功判据
- 修改后仍属于同一研究问题

**必须写清：**
- `retry_hypothesis`
- `allowed_modifications`
- `forbidden_modifications`
- `retry_count`（当前是第几次）
- `success_criteria`
- `unchanged_contracts`

**Retry 次数纪律：**
- 同一失败类型同一 stage 默认最多 **1-2 次**
- `holdout` 阶段默认最多 **1 次**，且只限 PURITY_FAIL 或 artifact/repro 问题
- 超限后仍无改善，必须升级为 `STAGE_ROLLBACK`、`CHILD_LINEAGE` 或 `NO_GO`

---

### `STAGE_ROLLBACK`

**允许范围：**
- 研究主问题不变，但当前 stage 不能继续
- 必须回到更早阶段补证据、修 freeze、重审稳健性

**必须写清：**
- `rollback_stage`（具体回退到哪个 stage）
- `rollback_reason`
- `re-entry_gate`（重新进入条件）
- `objects_to_refreeze`
- `objects_frozen_unchanged`

**纪律：**
- 回退不等于自由重开
- 只允许在明确 rollback 范围内重做
- 原线先前阶段的正式结论必须保留历史版本

---

### `CHILD_LINEAGE`

**触发条件（满足任一即触发）：**

1. 研究主问题变了
2. Universe 身份变了
3. 主副腿角色变了
4. 信号边从双边改成单边
5. 风险过滤从附属变主 gate
6. 执行语义改变到无法沿用原证据链
7. 策略从"独立主策略"变成"组合子信号"
8. 策略频率、交易身份或 portfolio role 被实质重写

**必须产出：**
- 新的 `00_mandate`
- 新的 `research_scope.md`
- 新的 `artifact_catalog.md`
- 新的 lineage id
- 与父谱系的关系说明 `lineage_relation.md`

**原线必须保留：**
- 原线失败或当前阶段结论不得被覆盖或重命名成新题

**`lineage_relation.md` 必须写清：**
- `parent_lineage_id`
- `difference_from_parent`
- `inherited_objects`
- `re-frozen_objects`
- `why_parent_cannot_absorb_this_change`

---

### `NO_GO`

**触发条件：**
- 主假设不成立
- 多轮 retry / rollback 后仍无合理修复空间
- holdout / shadow 证伪
- 经济性长期不成立

**必须产出：**
- `closure_note.md`
- `failure_summary.md`
- `lessons_learned.md`

**纪律：**
- 停线是正式结论之一，不允许伪装成"后续再看看"

---

## 8 种常见 CHILD_LINEAGE 误判场景

以下情况最容易被误判为小优化，实际必须开新谱系：

### 1. 从结构研究线变成执行研究线
`topicA` 原本是结构白名单，后来想改成逐 bar 执行 gate → 这不是 patch，是 CHILD_LINEAGE

### 2. 从双边研究线变成单边执行线
原 `topicC` 研究 `OB/OS`，后来只做 `topicC-3A / OB short only` → 策略身份变化，CHILD_LINEAGE

### 3. 从原 Universe 变成执行白名单
原来所有通过结构门槛的币进研究池，后来只留"交易成本更低的一小撮币" → 身份变化，CHILD_LINEAGE

### 4. 从风险过滤器变成主 alpha gate
`topicD` 原本只做风险过滤，后来变成只在 `RiskOff=0 & StateX=1` 时才算入场 → CHILD_LINEAGE

### 5. 从主策略变成组合辅助子信号
单独做不成立，但低相关、可做 ensemble → 研究治理上是新身份，CHILD_LINEAGE

### 6. 从双腿策略变成单腿策略（去掉任意一条腿）
原题有主腿与副腿，后来移除其中一条 → 策略机制改变，CHILD_LINEAGE

### 7. 借 execution 修复之名重写进出场语义
"只是优化退出"，但退出语义从均值回归改成固定 horizon → 交易语义变化，CHILD_LINEAGE

### 8. 改变 time split 中的 holdout 边界并重跑全流程
说是"修错"，但实际上 holdout 边界移动改变了泛化测试集 → 重新提交，CHILD_LINEAGE

## Change Audit Documents（每次正式变更必须产出）

每次正式变更请求至少产出：

### `change_request.md`
- 当前问题
- 提议变更
- 触发原因
- 预期分类

### `change_classification.md`
- 判定为 `PATCH / CONTROLLED_RETRY / STAGE_ROLLBACK / CHILD_LINEAGE / NO_GO`
- 判定理由
- 被排除的其他类别

### `impact_assessment.md`
- 对研究主问题的影响
- 对冻结对象的影响
- 对交易语义的影响
- 对已有证据链的影响

### `approval_record.md`
- 提出人
- Reviewer
- Referee
- 批准时间
- 正式决策

## Reviewer / Referee 审核清单

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

## Working Rules

- 只接受来自 stage failure skill 的分类结论，不接受未经 stage triage 的直接变更请求
- 4 问必须全部回答，不得跳过任何一问
- 变更类型确认后，对应纪律与产物要求强制执行，不得选择性遵守
- 原线结论保留原则不得妥协

## Conversation Contract

进入本 skill 后，输出顺序必须是：

1. 回显 stage failure skill 给出的 `failure_class`
2. 逐一回答变更判定四问
3. 给出判定矩阵对照
4. 宣布正式 change type
5. 列出对应的纪律与产物要求
6. 给出 `change_classification.md` 草案
7. 给出 `impact_assessment.md` 草案
8. 只有用户确认后，才生成正式 change audit docs
