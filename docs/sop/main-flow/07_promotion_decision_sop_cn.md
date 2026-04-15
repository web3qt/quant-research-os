# 07_promotion_decision_sop

Doc ID: SOP-PROMOTION-v1.0
Title: `07_promotion_decision_sop` — Promotion Decision 阶段标准操作流程（机构级）
Date: 2026-03-27
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev
Audience:
- Research
- Quant Dev
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `workflow_stage_gates.yaml`

---

# 1. 文档目的

本 SOP 只回答一件事：

**Promotion Decision 阶段应该如何执行、交什么 artifact、怎么判 gate。**

它不是主流程 SOP 的替代品，也不是某条具体研究线的专题说明。它是 Promotion Decision 阶段的**标准执行合同**。

与周边文档的关系：

| 文档 | 角色 | 本 SOP 如何使用 |
|------|------|-----------------|
| `research_workflow_sop.md` | 全流程解释层 | 本 SOP 是其 §4.8 的执行展开 |
| `workflow_stage_gates.yaml` | Gate contract 真值 | 本 SOP 的 gate 规则必须与 YAML 一致；如有冲突，以 YAML 为准 |
| `docs/sop/failures/` | 各阶段失败处置 | Promotion Decision 无独立失败 SOP，回退在本阶段内部处理 |
| `docs/sop/review/` | 审查模板 | 提供 Promotion Decision gate 审查的具体检查模板 |

---

# 2. 阶段定位

## 2.1 核心问题

> **组织上是否允许这条研究线进入下一步，而不是研究员个人是否"觉得还能做"。**

Promotion Decision 不是一个技术验证阶段。它是一个**组织治理节点**：所有前序阶段产出的证据在这里被汇总评审，由组织而非个人给出正式结论。

## 2.2 为什么必须独立存在

如果没有正式的 Promotion Decision 阶段，会出现以下问题：

- 研究员自行判断"差不多了"就推进，缺少组织级的质量关卡；
- 正负结果的追溯链在推进过程中丢失；
- 主线与子谱系的关系没有书面记录，后续无法复盘；
- 异常收益复核未完成就进入下一阶段，风险敞口无法控制。

## 2.3 上游输入合同

Promotion Decision 依赖以下前序阶段的 frozen output：

- 所有前序阶段的 gate 结论与 artifact；
- 双引擎回测结果（如已完成）；
- 异常收益复核结论；
- 主线与子谱系的对比记录。

## 2.4 下游消费者

| 下游阶段 | 消费内容 |
|----------|----------|
| `08_shadow_admission` | `final_research_conclusion.md`, `dashboard_index.md`, `artifact_catalog.md` |
| `09_canary_production` | Promotion Decision 的正式 GO 结论 |
| 全流程各阶段 | `retry_record.md` 作为迭代历史的追溯文档 |

---

# 3. 适用范围

## 3.1 适用于

- 所有已完成前序研究阶段、准备申请进入 shadow 或更后续阶段的研究线；
- 主线研究与子谱系研究的组织级审批；
- 任何需要正式组织结论（GO / NO-GO / RETRY / CHILD LINEAGE）的场景。

## 3.2 不适用于

- 尚未完成异常收益复核的研究线（必须先关闭异常收益复核）；
- 纯探索性研究或概念验证（不需要经过正式 gate）；
- 已经在 shadow 或 production 阶段的研究线的日常运维。

---

# 4. 执行步骤

## 4.1 汇总前序阶段证据

- 收集所有前序阶段的 gate pass 记录与关键 artifact；
- 确认异常收益复核已关闭，结论已归档；
- 确认主线与子谱系（如有）的对比记录已完成。

## 4.2 编制正式研究结论

- 起草 `final_research_conclusion.md`，包括：
  - 研究问题回顾（与 Mandate 一致性校验）；
  - 各阶段关键发现与证据摘要；
  - 正式结论：GO / NO-GO / RETRY / CHILD LINEAGE；
  - 结论的依据与限制条件。

## 4.3 编制仪表板索引

- 起草 `dashboard_index.md`，索引所有关键指标、图表、报告的位置与版本。

## 4.4 编制重试记录

- 起草 `retry_record.md`，记录所有迭代历史，包括每次 RETRY 的原因、修改内容与结果。

## 4.5 编制 Artifact 目录与字段字典

- 起草 `artifact_catalog.md`，列出本研究线所有正式 artifact 的清单、版本与存储位置；
- 起草 `field_dictionary.md`，定义本研究线使用的所有关键字段。

## 4.6 主线与子谱系治理

- **子线在某阶段表现更好不自动替换主线**；
- 替换至少在同口径下完成比较，且不能跳过 holdout；
- 任何主线替换都应在 Promotion Decision 给出**书面记录**，包括替换理由、对比口径与 holdout 结果。

## 4.7 组织级审批

- 提交所有 required outputs 给 Reviewer / Referee；
- Reviewer 根据 Formal Gate 规则给出正式裁定；
- 记录裁定结论与裁定人。

---

# 5. 必备输出与 Artifact 规范

| Artifact | 格式 | 说明 |
|----------|------|------|
| `final_research_conclusion.md` | Markdown | 正式研究结论，含 GO/NO-GO/RETRY/CHILD LINEAGE 裁定 |
| `dashboard_index.md` | Markdown | 所有关键指标、图表、报告的索引 |
| `retry_record.md` | Markdown | 所有迭代历史与 RETRY 记录 |
| `artifact_catalog.md` | Markdown | 本研究线所有正式 artifact 清单 |
| `field_dictionary.md` | Markdown | 本研究线关键字段定义 |

所有 artifact 必须在 gate 判定前完成并归档。缺少任何一项即视为 gate 未通过。

