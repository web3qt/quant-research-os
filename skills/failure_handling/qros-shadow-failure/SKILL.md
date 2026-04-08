---
name: qros-shadow-failure
description: Use when failure_class is determined for shadow stage. Runs the full shadow triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, produces stage-specific failure artifacts, and outputs both formal decision AND shadow_status (continue_shadow/pause_shadow/terminate_shadow).
---

# QROS Shadow Failure Handler

## Purpose

本 skill 处置 `07_shadow` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `07_shadow` 五步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. **额外输出 `shadow_status`**（`continue_shadow` / `pause_shadow` / `terminate_shadow`）
6. 输出标准产物
7. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`07_shadow` 的职责不是再研究 alpha，而是：在接近实盘的条件下验证信号、执行器、风控器、下单路径、监控链路是否一致工作；评估 shadow 与 `05_backtest / 06_holdout` 的偏差来源；检查成交质量、容量、滑点、时延、下单失败与告警是否可控；为正式 seed / production 给出运营层证据。

失败属于**运营层治理失败**或**真实世界可执行性失败**。不允许把 shadow 当成第三次开发层。

## Failure Classes

### `OPS_FAIL`
定义：当前失败首先来自运营、基础设施或流程问题，而不是策略本身。
典型：数据源抖动、消息丢失、时钟不同步 / API 不稳定、下单失败率高 / 监控告警失灵 / 订单日志无法完整复原 / 同策略逻辑在 replay 中正常但 shadow 中异常

### `EXECUTION_FAIL`
定义：研究与 holdout 仍有一定依据，但真实执行质量不足以支撑上线。
典型：实际滑点显著高于假设 / 队列损失、部分成交、撤单成本明显 / 下单路径导致延迟错过主要 alpha 窗口 / 实际净收益被执行损耗吃掉

### `CAPACITY_FAIL`
定义：策略在小规模影子仓位下可行，但在接近目标规模时容量不足，无法经济上线。
典型：shadow 小规模正常，稍放大后明显恶化 / 某些时段或 symbol 无法承接目标仓位 / 市场冲击、排队与流动性约束显著超出预期

### `GENERALIZATION_FAIL`
定义：策略在 holdout 通过，但在接近真实交易环境后，alpha 行为本身无法重现。
典型：不是单纯执行或容量问题，连 gross 也明显弱化 / 实时环境中 trade distribution 与 holdout 差异过大 / 真实盘口条件下核心结构消失 / shadow 暴露出 holdout 仍高估了可实现 alpha

### `THESIS_FAIL`
定义：shadow 表明该策略在接近真实世界条件下不具备上线价值，主假设实质失效。
典型：多轮修复后仍不具经济意义 / alpha 太薄无法覆盖真实执行摩擦 / 需要大量补丁才能勉强存活 / 当前线在运营层已不具继续价值

### `SCOPE_FAIL`
定义：若要让 shadow 成立，必须改变研究主问题、执行语义、风控角色或策略身份。
典型：从 alpha 线改成 execution-only 线 / 从主策略改成组合辅助信号 / 从原下单语义改成完全不同执行器 / 从"风险过滤器"变成"主信号门控器"

## Triage Sequence（五步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `shadow_failure_freeze.md`（含 lineage_id / run_id / stage / 已知违规点）
- `shadow_vs_holdout_compare.parquet`
- `execution_drift_report.md`
- `ops_incident_log.md`
- `repro_manifest.json`
- `review_notes.md`

### Step 1. 先排运营与执行 Correctness（优先）

固定顺序检查：
- 数据链路是否完整
- 下单与成交日志是否可重建
- 时钟 / 延迟 / API / 风控是否正常
- 订单状态机是否符合合同
- 关键交易样本是否可复盘
- 当前偏差是运营问题、执行问题还是策略问题

失败映射：
- 基础设施 / 流程问题 → `OPS_FAIL`
- 执行器 / 下单质量问题 → `EXECUTION_FAIL`

### Step 2. 运营层归因

只有 correctness 过关，才允许继续判断：
- 放大后劣化、目标规模不可行 → `CAPACITY_FAIL`
- 真实环境下连 gross 都明显弱化 → `GENERALIZATION_FAIL`
- 多轮后仍无上线价值 → `THESIS_FAIL`

### Step 3. Research Boundary Audit

检查 shadow 是否被拿来偷偷换题：
- 是否把主策略降级成辅助信号
- 是否改写执行语义、风控角色或策略身份
- 是否让新的过滤器成为主 gate
- 是否以"运营修复"为名重写 alpha 身份

失败映射：→ `SCOPE_FAIL`，停止原线推进

