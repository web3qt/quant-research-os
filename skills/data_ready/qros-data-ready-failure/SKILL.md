---
name: qros-data-ready-failure
description: Use when failure_class is determined for data_ready stage. Runs the full data_ready triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure artifacts.
---

# QROS Data Ready Failure Handler

## Purpose

本 skill 处置 `01_data_ready` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `01_data_ready` 五步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`01_data_ready` 的职责是：把 `00_mandate` 声明的数据需求物化成可复验输入，确保下游 `02_signal_ready` 使用的数据满足时间、单位、质量、覆盖率、可追溯性合同。

失败时，不能当成普通工程 bug，而是**研究治理失败**，因为错误数据会直接污染后续统计证据与回测结论。

## Failure Classes

### `DATA_MISSING`
定义：数据源或字段缺失，导致无法满足最小研究合同。
典型：某些 symbol 无历史文件 / pair_stats 缺失 / 关键质量标记未生成
contamination_path: → signal_ready, train_freeze, test_evidence, backtest, holdout（基础层数据缺失阻断全 pipeline）

### `DATA_MISALIGNMENT`
定义：时间对齐、采样频率、session 边界、收益归属窗口不正确。
典型：`r_t` 实际对应 `t+1` / ALT 与 BTC 使用不同 bar close 定义 / train/test 边界穿越错误
contamination_path: → signal_ready（时间错位导致信号构造错误）, train_freeze, test_evidence, backtest, holdout

### `LEAKAGE_FAIL`
定义：未来函数、标签泄漏、样本外信息混入研究窗口。
典型：使用未来价格补缺 / 用全样本统计量做 train 标准化 / 使用未来退市信息过滤样本
contamination_path: → signal_ready, train_freeze, test_evidence, backtest, holdout（泄漏统计量通过标准化/阈值链式传播至所有下游阶段）

### `QUALITY_FAIL`
定义：缺失、stale、outlier、停牌、异常成交等质量问题超出门槛。
典型：窗口有效样本严重不足 / stale bar 连续出现但未处理
contamination_path: → signal_ready（质量门禁缺失导致信号不可靠）, train_freeze, test_evidence

### `SCHEMA_FAIL`
定义：字段名、类型、单位、语义不符合合同。
典型：return 与 log_return 混用 / 百分比与小数混用 / 文档写的是 kappa，实际产物是 beta
contamination_path: → signal_ready（schema 不匹配导致字段消费错误）, train_freeze, test_evidence

### `REPRO_FAIL`
定义：同一版本配置下无法稳定复现同一底表或统计摘要。
典型：重跑文件 hash 变化 / 随机处理未固化 seed / 输入源版本漂移
contamination_path: → signal_ready, train_freeze, test_evidence, backtest, holdout（不可复现的基础层使所有下游产物不可审计）

### `SCOPE_FAIL`
定义：数据准备已经偏离 `00_mandate` 声明的研究范围。
典型：Mandate 只允许 1m，Data Ready 却混入 5m / Universe 被临时扩池或缩池
contamination_path: → signal_ready, train_freeze, test_evidence, backtest, holdout（研究范围偏差导致全 pipeline 证据偏离原问题）

## Triage Sequence（五步标准操作）

### Step 0. 冻结失败现场

第一动作不是改代码，而是产出 failure freeze package：

- `failure_freeze.md`（含 lineage_id / run_id / failed_checks / suspected_failure_class）
- `data_ready_manifest.json`
- `schema_snapshot.json`
- `coverage_report.parquet`
- `quality_report.parquet`
- `lineage_input_inventory.csv`
- `review_notes.md`

### Step 1. Correctness Triage（优先）

检查：
- bar close 对齐是否一致
- 收益 `r_t` 的归属窗口是否符合合同
- 标签窗口是否严格位于特征之后
- train / test / holdout 切分是否无穿越
- 收益简单收益还是对数收益、百分比与小数是否统一
- 输入文件是否有 version / hash / source path，重跑是否一致

失败映射：
- 时间因果错误 → `DATA_MISALIGNMENT` 或 `LEAKAGE_FAIL`
- 单位/schema 错误 → `SCHEMA_FAIL`
- 无法复现 → `REPRO_FAIL`

### Step 2. Quality & Coverage Audit

统计：`missing_rate` / `stale_rate` / `outlier_rate` / `zero_return_rate` / `valid_count_window`

