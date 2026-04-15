# 09_canary_production_sop

Doc ID: SOP-CANARY-v1.0
Title: `09_canary_production_sop` — Canary / Production 阶段标准操作流程（机构级）
Date: 2026-03-27
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev / Risk Control
Audience:
- Research
- Quant Dev
- Risk Control
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `workflow_stage_gates.yaml`

---

# 1. 文档目的

本 SOP 只回答一件事：

**Canary / Production 阶段应该如何执行、交什么 artifact、怎么判 gate。**

它不是主流程 SOP 的替代品，也不是某条具体研究线的专题说明。它是 Canary / Production 阶段的**标准执行合同**。

与周边文档的关系：

| 文档 | 角色 | 本 SOP 如何使用 |
|------|------|-----------------|
| `research_workflow_sop.md` | 全流程解释层 | 本 SOP 是其 §4.10 的执行展开 |
| `workflow_stage_gates.yaml` | Gate contract 真值 | 本 SOP 的 gate 规则必须与 YAML 一致；如有冲突，以 YAML 为准 |
| `docs/sop/failures/` | 各阶段失败处置 | 本阶段无独立失败 SOP |
| `docs/sop/review/` | 审查模板 | 提供 Canary / Production gate 审查的具体检查模板 |

---

# 2. 阶段定位

## 2.1 核心问题

> **在小规模真实环境和最终投产审批下，这条策略是否仍然可接受。**

Canary / Production 不再是研究阶段。它回答的是：**策略在经过 shadow 验证后，是否具备在真实环境中运行的全部工程与风控条件。**

## 2.2 为什么必须独立存在

本阶段**已经超出研究本身，属于更高等级的工程与风控治理**。

- Shadow 验证的是策略在非回测条件下的表现，但 shadow 环境仍有保护屏障；
- Canary 是在真实环境中以小规模运行，验证策略在真实交易条件下的行为；
- Production 是全量投产，需要完整的运维体系支撑。

如果跳过这个阶段：

- 没有 kill switch 或 rollback playbook，异常发生时无法紧急停止；
- 没有生产 owner 和升级路径，问题无人负责、无人升级；
- 试图跳过 shadow 直接进入 production，违反逐级准入纪律。

## 2.3 上游输入合同

Canary / Production 依赖以下前序阶段的 frozen output：

- Shadow Admission 的正式 GO 结论（`shadow_gate_decision.md`）；
- Shadow 运行期间的监控数据与运行报告；
- Shadow 期间的异常记录与处置结果；
- 所有前序阶段的 artifact_catalog。

## 2.4 下游消费者

| 下游消费者 | 消费内容 |
|------------|----------|
| 生产运维团队 | `production_runbook.md`, `production_rollback_playbook.md` |
| 风控团队 | `canary_metrics_spec.md`, `canary_gate_decision.md` |
| 全流程各阶段 | `artifact_catalog.md`, `field_dictionary.md` |

---

# 3. 适用范围

## 3.1 适用于

- 所有已通过 Shadow Admission（GO 结论）且 shadow 运行期无重大异常的研究线；
- 需要从 shadow 环境过渡到 canary 或 production 环境的策略；
- 任何需要最终投产审批的场景。

## 3.2 不适用于

- Shadow Admission 尚未给出正式 GO 的研究线；
- Shadow 运行期间存在未关闭的重大异常；
- 试图跳过 shadow 直接进入 production 的场景（**严格禁止**）。

---

# 4. 执行步骤

## 4.1 确认上游准入条件

- 确认 Shadow Admission 已给出正式 GO；
- 确认 shadow 运行期间无未关闭的重大异常；
- 确认 shadow 运行数据已归档。

## 4.2 定义最终运行边界

- 明确策略的最终运行边界：
  - 标的范围、资金规模、杠杆上限；
  - 运行时段、频率、最大持仓；
  - 成本假设与滑点容忍度。

## 4.3 指定生产 Owner 与升级路径

- 指定策略的生产 owner（不是研究员，是运维/风控负责人）；
- 定义问题升级路径：一级告警 → 二级响应 → 三级决策；
- 记录所有相关人员的联系方式与值班安排。

