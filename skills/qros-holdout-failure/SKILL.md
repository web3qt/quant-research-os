---
name: qros-holdout-failure
description: >
  Use when failure_class is determined for holdout_validation stage. Runs the
  full holdout triage sequence, enforces FAIL-HARD/FAIL-SOFT/
  PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure
  artifacts. NOTE: holdout default max 1 retry, only for PURITY_FAIL or
  artifact/repro issues.
---

# QROS Holdout Failure Handler

## Purpose

本 skill 处置 `06_holdout` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `06_holdout` 四步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`06_holdout` 的职责不是再开发，而是：在严格隔离的最终保留样本上验证策略泛化能力；检查样本内、test、backtest 与 holdout 之间的一致性；识别选择偏差、后验调参、脆弱参数峰值与流程污染；为 `07_shadow` 提供最终样本外证据。

**Holdout 是最终样本外审判，不是第二次开发集。失败后默认不鼓励 retry，仅 `PURITY_FAIL` 或 artifact/repro 问题才允许最多 1 次 retry。**

## Failure Classes

### `PURITY_FAIL`
定义：holdout 的独立性、隔离性或复现性被破坏，当前结果不具审计效力。
典型：holdout 时间边界提前泄漏 / holdout 曾被用于挑参数、挑 sibling、挑执行器 / holdout 结果无法独立复现 / 上游冻结对象在进入 holdout 前被替换
contamination_path: 终端阶段，无下游。但当前 holdout 结果不可信，promotion_decision 不可基于此结果

### `GENERALIZATION_FAIL`
定义：前序阶段看起来有效，但在真正未参与研发的数据上无法泛化。
典型：`05_backtest` 尚可但 holdout 断崖式下降 / gross / net 同时弱化 / 交易分布、收益结构、持仓行为与此前显著不同 / 不是成本略恶化而是整体边际消失
contamination_path: 终端阶段。泛化失败意味着策略不可部署，需回退或停止

### `FRAGILITY_FAIL`
定义：holdout 暴露策略依赖极窄参数点、极脆弱执行点或极偶然市场片段。
典型：当前冻结参数稍微偏移即显著恶化 / 邻域参数与当前参数结果断崖差异 / 微调成本、持有期、阈值就崩 / sibling lineages 没有稳定平台只有孤峰
contamination_path: 终端阶段。脆弱性暴露意味着参数不是稳定平台而是孤峰

### `SELECTION_BIAS_FAIL`
定义：当前 holdout 结果暴露前序通过主要来自多次试错后的选择偏差。
典型：当前赢家在 holdout 上集体失效 / 当前版本只是此前大量变体的幸存者 / 记录不清试过多少变体、筛过多少切片 / holdout 排名与此前最优排序严重不一致
contamination_path: 终端阶段。选择偏差意味着前序"通过"是虚假的

### `THESIS_FAIL`
定义：跨样本、跨阶段地看，主假设已不具备继续价值。
典型：多轮修复后仍然无法泛化 / 需要大量补丁才能勉强存活 / 当前线在最终保留样本上已不具研究价值
contamination_path: 终端阶段。主假设失效 = 当前 lineage 正式终止

### `SCOPE_FAIL`
定义：若要让 holdout 成立，必须改变研究主问题、Universe、执行语义或策略身份。
典型：把主策略降级成辅助信号 / 改变 Universe、持有期、side contract 才能过线 / 用 holdout 结果推动新线身份而不留痕
contamination_path: 终端阶段。但 scope 变更意味着原 lineage 结论不可延用

## Triage Sequence（四步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `holdout_failure_freeze.md`（含 lineage_id / run_id / stage / 已知违规点）
- `holdout_vs_backtest_compare.parquet`
- `purity_audit.md`
- `repro_manifest.json`
- `review_notes.md`

### Step 1. 流程纯度审计（优先）

固定顺序检查：
- holdout 是否被提前接触过
- holdout 是否真的未参与 freeze / selection / execution tuning
- 时间边界是否被污染
- 当前 run 是否可复现
- 上游冻结对象是否被私下替换

