---
name: qros-test-evidence-failure
description: Use when failure_class is determined for test_evidence stage. Runs the full test_evidence triage sequence, enforces FAIL-HARD/FAIL-SOFT/PASS_WITH_RESTRICTIONS classification, and produces stage-specific failure artifacts.
---

# QROS Test Evidence Failure Handler

## Purpose

本 skill 处置 `04_test_evidence` 阶段的所有失败。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 运行 `04_test_evidence` 五步 triage
2. 映射到 stage-specific failure class
3. 判定 FAIL-HARD / FAIL-SOFT / PASS_WITH_RESTRICTIONS
4. 给出 rollback routing 与 formal decision
5. 输出标准产物
6. 将 `failure_class` + 初步 disposition 传递给 `qros-lineage-change-control`

## 阶段职责边界

`04_test_evidence` 的职责不是继续找理由，而是：在已冻结的 train/test 切分、阈值、白名单、参数边界上验证结构证据；冻结正式 test 期统计结论；冻结后续 `05_backtest` 允许消费的证据对象；阻止团队用 test 结果反向改写 `03_train_freeze`。

失败属于**证据治理失败**，错误证据会直接污染后续回测与晋级决策。

## Failure Classes

### `EVIDENCE_ABSENT`
定义：正式 test 期中，核心结构证据不存在、方向错误或不足以支撑晋级。
典型：`Q5` 没有负向回归 / `gamma >= 0` / `DC_N` 未显著高于基线 / `DownLinkGap` 不显著大于 0

### `EVIDENCE_FRAGILE`
定义：证据存在，但极其脆弱，对窗口、切片、参数或 symbol 子集高度敏感。
典型：train/test 都略有边但轻微改动就断崖 / 统计只在少数参数点成立不形成平台 / 某几个 symbol 撑起总结果

### `REGIME_SPECIFIC_FAIL`
定义：证据只在极窄 market regime 成立，超出该 regime 即失效。
典型：只在低波期有用 / 只在牛市/熊市/risk-off 有效 / 只有极端环境下才出现结构

### `SELECTION_BIAS_FAIL`
定义：由于多次试验、重复筛选、挑切片、挑 symbol、挑 side，导致当前 test evidence 不再可信。
典型：记录不清试过多少变体 / `best_h`、白名单、side、阈值看过 test 结果后才定 / 反复切 test 窗、换 regime 分层直到结果成立

### `ARTIFACT_REPRO_FAIL`
定义：test evidence 产物无法稳定复现，或无法从底层时序追溯。
典型：同配置重跑 summary 不一致 / 汇总表与单币时序对不上 / `best_h` 来源路径不清楚 / symbol summary 与 report_by_h 不可核对

### `SCOPE_DRIFT_FAIL`
定义：当前 test evidence 讨论的问题已经偏离原研究问题。
典型：原题是双边结构审计，test 时只汇报对自己有利的一边 / 原题是 structure evidence，却在这层混入执行收益优化 / 原题是双边研究，却在 evidence 阶段静默改成单边

## Triage Sequence（五步标准操作）

### Step 0. 冻结失败现场

必须产出：

- `failure_freeze.md`（含 lineage_id / run_id / stage / 已知违规点）
- `test_evidence_manifest.json`
- `evidence_summary.parquet`
- `report_by_h.parquet`
- `repro_manifest.json`
- `review_notes.md`

### Step 1. Freeze Discipline Audit（优先）

检查：
- 当前 evidence 是否只消费了 `03_train_freeze` 允许的对象
- test 期统计是否没有反向重估阈值、白名单、`best_h`
- train/test 边界是否无穿越
- 当前切片与对比口径是否可追溯

失败映射：
- freeze discipline 失守 → `SELECTION_BIAS_FAIL`
- 讨论问题已偏离原题 → `SCOPE_DRIFT_FAIL`

### Step 2. Evidence Attribution

必须按顺序判断：
- 证据根本不存在 → `EVIDENCE_ABSENT`
- 证据存在但脆弱 → `EVIDENCE_FRAGILE`
- 证据只在极窄 regime 成立 → `REGIME_SPECIFIC_FAIL`
- 证据结论根本不可复建 → `ARTIFACT_REPRO_FAIL`

### Step 3. Artifact Reproducibility Audit

必须显式检查：
- summary 是否能追溯到原始时序
- `report_by_h`、symbol summary、segment summary 是否一致
- 同配置重跑是否稳定
- evidence summary 是否有完整 manifest 与 artifact catalog