## 4.4 定义 Kill Switch

- 明确 kill switch 的触发条件（定量）；
- 定义 kill switch 的操作步骤与授权流程；
- 确保 kill switch 可在预设时间内完成执行。

## 4.5 冻结 Canary 监控指标

- 编制 `canary_metrics_spec.md`，定义 canary 阶段所有监控指标：
  - 指标名称、计算公式、采样频率；
  - 预警阈值与升级路径；
  - 与 shadow 期间指标的对比与差异说明。

## 4.6 编制生产 Runbook 与回滚 Playbook

- 编制 `production_runbook.md`，定义日常运维操作：
  - 启动 / 停止 / 重启流程；
  - 日常检查项与频率；
  - 常见问题的标准处置流程。
- 编制 `production_rollback_playbook.md`，定义生产回滚方案：
  - 触发回滚的具体条件（定量）；
  - 回滚操作的逐步流程；
  - 回滚后的验证步骤与恢复方案；
  - 回滚责任人与授权流程。

## 4.7 编制 Artifact 目录与字段字典

- 更新 `artifact_catalog.md`，补充本阶段新增的 artifact；
- 更新 `field_dictionary.md`，补充本阶段新增的字段定义。

## 4.8 组织级审批

- 提交所有 required outputs 给 Reviewer / Referee / Risk Control；
- Reviewer 根据 Formal Gate 规则给出正式裁定；
- 记录裁定结论、裁定人与裁定时间。

---

# 5. 必备输出与 Artifact 规范

| Artifact | 格式 | 说明 |
|----------|------|------|
| `canary_gate_decision.md` | Markdown | Canary / Production 准入的正式裁定文档 |
| `production_runbook.md` | Markdown | 生产环境日常运维操作手册 |
| `production_rollback_playbook.md` | Markdown | 生产环境回滚方案 |
| `canary_metrics_spec.md` | Markdown | Canary 阶段所有监控指标定义 |
| `artifact_catalog.md` | Markdown | 本研究线所有正式 artifact 清单（更新版） |
| `field_dictionary.md` | Markdown | 本研究线关键字段定义（更新版） |

所有 artifact 必须在 gate 判定前完成并归档。缺少任何一项即视为 gate 未通过。

---

# 6. Formal Gate 规则

## 6.1 通过条件（pass_all_of）

以下条件**全部满足**方可通过：

1. 最终运行边界 / owner / 升级路径 / kill switch 已明确；
2. Canary 监控项和生产回滚方案已冻结。

## 6.2 一票否决条件（fail_any_of）

以下任一条件触发即判定不通过：

1. 没有 kill switch 或 rollback playbook；
2. 没有生产 owner 和升级路径；
3. 试图跳过 shadow 直接进 production。

## 6.3 允许的结论

| 结论 | 含义 |
|------|------|
| **GO** | 研究线通过，允许进入 canary 运行或正式投产 |
| **NO-GO** | 研究线未通过，退回修改或终止 |
| **PASS FOR RETRY** | 条件性通过，需补充特定内容后重新提交 |
| **CHILD LINEAGE** | 主线保持不变，子谱系按独立研究线流程处理 |

---

# 7. Audit-Only 检查项

以下检查项不构成 gate 判定依据，但审计时会检查：

- [ ] Kill switch 可在预设时间内完成执行（已验证）
- [ ] 生产 owner 非研究员本人（职责分离）
- [ ] 升级路径覆盖了非工作时段的值班安排
- [ ] 回滚 playbook 包含完整的逐步操作流程
- [ ] Canary 监控指标与 shadow 期间指标的差异已记录并解释
- [ ] 裁定人与裁定时间已记录

---

# 8. 常见陷阱与误区

## 8.1 没有 Kill Switch 就投产

**问题**：认为"出了问题再想办法"，没有预先定义紧急停止机制。

**纠正**：Kill switch 是投产的硬性前提。必须包含定量触发条件、操作步骤与授权流程。

## 8.2 没有生产 Owner 和升级路径

**问题**：研究员自己兼任生产 owner，或者没有明确的问题升级路径。

