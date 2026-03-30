---
name: qros-train-freeze-failure
description: Use when failure_class is determined for train_freeze stage. Runs the full train_freeze triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure artifacts.
---

# QROS Train Freeze Failure Handler

## Purpose

本 skill 处置 `03_train_freeze` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `03_train_freeze` 五步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`03_train_freeze` 的职责不是继续研究，而是：把后续 `04_test_evidence` / `05_backtest` 会消费的对象正式冻结，确保冻结对象来自允许的信息边界（而不是 test/backtest 结果），防止 `03` 变成隐性调参层或后验写回层。

失败属于**治理失败**，freeze 合同一旦不清楚，后续所有证据都可能被污染。

## Failure Classes

### `FREEZE_MISSING`
定义：应该冻结的对象没有被冻结，或只有口头说明没有正式产物。
典型：没有 `time_split.json` / 没有 `parameter_grid.yaml` / 没有 `selected_symbols_train.csv` / 没有明确 `freeze_manifest`
contamination_path: → test_evidence, backtest, holdout（缺失冻结对象导致下游无合法输入可消费）

### `FREEZE_AMBIGUOUS`
定义：冻结对象看似存在，但语义不明确，无法判断后续是否消费同一对象。
典型：「高波过滤已冻结」但未说明是 train 统计还是全样本统计 / 文档声明某种 `entry_mode`，代码却仍接受其他模式
contamination_path: → test_evidence（语义不清导致阈值/白名单消费歧义）, backtest, holdout

### `LEAKED_FREEZE_FAIL`
定义：冻结对象直接或间接使用了 test / backtest / holdout 信息。
典型：用全样本 `ResidualZ` 估分位阈值 / 用 test 期结果重排 `selected_symbols` / 用 backtest 表现选 `best_h` 再回写 `03` / 先看 OOS 再决定 train 门槛
contamination_path: → test_evidence, backtest, holdout（污染的冻结阈值/白名单/参数使所有下游验证失效）

### `MULTIPLE_TESTING_FAIL`
定义：freeze 前进行了大量搜索，但没有记录候选空间、试验次数与选择纪律。
典型：扫了很多窗口、阈值、过滤器，只留下一个最优组合 / 没有 trial log / 无法区分哪些参数是预先声明，哪些是探索后提案
contamination_path: → test_evidence（选择偏差导致白名单/best_h 不可信）, backtest, holdout

### `POST_FREEZE_DRIFT`
定义：freeze 之后对冻结对象进行了静默改写，但未新开 child lineage，也未重新审批。
典型：`selected_symbols_train.csv` 被覆盖 / `q20/q40/q60/q80` 被重算但路径不变 / `best_h` 从 `04` 回写进 `03`
contamination_path: → test_evidence, backtest, holdout（被篡改的冻结对象使下游消费的对象与审批时不一致）

### `REPRO_FAIL`
定义：在相同输入、相同版本下，freeze 结果无法稳定复现。
典型：两次运行白名单不一致 / 参数集顺序依赖随机种子但未记录
contamination_path: → test_evidence, backtest, holdout（不可复现的冻结使下游产物不可审计）

### `SCOPE_FAIL`
定义：借 `03_train_freeze` 之名，实质上改变了研究问题。
典型：原题是双边 `OB/OS`，freeze 时变成 `OB only` / 原题是结构审计，freeze 时变成收益最优化
contamination_path: → test_evidence, backtest, holdout（研究范围偏差导致全 pipeline 证据偏离原问题）

## Triage Sequence（五步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `failure_freeze.md`（含 lineage_id / run_id / stage / freeze 已知违规点）
- `freeze_manifest_snapshot.json`
- `trial_log_snapshot.csv`
- `time_split_snapshot.json`
- `repro_manifest.json`
- `review_notes.md`

### Step 1. Freeze Correctness Triage（优先）

检查：
- 后续阶段消费的对象是否都已显式冻结
- freeze 语义是否与文档一致
- freeze 对象是否只使用 train 期可用信息
- 候选空间与最终版本是否能追溯

失败映射：
- 对象缺失 → `FREEZE_MISSING`
- 语义不清 → `FREEZE_AMBIGUOUS`
- 使用未来信息 → `LEAKED_FREEZE_FAIL`