若研究依赖 pair，额外检查：ALT 与 BTC 时间戳严格对齐 / pair missing 标准化物化

失败映射：→ `QUALITY_FAIL` 或 `DATA_MISALIGNMENT`

### Step 3. Leakage & Sample Bias Audit

必须显式检查：
- 是否使用全样本统计量做局部标准化
- 是否使用未来已知信息过滤样本
- 是否存在幸存者偏差
- 是否把 test/holdout 期信息提前用于 Data Ready

一旦确认泄漏：
- 直接 `FAIL-HARD`，失败分类固定为 `LEAKAGE_FAIL`
- 禁止进入 `02_signal_ready`

### Step 4. Research Boundary Audit

检查 Data Ready 是否偷偷改题：
- 是否改变了 Universe / 主腿 / 时间频率 / 研究字段定义
- 是否在本阶段引入了下游 gate

失败映射：→ `SCOPE_FAIL`

### Step 5. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：存在时间错位 / 存在未来函数 / 关键字段缺失 / schema/unit 错到足以改变结论 / 数据无法复现
动作：当前 stage 终止，不得进入 `02_signal_ready`，必须修复并重跑完整 `01_data_ready`

#### `FAIL-SOFT`（需 Referee 判断）
条件：问题集中于部分 symbol 或部分时间段，可通过收缩 Universe 或限制时间范围处理
动作：Referee 判定是否允许 `PASS_WITH_RESTRICTIONS`，必须显式记录 restrictions 写入 contract

#### `PASS_WITH_RESTRICTIONS`
仅当：无泄漏、无时间错位、无关键 schema 错误；问题被清晰 flag 并可隔离；缩小后仍符合 `00_mandate` 主问题；Reviewer 接受限制条件

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `DATA_MISSING` | `01_data_ready` | `RETRY` |
| `DATA_MISALIGNMENT` | `01_data_ready` | `RETRY` |
| `LEAKAGE_FAIL` | `00_mandate` 或 `01_data_ready` | `RETRY` |
| `QUALITY_FAIL` | `01_data_ready` | `RETRY` |
| `SCHEMA_FAIL` | `01_data_ready` | `RETRY` |
| `REPRO_FAIL` | `01_data_ready` | `RETRY` |
| `SCOPE_FAIL` | `00_mandate` 或 change_control | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- 数据抓取与清洗逻辑、对齐逻辑
- 缺失、stale、outlier 标记生成逻辑
- schema 与字段字典
- manifest / version / reproducibility 机制
- 覆盖率过滤规则（前提是不改变 `00_mandate` 主问题）

**禁止修改：**
- 直接改信号公式来掩盖数据问题
- 直接改 `03_train_freeze` 阈值来适配脏数据
- 用后验 test/backtest 结果反向决定 Data Ready 过滤
- 临时缩短时间区间只保留"好看"的年份
- 在未走 change control 的情况下更换主研究对象

## Retry Discipline

每次 retry 必须写清：

```yaml
failure_class: <class>
root_cause_hypothesis: <具体假设>
rollback_stage: <stage>
allowed_modifications:
  - <modification_1>
expected_improvement:
  - <improvement_criterion>
unchanged_contracts:
  - universe
  - frequency
  - time_split
  - main_leg
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- 超过 2 次仍未收敛，必须升级为 Reviewer / Referee
- 若修复动作已经改变研究身份，则必须转 `CHILD LINEAGE`

## Required Artifacts（本 skill 产出）

- `failure_freeze.md`
- `data_ready_manifest.json`
- `coverage_report.parquet`
- `quality_report.parquet`
- `schema_snapshot.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY）

可选附加：
- `timestamp_alignment_audit.parquet`
- `label_leakage_audit.md`
- `symbol_restriction_list.csv`

## Formal Decision Mapping

本 skill 完成后，输出以下四种 formal decision 之一：

- **`RETRY`** — 问题明确，修复边界清晰，不改变研究身份
- **`NO-GO`** — 关键数据长期不可得，最小样本不成立
- **`CHILD LINEAGE`** — 修复动作实质改变 Universe / frequency / main_leg / field contract
- **`PASS FOR RETRY`** — 仅缺 schema/manifest/artifact 完整性，核心数据无误

注：`RESEARCH_AGAIN` 只作为 prose 解释，正式输出必须是以上四种之一。

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