### Step 4. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：`THESIS_FAIL` / `SCOPE_FAIL` / `GENERALIZATION_FAIL` 在合理修复后无改善 / `OPS_FAIL` 或 `EXECUTION_FAIL` 导致结果完全不可信
动作：当前 stage 终止，宣告 `terminate_shadow` 或 `pause_shadow`，不得继续运行

#### `FAIL-SOFT`（需 Referee 判断）
条件：`OPS_FAIL` / `EXECUTION_FAIL` / `CAPACITY_FAIL` 可定位，或仅缺 drift sidecar / ops review 闭环
动作：Referee 判定是否允许 `PASS FOR RETRY`，宣告 `pause_shadow`

#### `PASS_WITH_RESTRICTIONS`
仅当：偏差轻微、问题边界清晰、不需要暂停运行、Reviewer 接受限制条件

### Step 5. 映射 Formal Decision 与 Shadow Status

**Formal Decision**（必选其一）：
- `PASS FOR RETRY` — shadow 主结论已清楚，仅缺 ops / drift sidecar 闭环
- `RETRY` — 问题明确，回退层级清晰，修复不改变研究身份
- `NO-GO` — 真实世界条件下不具备上线价值
- `CHILD LINEAGE` — 修复动作实质改变研究主问题、执行语义或策略身份

**Shadow Status**（必须同时给出）：
- `continue_shadow` — 偏差轻微、问题清晰且不需要暂停运行
- `pause_shadow` — 当前需要暂停孵化，先修复再继续
- `terminate_shadow` — 原线 shadow 终止，不再继续运行

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision | 默认 shadow_status |
|---|---|---|---|
| `OPS_FAIL` | `07_shadow` | `PASS FOR RETRY` 或 `RETRY` | `pause_shadow` |
| `EXECUTION_FAIL` | `07_shadow` | `RETRY` | `pause_shadow` |
| `CAPACITY_FAIL` | `07_shadow` 或 `00_mandate` | `RETRY`、`NO-GO` 或 `CHILD LINEAGE` | `pause_shadow` 或 `terminate_shadow` |
| `GENERALIZATION_FAIL` | `05_backtest` 或 `06_holdout` | `RETRY` 或 `NO-GO` | `pause_shadow` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` | `terminate_shadow` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` | `terminate_shadow`（原线） |

## Allowed / Forbidden Modifications

**允许修改：**
- 数据链路、下单链路、监控告警、日志与复盘工具
- 下单节奏、订单类型、撤单与重试策略
- 成本模型与 execution drift 审计
- 容量门槛、session / liquidity bucket 约束
- 合法回退到 `05/06` 重审真实可执行条件与样本外证据

**禁止修改：**
- 用 shadow 结果反向定义 alpha
- 静默替换 `03/04/05/06` 冻结对象
- 把 shadow 当成无限优化池
- 借运营修复之名重写策略身份
- 跳过失败冻结，直接覆盖旧结果

## Retry Discipline

每次 retry 必须写清：

```yaml
failure_class: <class>
root_cause_hypothesis: <具体假设>
rollback_stage: <stage>
allowed_modifications:
  - <modification>
forbidden_modifications:
  - redefine_alpha_in_shadow
  - change_whitelist_or_best_h
  - change_strategy_identity
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - shadow_risk_role
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- 超过次数仍无改善，必须升级为 `NO-GO` 或 `CHILD LINEAGE`
- 不允许让 shadow 变成另一个 backtest

## Required Artifacts（本 skill 产出）

- `shadow_failure_freeze.md`
- `shadow_vs_holdout_compare.parquet`
- `execution_drift_report.md`
- `ops_incident_log.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — shadow 主结论已清楚，仅缺 ops / drift sidecar 或 review 闭环
- **`RETRY`** — 问题明确，回退层级清晰，修复不改变研究身份
- **`NO-GO`** — 接近真实世界条件下不具备上线价值，多轮合法修复后仍无继续价值
- **`CHILD LINEAGE`** — 修复动作实质改变研究主问题、执行语义、风控角色或策略身份

## Shadow Status Mapping（每次必须同时输出）

- **`continue_shadow`** — 偏差轻微、问题边界清晰、不需要暂停运行
- **`pause_shadow`** — 当前需要暂停孵化，先修复再继续（对应 OPS_FAIL / EXECUTION_FAIL / CAPACITY_FAIL / GENERALIZATION_FAIL）
- **`terminate_shadow`** — 原线 shadow 终止，不再继续运行（对应 THESIS_FAIL / SCOPE_FAIL）

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- `shadow_status`
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