### Step 2. Search Discipline Audit

检查：
- 是否记录了候选参数空间
- 是否记录了试验次数与筛选逻辑
- 是否只保留"最好看"的冻结版本
- 是否存在 `04/05` 结果回写 `03` 的迹象

失败映射：
- 搜索纪律失守 → `MULTIPLE_TESTING_FAIL`
- freeze 后静默改写 → `POST_FREEZE_DRIFT`

### Step 3. Reproducibility Audit

检查：同一版本下 freeze 结果能否重建 / 数据版本、排序、种子是否已固定

失败映射：→ `REPRO_FAIL`，禁止进入 `04_test_evidence`

### Step 4. Research Boundary Audit

检查是否偷偷改题：
- 是否从结构线变成交易线
- 是否从双边线变成单边线
- 是否新增了未在 mandate 声明的主 gate
- 是否改变了 Universe、frequency 或策略角色

失败映射：→ `SCOPE_FAIL`，停止原线推进

### Step 5. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：`LEAKED_FREEZE_FAIL` / `MULTIPLE_TESTING_FAIL` 且无 trial log / `POST_FREEZE_DRIFT` / `SCOPE_FAIL` / `REPRO_FAIL`
动作：当前 stage 终止，不得进入 `04_test_evidence`

#### `FAIL-SOFT`（需 Referee 判断）
条件：`FREEZE_MISSING` 或 `FREEZE_AMBIGUOUS`，freeze 语义基本清楚但 artifact sidecar 未闭环
动作：Referee 判定是否允许 `PASS FOR RETRY`

#### `PASS_WITH_RESTRICTIONS`
仅当：freeze 对象已存在；仅缺 trial log、manifest 或审计 sidecar 闭环；不需要改变研究身份

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `FREEZE_MISSING` | `03_train_freeze` | `RETRY` |
| `FREEZE_AMBIGUOUS` | `03_train_freeze` | `PASS FOR RETRY` 或 `RETRY` |
| `LEAKED_FREEZE_FAIL` | `02_signal_ready` 或更早 | `RETRY` |
| `MULTIPLE_TESTING_FAIL` | `02_signal_ready` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `POST_FREEZE_DRIFT` | 最近一个合法 freeze checkpoint | `RETRY` |
| `REPRO_FAIL` | `01_data_ready`、`02_signal_ready` 或 `03_train_freeze` | `RETRY` |
| `SCOPE_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- freeze manifest
- trial log 与候选空间记录
- 时间切分物化
- 白名单与阈值对象的生成实现
- reproducibility 与版本固定机制
- downstream contract 所需的审计 sidecar

**禁止修改：**
- 用 test / backtest 结果反向重估冻结对象
- 覆盖原冻结文件而不留痕
- 因结果不好而静默缩小 Universe
- 在未走 change control 的情况下改变策略身份
- 跳过失败冻结，直接写新版本覆盖旧版本

## Retry Discipline

每次 retry 必须写清：

```yaml
failure_class: <class>
root_cause_hypothesis: <具体假设>
rollback_stage: <stage>
allowed_modifications:
  - <modification>
forbidden_modifications:
  - overwrite_existing_freeze_artifacts_in_place
  - use_test_results_to_select_best_h
  - change_strategy_identity
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - universe_definition
  - signal_family
  - downstream_stage_order
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- `03` 不得成为无限期调参层
- 若修复动作已经改变研究身份，必须转 `CHILD LINEAGE`

## Required Artifacts（本 skill 产出）

- `failure_freeze.md`
- `freeze_manifest_snapshot.json`
- `trial_log_snapshot.csv`
- `time_split_snapshot.json`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — 冻结对象已成立，仅缺 trial log / manifest / 审计 sidecar 闭环
- **`RETRY`** — 问题明确，回退层级清晰，修复不改变研究身份
- **`NO-GO`** — 冻结合同始终无法稳定成立，多轮修复后仍无法形成可审计 freeze
- **`CHILD LINEAGE`** — 修复动作实质改变 Universe / frequency / signal_side / 策略身份 / 研究主问题

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判