**纠正**：生产 owner 必须是运维/风控负责人，不能是研究员本人。升级路径必须覆盖所有时段。

## 8.3 试图跳过 Shadow 直接进 Production

**问题**：认为回测结果足够好，不需要 shadow 阶段的验证。

**纠正**：逐级准入纪律不可违反。必须先通过 Shadow Admission 和 shadow 运行期，才能进入 Canary / Production。

## 8.4 把 Canary 当 Shadow 用

**问题**：在 canary 阶段仍然在调试策略参数，而不是验证生产就绪性。

**纠正**：Canary 阶段的目的是验证策略在真实环境中的工程与风控条件，不是继续优化策略。

---

# 9. 失败与回退

本阶段无独立失败 SOP。回退在本阶段内部处理：

- **NO-GO**：退回前序阶段修改，或终止研究线，归档全部 artifact；
- **PASS FOR RETRY**：补充缺失内容后重新提交，需记录补充内容；
- **CHILD LINEAGE**：主线保持不变，子谱系按独立研究线流程重新进入管线。

任何回退都不删除已有 artifact，仅追加新版本。

---

# 10. 阶段专属要求

## 10.1 超出研究范畴

本阶段已经超出研究本身，属于更高等级的工程与风控治理。这意味着：

- 审批权限高于前序研究阶段；
- 需要工程团队和风控团队的联合签发；
- 研究团队在本阶段的角色是配合而非主导。

## 10.2 Kill Switch 的强制性

没有 kill switch 的策略不允许进入任何真实环境运行。Kill switch 必须满足：

- 触发条件是定量的，不依赖人为判断；
- 操作步骤是预定义的，不需要临时决策；
- 执行时间是可控的，有明确的 SLA。

## 10.3 职责分离

生产 owner 与研究员必须是不同的人。这是基本的风控纪律：

- 研究员负责策略的研究与验证；
- 生产 owner 负责策略的运维与风控；
- 两者之间通过 runbook 和 playbook 进行职责交接。

---

# 11. Checklist 速查表

## 11.1 执行前

- [ ] Shadow Admission 已给出正式 GO
- [ ] Shadow 运行期间无未关闭的重大异常
- [ ] Shadow 运行数据已归档

## 11.2 执行中

- [ ] 最终运行边界已定义
- [ ] 生产 owner 已指定（非研究员本人）
- [ ] 升级路径已定义（覆盖所有时段）
- [ ] Kill switch 已定义（含定量触发条件）
- [ ] `canary_metrics_spec.md` 已编制并冻结
- [ ] `production_runbook.md` 已编制
- [ ] `production_rollback_playbook.md` 已编制并冻结
- [ ] `artifact_catalog.md` 已更新
- [ ] `field_dictionary.md` 已更新

## 11.3 Gate 判定

- [ ] pass_all_of 条件全部满足
- [ ] 未触发任何一票否决条件
- [ ] 正式结论已给出（GO / NO-GO / PASS FOR RETRY / CHILD LINEAGE）
- [ ] 裁定人与裁定时间已记录

## 11.4 归档

- [ ] 所有 artifact 已归档至指定位置
- [ ] `canary_gate_decision.md` 已完成并签发
- [ ] 版本号已更新

---

# 12. 关联文档

| 文档 | 位置 | 说明 |
|------|------|------|
| `research_workflow_sop.md` | `docs/sop/main-flow/` | 全流程 SOP，本阶段对应 §4.10 |
| `workflow_stage_gates.yaml` | 项目根目录 / 配置目录 | Gate contract 真值来源 |
| `08_shadow_admission_sop_cn.md` | `docs/sop/main-flow/` | 上游阶段 SOP |
| `07_shadow_failure_sop_cn.md` | `docs/sop/failures/` | Shadow 失败处置 SOP |
| `artifact_catalog.md` | 各研究线目录 | Artifact 清单模板 |
| `field_dictionary.md` | 各研究线目录 | 字段定义模板 |

---

> **优先级说明**：如果本文档与 `workflow_stage_gates.yaml` 存在差异，以 YAML 为准。
