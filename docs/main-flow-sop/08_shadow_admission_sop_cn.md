# 08_shadow_admission_sop

Doc ID: SOP-SHADOW-v1.0
Title: `08_shadow_admission_sop` — Shadow Admission 阶段标准操作流程（机构级）
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

**Shadow Admission 阶段应该如何执行、交什么 artifact、怎么判 gate。**

它不是主流程 SOP 的替代品，也不是某条具体研究线的专题说明。它是 Shadow Admission 阶段的**标准执行合同**。

与周边文档的关系：

| 文档 | 角色 | 本 SOP 如何使用 |
|------|------|-----------------|
| `research_workflow_sop.md` | 全流程解释层 | 本 SOP 是其 §4.9 的执行展开 |
| `workflow_stage_gates.yaml` | Gate contract 真值 | 本 SOP 的 gate 规则必须与 YAML 一致；如有冲突，以 YAML 为准 |
| `第二层-阶段失败 sop/07_shadow_failure_sop_cn.md` | Shadow 失败处置 | Shadow 运行期间失败的回退与处置纪律 |
| `第四层-check/` | 审查模板 | 提供 Shadow Admission gate 审查的具体检查模板 |

---

# 2. 阶段定位

## 2.1 核心问题

> **这条研究线在完成双引擎回测验证之后，是否具备进入 shadow 的治理条件。**

Shadow Admission 不是在验证策略是否"有效"——那是前序阶段的责任。它回答的是：**在治理层面，监控、回滚、容量控制等准入条件是否已经就位。**

## 2.2 为什么必须独立存在

Shadow 只是更高一级的准入，**不是最终上线批准**。它与 Production 之间有本质区别：

- Shadow 运行在模拟或受限真实环境中，目的是验证策略在非回测条件下的表现；
- Shadow 期间需要独立的监控指标与回滚条件，不能沿用回测期间的标准；
- 没有 Shadow Admission 的治理关卡，策略可能在没有监控的情况下进入真实环境。

如果跳过这个阶段：

- 没有监控指标就进入实盘，异常无法被及时发现；
- 没有回滚条件就进入实盘，异常发现了也无法及时止损；
- 容量假设未经映射就进入实盘，资金规模可能超出策略承载范围。

## 2.3 上游输入合同

Shadow Admission 依赖以下前序阶段的 frozen output：

- Promotion Decision 的正式 GO 结论（`final_research_conclusion.md`）；
- 双引擎回测结果与一致性复核结论；
- Backtest 阶段 capacity_review 的结论；
- 所有前序阶段的 artifact_catalog。

## 2.4 下游消费者

| 下游阶段 | 消费内容 |
|----------|----------|
| Shadow 运行期 | `monitoring_spec.md`, `rollback_playbook.md`, `shadow_run_manifest.json` |
| `09_canary_production` | `shadow_gate_decision.md`, shadow 期间的运行记录与监控数据 |
| 全流程各阶段 | `artifact_catalog.md`, `field_dictionary.md` |

---

# 3. 适用范围

## 3.1 适用于

- 所有已通过 Promotion Decision（GO 结论）、准备进入 shadow 运行的研究线；
- 需要从回测环境过渡到 shadow 环境的策略；
- 任何需要冻结监控指标与回滚条件的 shadow 准入场景。

## 3.2 不适用于

- Promotion Decision 尚未给出正式 GO 的研究线（必须先完成 Promotion Decision）；
- 已经在 shadow 运行中的策略（运行期间问题参见 `07_shadow_failure_sop_cn.md`）；
- 直接从回测跳到 production 的场景（**禁止跳过 shadow**）。

---

# 4. 执行步骤

## 4.1 确认上游准入条件

- 确认 Promotion Decision 已给出正式 GO；
- 确认双引擎回测结果可用且一致性复核已完成；
- 确认 Backtest 阶段的 capacity_review 结论已归档。

## 4.2 双引擎结果一致性复核

- 补充或确认双引擎（如 Zipline + 自研引擎）结果的一致性复核结论；
- 记录一致性偏差范围与可接受阈值；
- 如偏差超出阈值，必须给出原因分析与处置方案。

## 4.3 容量假设的治理级复核

- 对 Backtest 阶段的 capacity_review 进行治理级复核；
- 将容量假设映射为 shadow 期间的具体操作条件：
  - **监控阈值**：容量使用率超过多少触发预警；
  - **降额动作**：预警触发后的具体降额步骤与幅度；
  - **回滚触发条件**：容量异常达到什么程度触发全量回滚。

