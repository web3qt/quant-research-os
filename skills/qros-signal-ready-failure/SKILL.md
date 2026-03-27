---
name: qros-signal-ready-failure
description: Use when failure_class is determined for signal_ready stage. Runs the full signal_ready triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure artifacts.
---

# QROS Signal Ready Failure Handler

## Purpose

本 skill 处置 `02_signal_ready` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `02_signal_ready` 五步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`02_signal_ready` 的职责不是证明策略有效，而是把 `00_mandate` 声明的研究对象物化成**可复验字段**，确保字段表达式、窗口、滞后、样本门槛、质量字段满足合同，隔离所有会污染后续统计证据的时间因果错误。

失败属于**研究对象物化失败**，因为错误字段会直接污染后续冻结、证据与回测。

## Failure Classes

### `FORMULA_FAIL`
定义：信号表达式、窗口边界、分母、门槛或样本条件实现错误。
典型：`DC_up`/`DC_down` 分母错 / `ResidualZ` 标准化窗口不对 / `OB/OS` 阈值实现与合同不符 / `DownLinkGap` 方向写反

### `TEMPORAL_LEAK_FAIL`
定义：信号使用了 `t` 时点不可见信息，或提前消费未来冻结对象。
典型：使用未来 bar 计算当前信号 / 在 `02` 层使用 `best_h`、test quantile、正式白名单 / 消费 `04_test_evidence` 结果

### `SEMANTIC_DRIFT_FAIL`
定义：字段名看似不变，但字段语义已不再回答原研究问题。
典型：名叫 `ResidualZ` 实际加入未声明过滤 / 用多层 if-rule 把字段变成后验收益优化器

### `QUALITY_GATE_FAIL`
定义：信号物化成功，但质量门禁不足，无法安全支持下游消费。
典型：缺少 `low_sample` / 缺少 `missing_rate_window` / `pair_missing` 未正确传播 / 下游无法拒绝劣质记录

### `SCHEMA_FAIL`
定义：字段命名、类型、序列化、分区规则或 artifact catalog 不满足合同。
典型：字段缺失或拼写不一致 / 同名字段类型不一致 / artifact 路径与 contract 不一致

### `REPRO_FAIL`
定义：同一输入、同一代码、同一配置下，信号输出不一致或无法稳定复算。
典型：多次运行结果不同 / 并发/排序导致非确定性 / 浮点聚合不稳定

### `SCOPE_FAIL`
定义：当前信号层已经引入新的研究问题，超出原谱系边界。
典型：在 `02` 层加入新的 regime gate / 把结构诊断字段升格为交易主信号 / 从双边线静默改成单边线

## Triage Sequence（五步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `failure_freeze.md`（含 lineage_id / run_id / failed_checks / suspected_failure_class）
- `signal_manifest.json`
- `field_snapshot.parquet`
- `field_dictionary.md`
- `artifact_catalog.md`
- `repro_manifest.json`
- `review_notes.md`

### Step 1. Correctness Triage（优先）

检查：
- lag / shift / rolling 的时间因果是否正确
- 当前字段是否只使用 `t` 时点可见信息
- 表达式、分母、窗口边界是否符合合同
- 字段名、字段语义、field dictionary 是否一致

失败映射：
- 时间因果错误 → `TEMPORAL_LEAK_FAIL`
- 表达式实现错误 → `FORMULA_FAIL`
- 语义漂移 → `SEMANTIC_DRIFT_FAIL` 或 `SCOPE_FAIL`

### Step 2. Quality & Schema Audit

检查：`low_sample` / `missing_rate_window` / `pair_missing` / 有效窗口计数 / field dictionary 完整性 / artifact catalog 与路径一致性

失败映射：
- 质量门禁不足 → `QUALITY_GATE_FAIL`
- schema/路径/类型错误 → `SCHEMA_FAIL`

### Step 3. Reproducibility Audit

检查：同配置重跑结果是否一致 / 执行环境、排序规则、并发路径是否稳定

失败映射：→ `REPRO_FAIL`，禁止继续进入 `03_train_freeze`

### Step 4. Research Boundary Audit

检查是否偷偷改题：
- 是否把诊断字段升格为交易主信号
- 是否引入新过滤器并改变主问题
- 是否改变 side contract
- 是否让字段名称继续承载新语义

失败映射：→ `SCOPE_FAIL` 或 `SEMANTIC_DRIFT_FAIL`，停止原线推进

### Step 5. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：存在 TEMPORAL_LEAK_FAIL / FORMULA_FAIL 严重到改变研究结论 / SEMANTIC_DRIFT_FAIL / SCOPE_FAIL / REPRO_FAIL
动作：当前 stage 终止，不得进入 `03_train_freeze`

#### `FAIL-SOFT`（需 Referee 判断）
条件：QUALITY_GATE_FAIL 或 SCHEMA_FAIL，但核心字段语义与时间因果已正确
动作：Referee 判定是否允许 `PASS FOR RETRY`

#### `PASS_WITH_RESTRICTIONS`
仅当：核心字段语义与时间因果正确；质量门禁缺口已显式记录；Reviewer 接受限制条件

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `FORMULA_FAIL` | `02_signal_ready` | `RETRY` |
| `TEMPORAL_LEAK_FAIL` | 泄漏产生的最早阶段（通常 01/02） | `RETRY` |
| `SEMANTIC_DRIFT_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |
| `QUALITY_GATE_FAIL` | `02_signal_ready` | `RETRY` |
| `SCHEMA_FAIL` | `02_signal_ready` | `RETRY` |
| `REPRO_FAIL` | `02_signal_ready` | `RETRY` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- 表达式实现
- lag / rolling / denominator / threshold 的边界实现
- 质量字段与状态字段
- schema、field dictionary、artifact catalog
- 排序、并发、数值稳定性与 reproducibility 机制
- 将已漂移字段拆分为主字段与审计字段

**禁止修改：**
- 因为回测或 test 不好看而反向修改信号定义
- 在 `02` 层使用 `03/04/05` 才能出现的冻结对象
- 通过增加例外规则让字段"看起来更合理"
- 在原线静默改变研究问题
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
  - change_mandate
  - consume_test_evidence_objects
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - universe
  - time_split
  - downstream_freeze_inputs
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- 超过 2 次仍未收敛，必须升级为 `NO-GO` 或 `CHILD LINEAGE`
- 不允许长期停留在 `02` 通过不断小修隐性换题

## Required Artifacts（本 skill 产出）

- `failure_freeze.md`
- `signal_manifest.json`
- `field_snapshot.parquet`
- `field_dictionary.md`
- `artifact_catalog.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — 核心字段语义与时间因果正确，仅缺 review sidecar / field dictionary / artifact catalog 闭环
- **`RETRY`** — 问题明确，修复边界清晰，不改变研究身份
- **`NO-GO`** — 字段语义始终无法稳定定义，所有实现都严重依赖泄漏或后验拼装
- **`CHILD LINEAGE`** — 修复动作实质改变主机制 / Universe / frequency / side contract / 策略身份

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