失败映射：
- 优先归类为 `PURITY_FAIL`，当前 holdout 结果不具审计效力

### Step 2. 泛化归因

只有流程纯度过关，才允许继续判断：
- 前序可做但 holdout 断崖 → `GENERALIZATION_FAIL`
- 当前参数是孤峰不具平台 → `FRAGILITY_FAIL`
- 当前通过主要来自前序筛选幸存者 → `SELECTION_BIAS_FAIL`
- 跨样本看机制已不成立 → `THESIS_FAIL`

### Step 3. Research Boundary Audit

检查 holdout 是否被拿来偷偷换题：
- 是否因为 holdout 失败就改 Universe 或持有期
- 是否把主策略降级成辅助信号
- 是否用 holdout 结果推动新风控、新执行语义成为主问题

失败映射：→ `SCOPE_FAIL`，停止原线推进

### Step 4. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：`GENERALIZATION_FAIL` / `FRAGILITY_FAIL` / `SELECTION_BIAS_FAIL` / `THESIS_FAIL` / `SCOPE_FAIL`
动作：当前 stage 终止，不得进入 `07_shadow`

#### `FAIL-SOFT`（需 Referee 判断）
条件：`PURITY_FAIL`；holdout 主结论清楚但 purity audit / compare sidecar / review 闭环不完整
动作：Referee 判定是否允许 `PASS FOR RETRY`

#### `PASS_WITH_RESTRICTIONS`
仅当：holdout 主结论已清楚；仅缺 purity audit / compare sidecar / reviewer 闭环；不需要改变研究身份

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `PURITY_FAIL` | `05_backtest` 或更早 | `PASS FOR RETRY` 或 `RETRY` |
| `GENERALIZATION_FAIL` | `04_test_evidence` 或 `05_backtest` | `RETRY` 或 `NO-GO` |
| `FRAGILITY_FAIL` | `03_train_freeze` 或 `04_test_evidence` | `RETRY` 或 `NO-GO` |
| `SELECTION_BIAS_FAIL` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- purity audit、边界隔离、repro 链
- holdout compare 与 review sidecar
- 合法回退到 `04/05` 重审证据与交易可行性
- 合法回退到 `03` 重审参数高原与 freeze discipline

**禁止修改：**
- 在当前 holdout 上继续调参
- 用 holdout 结果反向定义 whitelist、`best_h` 或主阈值
- 重估原线冻结对象并宣称"只是微调"
- 跳过失败冻结，直接覆盖旧结果
- 把 holdout 变成第二次开发集

## Retry Discipline

⚠️ **Holdout 默认不鼓励 retry。** 只有以下场景才允许，且最多 1 次：

- `PURITY_FAIL`（holdout 独立性被破坏）
- 明确的 artifact / reproduction 问题
- 当前 holdout run 因流程问题不具审计效力

每次 retry 必须写清：

```yaml
failure_class: <class>
root_cause_hypothesis: <具体假设>
rollback_stage: <stage>
allowed_modifications:
  - <modification>
forbidden_modifications:
  - tune_parameters_on_holdout
  - rewrite_whitelist_from_holdout
  - change_strategy_identity
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - time_split_except_holdout_boundary_fix
```

- 同一问题默认最多允许 **1 次** retry（比其他 stage 严格）
- retry 后仍失败，不得继续在 holdout 上做受控优化
- 若 holdout 真正暴露了泛化问题，应升级为 `NO-GO` 或合法回退

## Required Artifacts（本 skill 产出）

- `holdout_failure_freeze.md`
- `holdout_vs_backtest_compare.parquet`
- `purity_audit.md`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY，仅限 PURITY_FAIL 或 repro 问题）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — holdout 主结论已清楚，仅缺 purity audit / compare sidecar / reviewer 闭环
- **`RETRY`** — 问题明确（仅限 PURITY_FAIL 或 repro），修复不改变研究身份；通常只 1 次
- **`NO-GO`** — 泛化失败、脆弱性暴露或主假设失效，当前线在最终保留样本上不值得继续
- **`CHILD LINEAGE`** — 修复动作实质改变研究主问题、Universe、执行语义或策略身份

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