## 4.4 冻结监控指标与回滚条件

- 编制 `monitoring_spec.md`，定义 shadow 期间所有监控指标，包括：
  - 指标名称、计算公式、采样频率；
  - 预警阈值与升级路径；
  - 数据来源与延迟容忍度。
- 编制 `rollback_playbook.md`，定义回滚条件与操作步骤，包括：
  - 触发回滚的具体条件（定量）；
  - 回滚操作的逐步流程；
  - 回滚后的验证步骤；
  - 回滚责任人与联系方式。

## 4.5 编制 Shadow 期间异常处理规则

- 定义 shadow 期间可能出现的异常类型与分级；
- 每种异常对应的处理流程、响应时限、升级路径；
- 记录到 `rollback_playbook.md` 或独立的异常处理附件中。

## 4.6 编制 Shadow 运行清单

- 起草 `shadow_run_manifest.json`，定义 shadow 运行的完整配置：
  - 策略标识、版本、运行环境；
  - 资金规模、标的范围、时间窗口；
  - 监控接入点与告警通道。

## 4.7 编制 Artifact 目录与字段字典

- 更新 `artifact_catalog.md`，补充本阶段新增的 artifact；
- 更新 `field_dictionary.md`，补充本阶段新增的字段定义。

## 4.8 组织级审批

- 提交所有 required outputs 给 Reviewer / Referee；
- Reviewer 根据 Formal Gate 规则给出正式裁定；
- 记录裁定结论与裁定人。

---

# 5. 必备输出与 Artifact 规范

| Artifact | 格式 | 说明 |
|----------|------|------|
| `shadow_gate_decision.md` | Markdown | Shadow 准入的正式裁定文档 |
| `monitoring_spec.md` | Markdown | Shadow 期间所有监控指标定义 |
| `rollback_playbook.md` | Markdown | 回滚条件与操作步骤 |
| `shadow_run_manifest.json` | JSON | Shadow 运行的完整配置清单 |
| `artifact_catalog.md` | Markdown | 本研究线所有正式 artifact 清单（更新版） |
| `field_dictionary.md` | Markdown | 本研究线关键字段定义（更新版） |

所有 artifact 必须在 gate 判定前完成并归档。缺少任何一项即视为 gate 未通过。

---

# 6. Formal Gate 规则

## 6.1 通过条件（pass_all_of）

以下条件**全部满足**方可通过：

1. 双引擎结果一致性已复核；
2. 成本与容量假设已复核；
3. Capacity review 已映射成 shadow 期间的监控 / 降额 / 回滚条件；
4. 监控指标与回滚条件已冻结；
5. Shadow 期间异常处理规则已写清。

## 6.2 一票否决条件（fail_any_of）

以下任一条件触发即判定不通过：

1. 没有监控指标就进入 shadow；
2. 没有回滚条件就进入 shadow；
3. Promotion 还未正式 GO。

## 6.3 允许的结论

| 结论 | 含义 |
|------|------|
| **GO** | 研究线通过 shadow 准入，允许进入 shadow 运行 |
| **NO-GO** | 研究线未通过 shadow 准入，退回修改或终止 |
| **PASS FOR RETRY** | 条件性通过，需补充特定内容后重新提交 |
| **CHILD LINEAGE** | 主线保持不变，子谱系按独立研究线流程处理 |

---

# 7. Audit-Only 检查项

以下检查项不构成 gate 判定依据，但审计时会检查：

- [ ] 双引擎一致性偏差在可接受范围内且有书面分析
- [ ] 监控指标覆盖了所有关键风险维度（收益、回撤、容量、延迟）
- [ ] 回滚 playbook 包含完整的逐步操作流程
- [ ] Shadow 运行配置与 Backtest 配置的差异已记录并解释
- [ ] 异常处理规则覆盖了所有分级场景
- [ ] 裁定人与裁定时间已记录

---

# 8. 常见陷阱与误区

## 8.1 把 Shadow 等同于 Production

**问题**：认为通过 Shadow Admission 就等于批准上线，跳过后续 Canary / Production 阶段。

**纠正**：Shadow 只是更高一级的准入，不是最终上线批准。Shadow 之后仍需经过 Canary / Production 阶段。

## 8.2 没有监控指标就进入 Shadow