失败映射：→ `ARTIFACT_REPRO_FAIL`，禁止进入 `05_backtest`

### Step 4. Research Boundary Audit

检查是否偷偷换题：
- 是否只汇报有利 side
- 是否把证据层变成执行收益优化层
- 是否因为某个 regime 好看就临时把 regime filter 升格成主问题

失败映射：→ `SCOPE_DRIFT_FAIL`，停止原线推进

### Step 5. 判定失败等级

#### `FAIL-HARD`（自动 FAIL）
条件：`EVIDENCE_ABSENT` / `EVIDENCE_FRAGILE`（多轮后仍不稳） / `REGIME_SPECIFIC_FAIL` / `SELECTION_BIAS_FAIL` / `ARTIFACT_REPRO_FAIL` / `SCOPE_DRIFT_FAIL`
动作：当前 stage 终止，不得进入 `05_backtest`

#### `FAIL-SOFT`（需 Referee 判断）
条件：核心证据结论成立，但 summary、segmentation sidecar 或 artifact catalog 不完整；reviewer 认可主结论但 referee 无法判断 freeze discipline 漏洞
动作：Referee 判定是否允许 `PASS FOR RETRY`

#### `PASS_WITH_RESTRICTIONS`
仅当：核心证据已成立；仅缺 artifact sidecar 或 catalog 闭环；不需要改变研究身份

## Rollback Routing Table

| failure_class | 默认回退阶段 | 默认 formal decision |
|---|---|---|
| `EVIDENCE_ABSENT` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `NO-GO` |
| `EVIDENCE_FRAGILE` | `03_train_freeze` | `RETRY` 或 `NO-GO` |
| `REGIME_SPECIFIC_FAIL` | `03_train_freeze` 或 `00_mandate` | `CHILD LINEAGE` 或 `NO-GO` |
| `SELECTION_BIAS_FAIL` | `03_train_freeze` 或 `00_mandate` | `RETRY` 或 `CHILD LINEAGE` |
| `ARTIFACT_REPRO_FAIL` | `04_test_evidence` | `PASS FOR RETRY` 或 `RETRY` |
| `SCOPE_DRIFT_FAIL` | `00_mandate` 或 child lineage | `CHILD LINEAGE` |

## Allowed / Forbidden Modifications

**允许修改：**
- evidence summary / segment summary / symbol summary 的复现链
- 当前 stage 的 artifact catalog 与 review sidecar
- 受控回退到 `03_train_freeze` 重新冻结候选空间、阈值或白名单
- 受控回退到 `02_signal_ready` 修复上游字段合同

**禁止修改：**
- 因为 test 不好看而追加新切片直到结果成立
- 用 test 结果反向重估 `03_train_freeze` 冻结对象
- 把 regime 解释临时升级成主问题
- 用执行收益或 backtest 曲线替代 test evidence
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
  - slice_test_until_it_looks_good
  - rewrite_freeze_objects_from_test_results
  - change_research_question
expected_improvement:
  - <criterion>
unchanged_contracts:
  - mandate
  - time_split
  - signal_family
  - data_contract
```

- 同一 failure class 连续 retry 不得超过 **2 次**
- 若正式 test 证据多轮后仍不成立，应升级为 `NO-GO`
- `04` 不得变成无限切片优化层

## Required Artifacts（本 skill 产出）

- `failure_freeze.md`
- `test_evidence_manifest.json`
- `evidence_summary.parquet`
- `report_by_h.parquet`
- `repro_manifest.json`
- `failure_classification.md`
- `rollback_decision.yaml`
- `retry_plan.md`（若 RETRY）

## Formal Decision Mapping

- **`PASS FOR RETRY`** — 核心证据结论已成立，仅缺 artifact sidecar / catalog / reviewer 闭环
- **`RETRY`** — 存在明确回退目标，修复不改变研究身份，证据仍值得在合法边界内重审
- **`NO-GO`** — 正式 test 证据缺失或脆弱，多轮受控修复后仍不足以支撑晋级
- **`CHILD LINEAGE`** — 修复动作实质改变 regime 条件、研究主问题、Universe、frequency 或策略身份

## After This Skill

将以下内容传给 `qros-lineage-change-control`：

- `failure_class`
- `disposition`（初步）
- 四问预判（研究主问题是否变化 / 冻结对象是否变化 / 交易语义是否变化 / 证据链是否可延续）
