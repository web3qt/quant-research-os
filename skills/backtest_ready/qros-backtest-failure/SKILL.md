---
name: qros-backtest-failure
description: Use when failure_class is determined for backtest_ready stage. Runs the full backtest triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure artifacts.
---

# QROS Backtest Failure Handler

## Purpose

本 skill 处置 `05_backtest` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `05_backtest` 四步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`05_backtest` 的职责不是重新发明信号，而是：只消费上游已冻结对象；验证冻结后的规则在账户级、成本后、可执行口径下是否具备交易经济性；交叉验证双引擎与执行语义的一致性；输出可审计的收益、费用、换手、持仓、关闭原因与风险画像。

失败属于**交易可行性失败**，在此层不允许用回测结果反向改写上游冻结对象。

## Failure Classes

### `ENG_FAIL`
定义：当前失败首先来自工程、实现或 correctness 问题，而不是研究本身。
典型：双引擎结果不一致 / 同配置复跑不一致 / 费用单位、名义仓位、账户预算换算错误 / 下单/成交/持仓状态机逻辑错误 / 时间标签或进入退出时点错位
contamination_path: → holdout（工程问题传播到 holdout 回测）

### `EXEC_FAIL`
定义：统计上可能仍有边，但冻结规则在真实账户级语义下不具备经济性。
典型：`gross_pnl_sum > 0` 但 `net_pnl_sum < 0` / `gross/trade` 明显低于 `fee/trade` / 交易次数过多换手过高 / capacity 或成本稍微上调就崩 / 当前执行更像"事件持有器"而不是原研究想要的执行器
contamination_path: → holdout（经济性不足在 holdout 会进一步恶化）

### `RESEARCH_FAIL`
定义：回测失败暴露出上游证据冻结不足、sample-out discipline 失守或 evidence contract 不稳。
典型：`04_test_evidence` 只在局部切片成立 / `best_h`、白名单或 freeze discipline 被破坏 / 当前 backtest 与上游冻结对象不一致 / 核心机制在交易口径下无法由上游证据支撑
contamination_path: → holdout（上游证据不稳导致回测和 holdout 结论均不可靠）

### `THESIS_FAIL`
定义：在合理实现、合理成本与合理执行口径下，机制本身不再成立。
典型：边际太薄无法覆盖合理成本 / 多轮修复后仍无经济意义 / 策略身份被执行摩擦挤压得面目全非 / 继续投入已不具研究价值
contamination_path: → holdout（机制失效在 holdout 最终确认）

### `SCOPE_FAIL`
定义：为了拯救回测，必须改变研究主问题、Universe、执行语义或策略身份。
典型：通过新增风险过滤器把策略改成另一类问题 / 静默改变 Universe 或持有期 / 把 alpha 线改成 execution-only 线 / 在原线内重写退出语义并改变身份
contamination_path: → holdout（研究范围偏差在 holdout 最终确认时暴露）

## Triage Sequence（四步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `failure_freeze.md`（含 lineage_id / run_id / stage / 已知违规点）
- `engine_compare.csv`
- `repro_manifest.json`
- `review_notes.md`

建议固定目录：`05_backtest/failure_packages/<failure_id>/`

### Step 1. Correctness Triage（优先）

固定顺序检查：
- 同配置复跑是否一致
- 双引擎 / replay 是否一致
- 单位、预算、名义仓位、费用尺度是否一致
- 成交 / 持仓 / 平仓状态机是否一致
- 抽样核对典型交易是否对得上冻结合同

失败映射：
- 优先归类为 `ENG_FAIL`，暂停经济性讨论

### Step 2. 交易可行性归因

只有 correctness 过关，才允许继续判断：
- gross 还有边但 net 被吃掉 → `EXEC_FAIL`
- 当前失败暴露上游 evidence / freeze 不稳 → `RESEARCH_FAIL`
- 机制本身不再成立 → `THESIS_FAIL`
- 要让结果过线必须改题 → `SCOPE_FAIL`

### Step 3. Research Boundary Audit

检查是否偷偷改题：
- 是否改了 Universe
- 是否改了 signal formula
- 是否改了冻结阈值、白名单、`best_h`
- 是否让新的风险过滤器改变了策略身份

失败映射：→ `SCOPE_FAIL`，停止原线推进

### Step 4. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：`ENG_FAIL`（核心 correctness 问题） / `RESEARCH_FAIL` / `THESIS_FAIL` / `SCOPE_FAIL`
动作：当前 stage 终止，不得进入 `06_holdout`

#### `FAIL-SOFT`（需 Referee 判断）
条件：账户级结果勉强过线，但 engine compare、close reason、cost sensitivity sidecar 不完整；gross 与 net 拆解尚未闭环
动作：Referee 判定是否允许 `PASS FOR RETRY`

#### `PASS_WITH_RESTRICTIONS`
仅当：回测 verdict 已清楚；仅缺 engine compare / failure package / review sidecar 闭环；不需要改变研究身份

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `ENG_FAIL` | `05_backtest`、`02_signal_ready` 或 `01_data_ready` | `RETRY` |
| `EXEC_FAIL` | `05_backtest` | `RETRY` |
| `RESEARCH_FAIL` | `03_train_freeze` 或 `04_test_evidence` | `RETRY` |
| `THESIS_FAIL` | 不回退原线 | `NO-GO` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- 回测引擎实现与 replay 语义
- 费用 / 滑点 / 预算 / 名义仓位换算
- 执行器、下单节奏、退出语义的 stage-local 实现
- engine compare、failure package、audit sidecar
- 合法回退到 `03/04` 的 evidence / freeze 闭环

**禁止修改：**
- 用回测结果反向改写 `03_train_freeze` 冻结对象
- 静默改变信号公式、白名单、`best_h`、time split
- 用 summary 文本替代账户级经济性判断
- 借修执行器之名重写研究问题
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
  - change_signal_formula
  - change_whitelist
  - change_time_split
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - universe
  - signal_formula
  - whitelist
  - best_h
  - time_split
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- 若多轮修复后仍不具经济意义，应升级为 `NO-GO`
- `05` 不得变成无限期曲线优化层

## Required Artifacts（本 skill 产出）

- `failure_freeze.md`
- `failure_classification.md`
- `rollback_decision.yaml`
- `engine_compare.csv`
- `repro_manifest.json`
- `retry_plan.md`（若 RETRY）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — 回测 verdict 已清楚，仅缺 engine compare / failure package / reviewer 闭环
- **`RETRY`** — 问题明确，回退层级清晰，修复不改变研究身份
- **`NO-GO`** — 机制在合理实现与合理成本下不值得继续，多轮修复后仍不具交易经济性
- **`CHILD LINEAGE`** — 修复动作实质改变 Universe、执行语义、持有期、研究主问题或策略身份

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