---

# 6. Formal Gate 规则

## 6.1 通过条件（pass_all_of）

以下条件**全部满足**方可通过：

1. 已形成正式组织结论（GO / NO-GO / RETRY / CHILD LINEAGE 之一）；
2. Primary line 与 child lineage 关系已写清；
3. 正负结果都可追溯；
4. required_outputs 全部存在。

## 6.2 一票否决条件（fail_any_of）

以下任一条件触发即判定不通过：

1. 只说"看起来还不错"而不给正式结论；
2. 只保留最终通过的版本（删除或隐藏了失败版本的记录）；
3. 上游异常收益复核未关闭却直接给 GO。

## 6.3 允许的结论

| 结论 | 含义 |
|------|------|
| **GO** | 研究线通过，允许进入下一阶段 |
| **NO-GO** | 研究线终止，归档全部 artifact |
| **RETRY** | 研究线退回修改，需记录 retry 原因并更新 retry_record.md |
| **CHILD LINEAGE** | 当前主线保持不变，开设子谱系继续探索 |

---

# 7. Audit-Only 检查项

以下检查项不构成 gate 判定依据，但审计时会检查：

- [ ] `final_research_conclusion.md` 中的结论与前序阶段证据逻辑一致
- [ ] `retry_record.md` 完整记录了所有迭代，无遗漏
- [ ] 子谱系对比使用了同口径数据且未跳过 holdout
- [ ] 裁定人与裁定时间已记录
- [ ] artifact 命名与版本号符合团队规范

---

# 8. 常见陷阱与误区

## 8.1 只说"看起来还不错"不给正式结论

**问题**：研究员或 Reviewer 用模糊措辞代替正式裁定，导致下游阶段无法判断是否已获批准。

**纠正**：必须给出四种正式结论之一（GO / NO-GO / RETRY / CHILD LINEAGE），不接受任何模糊表述。

## 8.2 只保留最终通过的版本

**问题**：删除或隐藏中间失败的版本，破坏可追溯性。

**纠正**：所有版本（包括失败版本）必须归档，`retry_record.md` 必须完整记录每次迭代。

## 8.3 异常收益复核未完成时给 GO

**问题**：在上游异常收益复核尚未关闭的情况下，提前给出 GO 结论。

**纠正**：异常收益复核必须先关闭，结论已归档后，才能进入 Promotion Decision 的 GO 判定。

## 8.4 子线表现好就自动替换主线

**问题**：子谱系在某阶段表现优于主线，研究员未经正式流程直接替换。

**纠正**：替换必须在同口径下完成比较、不能跳过 holdout、必须在本阶段给出书面记录。

---

# 9. 失败与回退

Promotion Decision 无独立失败 SOP。回退在本阶段内部处理：

- **RETRY**：退回修改，更新 `retry_record.md`，重新进入本阶段执行步骤；
- **NO-GO**：研究线终止，归档全部 artifact，记录终止原因；
- **CHILD LINEAGE**：主线保持不变，子谱系按独立研究线流程重新进入管线。

任何回退都不删除已有 artifact，仅追加新版本。

---

# 10. 阶段专属要求

## 10.1 主线与子谱系治理纪律

这是 Promotion Decision 阶段最核心的治理要求（源自 §4.8）：

1. **子线在某阶段更好不自动替换主线**——表现优劣不是替换的充分条件；
2. **替换至少在同口径下完成比较**——数据口径、时间窗口、评价指标必须对齐；
3. **不能跳过 holdout**——即使子线在 in-sample 表现更好，也必须在 holdout 上验证；
4. **任何主线替换都应在 Promotion Decision 给出书面记录**——包括替换理由、对比口径、holdout 结果、裁定人与裁定时间。

## 10.2 组织结论 vs 个人判断

Promotion Decision 的结论是**组织级**的，不是研究员个人的。即使研究员认为"还能做"，如果组织判定 NO-GO，研究线即终止。反之亦然。

---

# 11. Checklist 速查表

## 11.1 执行前

- [ ] 所有前序阶段 gate 已通过
- [ ] 异常收益复核已关闭并归档
- [ ] 主线与子谱系对比记录已完成（如适用）

## 11.2 执行中

- [ ] `final_research_conclusion.md` 已起草，含正式结论
- [ ] `dashboard_index.md` 已编制
- [ ] `retry_record.md` 已编制，记录完整
- [ ] `artifact_catalog.md` 已编制
- [ ] `field_dictionary.md` 已编制
- [ ] 主线替换有书面记录（如适用）

## 11.3 Gate 判定

- [ ] 正式结论已给出（GO / NO-GO / RETRY / CHILD LINEAGE）
- [ ] Primary line 与 child lineage 关系已写清
- [ ] 正负结果都可追溯
- [ ] required_outputs 全部存在
- [ ] 未触发任何一票否决条件

## 11.4 归档

- [ ] 所有 artifact 已归档至指定位置
- [ ] 裁定人与裁定时间已记录
- [ ] 版本号已更新

---

# 12. 关联文档

| 文档 | 位置 | 说明 |
|------|------|------|
| `research_workflow_sop.md` | `docs/sop/main-flow/` | 全流程 SOP，本阶段对应 §4.8 |
| `workflow_stage_gates.yaml` | 项目根目录 / 配置目录 | Gate contract 真值来源 |
| `08_shadow_admission_sop_cn.md` | `docs/sop/main-flow/` | 下游阶段 SOP |
| `artifact_catalog.md` | 各研究线目录 | Artifact 清单模板 |
| `field_dictionary.md` | 各研究线目录 | 字段定义模板 |

---

> **优先级说明**：如果本文档与 `workflow_stage_gates.yaml` 存在差异，以 YAML 为准。