**问题**：急于推进，在监控指标尚未定义的情况下就启动 shadow 运行。

**纠正**：监控指标必须在 gate 判定前冻结。没有监控的 shadow 运行等于盲跑。

## 8.3 没有回滚条件就进入 Shadow

**问题**：认为"出了问题再说"，没有预先定义回滚条件与操作步骤。

**纠正**：回滚 playbook 必须在 gate 判定前冻结，且包含定量触发条件与逐步操作流程。

## 8.4 容量假设未映射到 Shadow 操作条件

**问题**：Backtest 阶段的 capacity_review 结论停留在纸面，未转化为 shadow 期间的监控阈值、降额动作、回滚触发条件。

**纠正**：必须将容量假设逐一映射为 shadow 期间的可操作条件，并写入 `monitoring_spec.md` 和 `rollback_playbook.md`。

---

# 9. 失败与回退

Shadow Admission 的失败处置参见：

- **失败 SOP**：`第二层-阶段失败 sop/07_shadow_failure_sop_cn.md`

本阶段内部的回退规则：

- **NO-GO**：退回前序阶段修改，或终止研究线；
- **PASS FOR RETRY**：补充缺失内容后重新提交，需在 retry 记录中注明补充内容；
- **CHILD LINEAGE**：主线保持不变，子谱系按独立研究线流程重新进入管线。

任何回退都不删除已有 artifact，仅追加新版本。

---

# 10. 阶段专属要求

## 10.1 双引擎结果一致性复核

Shadow Admission 必须补充双引擎结果一致性复核结论。这不是简单的"两个引擎跑了结果差不多"，而是需要：

- 明确偏差的定量范围；
- 分析偏差来源（数据对齐、成交假设、费用模型等）；
- 给出偏差是否可接受的正式结论。

## 10.2 容量治理级复核

Backtest 阶段的 capacity_review 在本阶段需要被提升到治理级：

- 不仅是"容量够不够"的回答，而是"容量异常时怎么办"的操作方案；
- 必须包含：监控阈值、降额动作、回滚触发条件三项完整映射。

## 10.3 Shadow 不是 Production

Shadow Admission 的所有输出都是为 shadow 运行服务的，不能直接套用到 production。进入 production 需要经过独立的 `09_canary_production` 阶段。

---

# 11. Checklist 速查表

## 11.1 执行前

- [ ] Promotion Decision 已给出正式 GO
- [ ] 双引擎回测结果可用
- [ ] Backtest 阶段 capacity_review 结论已归档

## 11.2 执行中

- [ ] 双引擎结果一致性复核结论已完成
- [ ] 容量假设已映射为 shadow 期间的监控/降额/回滚条件
- [ ] `monitoring_spec.md` 已编制并冻结
- [ ] `rollback_playbook.md` 已编制并冻结
- [ ] Shadow 期间异常处理规则已写清
- [ ] `shadow_run_manifest.json` 已编制
- [ ] `artifact_catalog.md` 已更新
- [ ] `field_dictionary.md` 已更新

## 11.3 Gate 判定

- [ ] pass_all_of 五项条件全部满足
- [ ] 未触发任何一票否决条件
- [ ] 正式结论已给出（GO / NO-GO / PASS FOR RETRY / CHILD LINEAGE）
- [ ] 裁定人与裁定时间已记录

## 11.4 归档

- [ ] 所有 artifact 已归档至指定位置
- [ ] `shadow_gate_decision.md` 已完成并签发
- [ ] 版本号已更新

---

# 12. 关联文档

| 文档 | 位置 | 说明 |
|------|------|------|
| `research_workflow_sop.md` | `第一层-主流程sop/` | 全流程 SOP，本阶段对应 §4.9 |
| `workflow_stage_gates.yaml` | 项目根目录 / 配置目录 | Gate contract 真值来源 |
| `07_promotion_decision_sop_cn.md` | `第一层-主流程sop/` | 上游阶段 SOP |
| `09_canary_production_sop_cn.md` | `第一层-主流程sop/` | 下游阶段 SOP |
| `07_shadow_failure_sop_cn.md` | `第二层-阶段失败 sop/` | Shadow 失败处置 SOP |
| `artifact_catalog.md` | 各研究线目录 | Artifact 清单模板 |
| `field_dictionary.md` | 各研究线目录 | 字段定义模板 |

---

> **优先级说明**：如果本文档与 `workflow_stage_gates.yaml` 存在差异，以 YAML 为准。
