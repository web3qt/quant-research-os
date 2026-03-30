# QROS data_ready Failure Classification — Baseline Evaluation

You are a QROS data_ready stage review expert. For each sample below, classify the failure into one of 7 classes based on the SKILL rules.

## SKILL RULES

### qros-data-ready-review (Full):
```
---
name: qros-data-ready-review
description: Use when data_ready artifacts have been authored and must pass formal gate review before advancing to signal_ready stage.
---

# Data Ready Review

## Purpose

产出共享、可审计、strategy-agnostic 的 Layer 0 数据基础层

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- mandate frozen outputs
- 原始市场数据或共享上游数据源
- 正式 universe 与时间边界

## Required Outputs

Required outputs:
- aligned_bars/
- rolling_stats/
- qc_report.parquet
- dataset_manifest.json
- validation_report.md
- data_contract.md
- dedupe_rule.md
- universe_summary.md
- universe_exclusions.csv
- universe_exclusions.md
- data_ready_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Data Ready

Formal gate summary:
Must pass all of:
- 基准腿覆盖审计已完成
- dense 时间轴已生成，正式对象时间轴长度一致
- 缺失、坏价、stale 和 outlier 语义已显式保留
- qc_report 与 dataset_manifest 已生成
- 排除项和准入结果已显式记录
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 没有统一时间栅格
- 混用 open_time 和 close_time 作为主键
- 静默吞掉缺失或静默 forward-fill
- 基准腿覆盖或 universe 审计无法解释

## Checklist

Stage checklist:
- [blocking] dense 时间轴已生成，目标对象时间栅格一致
- [blocking] 缺失、stale、outlier、坏价等语义被显式标记，而非静默修复
- [blocking] 基准腿（如 BTC）覆盖审计通过
- [blocking] dataset_manifest.json 已冻结当前数据版本、Universe 版本和产物路径
- [blocking] 去重规则与时间主键口径明确，未混用 open_time / close_time
- [blocking] Universe 排除项已显式记录，并给出原因
- [reservation] rolling_stats 或等价可复用 rolling 缓存已生成

## Audit-Only Items

Audit-only items:
- 个别对象质量偏弱但未触发正式排除
- rolling cache 选择是否足够经济

## Closure Artifacts

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Reviewer Findings File

Before writing closure artifacts, create `review_findings.yaml` in the current `stage_dir`.

Minimum expected fields:

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

Use reviewer findings for semantic judgment. Let the review engine handle the hard evidence checks and final artifact writing.

## Allowed Verdicts

- `PASS`: 当前阶段目标已满足，无保留事项
- `CONDITIONAL PASS`: 当前阶段主要目标满足，但存在必须明示的保留事项
- `PASS FOR RETRY`: 允许按既定 rollback 范围受控重试，未完成前不得继续晋级
- `RETRY`: 当前阶段失败，但失败原因仍属于受控可修复问题
- `NO-GO`: 组织上不支持继续推进当前方案
- `GO`: 组织上批准进入下一治理或运行阶段
- `CHILD LINEAGE`: 需要以新谱系承接，不允许在原线静默改题

## Rollback Rules

- Default rollback stage: data_ready
- Allowed modification: 数据抽取
- Allowed modification: 时间对齐
- Allowed modification: QC 规则
- Allowed modification: admissibility 审计
- Must open child lineage when: 想修改 mandate 冻结的时间边界
- Must open child lineage when: 想修改 mandate 冻结的 universe 口径

## Downstream Permissions

- May advance to: signal_ready
- Frozen output consumable by next stage: aligned_bars/
- Frozen output consumable by next stage: rolling_stats/
- Frozen output consumable by next stage: qc_report.parquet
- Frozen output consumable by next stage: dataset_manifest.json
- Frozen output consumable by next stage: universe_fixed.csv
- Next stage must not consume/re-estimate: 正式时间边界
- Next stage must not consume/re-estimate: universe admission rules

## Verdict Flow

1. Confirm current stage
2. Load the stage contract
3. Load the stage checklist
4. Check required inputs and outputs
5. Evaluate the formal gate first
6. Record audit-only findings after that
7. Save `review_findings.yaml`
8. Run `~/.qros/bin/qros-review`
9. Review the generated closure artifacts

```

### qros-data-ready-failure (Full):
```
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

### `DATA_MISALIGNMENT`
定义：时间对齐、采样频率、session 边界、收益归属窗口不正确。
典型：`r_t` 实际对应 `t+1` / ALT 与 BTC 使用不同 bar close 定义 / train/test 边界穿越错误

### `LEAKAGE_FAIL`
定义：未来函数、标签泄漏、样本外信息混入研究窗口。
典型：使用未来价格补缺 / 用全样本统计量做 train 标准化 / 使用未来退市信息过滤样本

### `QUALITY_FAIL`
定义：缺失、stale、outlier、停牌、异常成交等质量问题超出门槛。
典型：窗口有效样本严重不足 / stale bar 连续出现但未处理

### `SCHEMA_FAIL`
定义：字段名、类型、单位、语义不符合合同。
典型：return 与 log_return 混用 / 百分比与小数混用 / 文档写的是 kappa，实际产物是 beta

### `REPRO_FAIL`
定义：同一版本配置下无法稳定复现同一底表或统计摘要。
典型：重跑文件 hash 变化 / 随机处理未固化 seed / 输入源版本漂移

### `SCOPE_FAIL`
定义：数据准备已经偏离 `00_mandate` 声明的研究范围。
典型：Mandate 只允许 1m，Data Ready 却混入 5m / Universe 被临时扩池或缩池

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

```

## FAILURE CLASSES

1. DATA_MISSING — 数据源或字段缺失，导致无法满足最小研究合同
2. DATA_MISALIGNMENT — 时间对齐、采样频率、session 边界、收益归属窗口不正确
3. LEAKAGE_FAIL — 未来函数、标签泄漏、样本外信息混入研究窗口
4. QUALITY_FAIL — 缺失、stale、outlier、停牌、异常成交等质量问题超出门槛
5. SCHEMA_FAIL — 字段名、类型、单位、语义不符合合同
6. REPRO_FAIL — 同一版本配置下无法稳定复现同一底表或统计摘要
7. SCOPE_FAIL — 数据准备已经偏离 mandate 声明的研究范围

## SEVERITY LEVELS

- FAIL-HARD: 存在时间错位/未来函数/关键字段缺失/schema错误到足以改变结论
- FAIL-SOFT: 问题集中于部分 symbol 或部分时间段，可通过收缩 Universe 或限制时间范围处理

## INSTRUCTIONS

For each sample, output EXACTLY this format (one line per sample):
SAMPLE_ID | PREDICTED_CLASS | SEVERITY | ONE_SENTENCE_RATIONALE

Do NOT look at the sample ID to guess the class. Classify based solely on the data spec content and SKILL rules.

---

## SAMPLES

### Sample 1: sample_001_data_missing

**Research Idea**: BTC 领动高流动性 ALT — 冲击事件后 30 分钟收益预测

**Mandate Snapshot**:
frequency: 1m bars
main_leg: BTC
required_fields:
- open, high, low, close, volume
- vwap (per bar)
- pair_stats (BTC-ALT correlation matrix)
research_question: "BTC \u5927\u5E45\u6CE2\u52A8\u540E\uFF0C\u9AD8\u6D41\u52A8\u6027\
  \ ALT \u662F\u5426\u5728 30 \u5206\u949F\u7A97\u53E3\u5185\u4EA7\u751F\u53EF\u9884\
  \u6D4B\u7684\u8D85\u989D\u6536\u76CA"
time_window: 2022-01-01 to 2024-12-31
universe: BTC + TOP20 ALT by 30d volume (CoinGecko ranking)


**Data Spec Attempt**:
## Dataset Manifest
- BTC 1m bars: 2022-01-01 to 2024-12-31 ✓ (1,576,800 rows)
- ETH 1m bars: 2022-01-01 to 2024-12-31 ✓
- SOL 1m bars: 2022-01-01 to 2024-12-31 ✓
- AVAX 1m bars: 2023-06-01 to 2024-12-31 ⚠️ (partial history)
- MATIC 1m bars: MISSING — exchange API did not return data before rebrand
- pair_stats: BTC-ETH, BTC-SOL correlation computed ⚠️ (missing AVAX, MATIC)
- rolling_stats: 60m rolling mean/std for BTC, ETH, SOL
- vwap: computed for BTC, ETH, SOL only

Note: MATIC data unavailable from Binance API (symbol renamed to POL).
AVAX only has 18 months of data. Proceeding with available universe.


**Lineage Context**:
idea_intake_output_summary: 'Universe: BTC + TOP20 ALT. Require full 3-year history
  for all symbols.'
mandate_freeze_hash: md5:a1b2c3d4
mandate_universe_constraint: All symbols must have >= 2 years of continuous data coverage


---

### Sample 2: sample_002_data_missing

**Research Idea**: ETH/BTC 比率与 DeFi TVL 的领先-滞后关系

**Mandate Snapshot**:
frequency: daily
main_leg: ETH/BTC ratio
required_fields:
- eth_btc_close (daily)
- defi_tvl_total (daily)
- defi_tvl_by_protocol (top 20)
research_question: "DeFi TVL \u53D8\u5316\u662F\u5426\u9886\u5148 ETH/BTC \u6BD4\u7387\
  \u53D8\u5316 1-7 \u5929"
time_window: 2021-01-01 to 2024-06-30
universe: ETH/BTC pair + DeFi TVL aggregated


**Data Spec Attempt**:
## Dataset Manifest
- eth_btc_close: 2021-01-01 to 2024-06-30 ✓
- defi_tvl_total: 2021-01-01 to 2024-06-30 ✓
- defi_tvl_by_protocol: ERROR — DeFi Llama API returns inconsistent
  protocol names across time. Top 20 protocol list changes as protocols
  merge, rebrand, or become inactive. Attempted to align by protocol
  slug but 3 protocols have duplicate entries with different slugs.
  Omitting protocol-level breakdown for now.
- rolling_stats: 7d, 14d, 30d rolling TVL change for total only

Note: Protocol-level TVL alignment too complex. Using aggregate TVL only.
Research can proceed with total TVL.


**Lineage Context**:
idea_intake_output_summary: Research requires top 20 DeFi protocol TVL to analyze
  protocol-specific leading signals.
mandate_field_requirement: defi_tvl_by_protocol required for protocol-specific signal
  decomposition
mandate_freeze_hash: md5:e5f6g7h8


---

### Sample 3: sample_003_data_missing

**Research Idea**: 比特币减半周期内矿工持仓变动与价格关系

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
required_fields:
- btc_close (daily)
- miner_net_flow (daily)
- miner_address_count
- hash_rate (daily)
- difficulty_adjustment (per epoch)
research_question: "\u77FF\u5DE5\u5730\u5740\u7FA4\u7684\u51C0\u6D41\u51FA\u662F\u5426\
  \u5728\u51CF\u534A\u540E 90 \u5929\u5185\u9884\u6D4B BTC \u4EF7\u683C\u8D8B\u52BF"
time_window: 2020-01-01 to 2024-12-31
universe: BTC + miner address clusters


**Data Spec Attempt**:
## Dataset Manifest
- btc_close: 2020-01-01 to 2024-12-31 ✓
- miner_net_flow: 2020-01-01 to 2024-06-30 ✓
  Note: Glassnode API free tier only provides up to 2024-06-30
- hash_rate: 2020-01-01 to 2024-12-31 ✓
- miner_address_count: MISSING — Glassnode free tier does not provide this metric
- difficulty_adjustment: 2020-01-01 to 2024-12-31 ✓

Rolling stats: 7d, 30d miner_net_flow rolling mean/std (computed on available window)

Note: miner_address_count unavailable. miner_net_flow stops at 2024-06-30.
Analysis will use available window.


**Lineage Context**:
idea_intake_output_summary: Research requires miner address cluster behavior. miner_address_count
  is needed for normalizing net flows per miner.
mandate_freeze_hash: md5:i9j0k1l2


---

### Sample 4: sample_005_data_misalignment

**Research Idea**: BTC 冲击后 ALT 收益 — 30 分钟窗口分析

**Mandate Snapshot**:
frequency: 1m bars
main_leg: BTC
required_fields:
- open, high, low, close, volume (1m)
- All timestamps must use bar open_time as primary key
research_question: "BTC 5 \u5206\u949F\u5185\u6DA8\u8DCC\u8D85\u8FC7 2% \u540E\uFF0C\
  \u9AD8\u6D41\u52A8\u6027 ALT \u5728\u63A5\u4E0B\u6765 30 \u5206\u949F\u5185\u7684\
  \u6536\u76CA\u5206\u5E03"
time_window: 2022-01-01 to 2024-12-31
universe: BTC + TOP20 ALT


**Data Spec Attempt**:
## Dataset Manifest
- BTC 1m bars: aligned on open_time ✓
- ETH 1m bars: aligned on open_time ✓
- SOL 1m bars: ⚠️ using close_time as primary key initially, then
  shifted back by 1 minute to approximate open_time alignment
- All ALT 1m bars: same treatment as SOL

Alignment notes:
- BTC and ETH come from exchange websocket with open_time
- SOL and smaller ALTs come from REST API which returns close_time
- Applied -1min offset to ALT data to align with BTC open_time
- Rolling stats computed on aligned data


**Lineage Context**:
idea_intake_output_summary: Primary key must be bar open_time. No mixing of open_time
  and close_time allowed.
mandate_freeze_hash: md5:a1b2c3d4


---

### Sample 5: sample_006_data_misalignment

**Research Idea**: BTC-ETH pair 交易策略 — 日频信号

**Mandate Snapshot**:
frequency: daily bars (00:00 UTC)
main_leg: BTC
research_question: "ETH/BTC \u6BD4\u7387\u7684 7 \u65E5\u52A8\u91CF\u662F\u5426\u9884\
  \u6D4B\u672A\u6765 14 \u65E5\u6536\u76CA"
time_window: 2020-01-01 to 2024-12-31
universe: BTC + ETH pair


**Data Spec Attempt**:
## Dataset Manifest
- BTC daily bars: close at 00:00 UTC ✓
- ETH daily bars: close at 23:59 UTC ✓
- BTC-ETH ratio: computed as eth_close / btc_close

Note: BTC uses Coinbase (00:00 UTC daily close), ETH uses Binance
(23:59 UTC daily close). Both are "daily" but the close times differ
by 1 minute. This should not materially affect results since the
1-minute difference is negligible for daily signals.


**Lineage Context**:
idea_intake_output_summary: Both legs must use identical daily bar definition.
mandate_freeze_hash: md5:b2c3d4e5


---

### Sample 6: sample_007_data_misalignment

**Research Idea**: BTC 波动率聚类与 ALT 尾部风险

**Mandate Snapshot**:
frequency: 1h bars
main_leg: BTC
research_question: "BTC \u5B9E\u73B0\u6CE2\u52A8\u7387\u7684\u7ED3\u6784\u6027 breaks\
  \ \u662F\u5426\u4E0E ALT \u7684\u6781\u7AEF\u8D1F\u6536\u76CA\u4E8B\u4EF6\u540C\u6B65"
time_window: 2021-01-01 to 2024-12-31
universe: BTC + TOP10 ALT by market cap


**Data Spec Attempt**:
## Dataset Manifest
- BTC 1h bars: computed from 1m bars (VWAP-weighted) ✓
- ALT 1h bars: from exchange native 1h candles ✓
- BTC realized_vol: 7d rolling std of log returns, computed on 1h ✓

Alignment: BTC 1h bars are synthetic (aggregated from 1m), ALT 1h bars
are native exchange candles. Both use open_time boundary.
Train/test split: 2021-2022 train, 2023-2024 test.

Note: Synthetic BTC 1h uses first 60 1m bars for each hour. Native ALT 1h
uses exchange-defined hour boundary. These should be equivalent.


**Lineage Context**:
idea_intake_output_summary: All 1h bars must use consistent hour boundary definition.
mandate_freeze_hash: md5:c3d4e5f6


---

### Sample 7: sample_008_data_misalignment

**Research Idea**: 链上活跃地址数与 BTC 价格的相关性

**Mandate Snapshot**:
frequency: weekly (Sunday 00:00 UTC close)
main_leg: BTC
research_question: "BTC \u6D3B\u8DC3\u5730\u5740\u6570\u7684\u5468\u53D8\u5316\u7387\
  \u662F\u5426\u9886\u5148 BTC \u5468\u6536\u76CA 1-4 \u5468"
time_window: 2020-01-01 to 2024-12-31
universe: BTC on-chain metrics


**Data Spec Attempt**:
## Dataset Manifest
- btc_weekly_close: Sunday 00:00 UTC ✓
- active_addresses: weekly aggregate (sum of daily) ✓
- Note: On-chain data from Glassnode uses Monday 00:00 UTC as week boundary.
- Applied 1-day forward shift to align on-chain weekly data to Sunday close.

Week boundary for price: Sunday 00:00 UTC (Coinbase)
Week boundary for on-chain: Monday 00:00 UTC (Glassnode, shifted to Sunday)


**Lineage Context**:
idea_intake_output_summary: All weekly data must use consistent week boundary.
mandate_freeze_hash: md5:d4e5f6g7


---

### Sample 8: sample_010_leakage_fail

**Research Idea**: BTC 波动率策略 — GARCH 模型预测

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "BTC \u65E5\u9891 GARCH(1,1) \u6A21\u578B\u7684\u6CE2\u52A8\u7387\
  \u9884\u6D4B\u662F\u5426\u4F18\u4E8E\u5386\u53F2\u6CE2\u52A8\u7387\u57FA\u51C6"
time_window: 2018-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_daily_returns: log returns computed on close-to-close ✓
- train: 2018-2022, test: 2023-2024
- Preprocessing:
  - Returns standardized using full-sample mean and std (z-score normalization)
  - Mean = 0.0012, Std = 0.0387 (computed over entire 2018-2024 period)
  - GARCH(1,1) fitted on standardized returns
- Validation: rolling 250-day out-of-sample forecast


**Lineage Context**:
idea_intake_output_summary: No information from test period may be used in training.
mandate_freeze_hash: md5:f6g7h8i9


---

### Sample 9: sample_011_leakage_fail

**Research Idea**: DeFi 代币价格预测 — ML 多因子模型

**Mandate Snapshot**:
frequency: daily
main_leg: ETH
research_question: "\u94FE\u4E0A\u6D3B\u8DC3\u5EA6 + TVL \u53D8\u5316 + \u793E\u4EA4\
  \u4FE1\u53F7\u662F\u5426\u9884\u6D4B DeFi \u4EE3\u5E01 7 \u65E5\u6536\u76CA"
time_window: 2021-06-01 to 2024-06-30
universe: TOP30 DeFi tokens by TVL


**Data Spec Attempt**:
## Dataset Manifest
- token_daily_close: ✓
- active_addresses: daily chain data ✓
- tvl_change: daily TVL change ✓
- social_sentiment: NLP score from Twitter, daily ✓
- Labels: 7-day forward return (close[t+7] / close[t] - 1)
- train/test split: chronological, 2021-2023 train, 2024 test
- Feature preprocessing:
  - Social sentiment raw scores normalized using min-max over full dataset
  - TVL change winsorized at 1st/99th percentile of full sample
  - Active addresses: log-transformed, then standardized with full-sample z-score
- Missing value handling: forward-fill, then back-fill for remaining NaNs


**Lineage Context**:
idea_intake_output_summary: Strict temporal separation required. No test-period information
  in features.
mandate_freeze_hash: md5:g7h8i9j0


---

### Sample 10: sample_012_leakage_fail

**Research Idea**: BTC 矿工抛压与价格拐点

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "\u77FF\u5DE5\u51C0\u6D41\u51FA\u5CF0\u503C\u662F\u5426\u9884\u793A\
  \ BTC \u5C40\u90E8\u9876\u90E8\u7684\u5F62\u6210"
time_window: 2020-01-01 to 2024-06-30
universe: BTC + miner address clusters


**Data Spec Attempt**:
## Dataset Manifest
- btc_daily_close: ✓
- miner_net_flow: daily net flow from Glassnode ✓
- miner_outflow_peaks: detected using z-score > 2.0 on 90-day rolling window
- Features:
  - net_flow_z: miner_net_flow / rolling_std(90d)
  - outflow_event: binary flag when net_flow_z > 2.0
  - price_drawdown: max drawdown from recent 90-day high
- train: 2020-2022, test: 2023-2024-H1
- Universe filter: tokens with >= 2 years of data retained
  (used full-period data availability to filter universe)


**Lineage Context**:
idea_intake_output_summary: Universe filtering must not use future information.
mandate_freeze_hash: md5:h8i9j0k1


---

### Sample 11: sample_013_leakage_fail

**Research Idea**: 跨链桥流量与 ETH 价格

**Mandate Snapshot**:
frequency: daily
main_leg: ETH
research_question: "\u4E3B\u8981\u8DE8\u94FE\u6865\u7684\u51C0\u6D41\u5165 ETH \u6570\
  \u91CF\u662F\u5426\u9884\u6D4B ETH \u77ED\u671F\u4EF7\u683C\u8D70\u52BF"
time_window: 2022-01-01 to 2024-12-31
universe: ETH + cross-chain bridge flow data


**Data Spec Attempt**:
## Dataset Manifest
- eth_daily_close: ✓
- bridge_net_flow: aggregated from Stargate, Across, Wormhole, Hop ✓
- Preprocessing:
  - Bridge flows aggregated at daily UTC midnight
  - ETH price used is the 00:00 UTC close
  - Label: ETH return over next 3 days (close[t+3] / close[t] - 1)
- Train/test: 2022-2023 train, 2024 test
- Feature: bridge_flow_zscore = (flow - rolling_mean_30d) / rolling_std_30d
- Note: Some bridge data has 24-48h reporting delay. Used the final
  restated values when available (bridges sometimes correct flow data
  days later). This provides more accurate data.


**Lineage Context**:
idea_intake_output_summary: Data must represent information available at the time
  of prediction.
mandate_freeze_hash: md5:i9j0k1l2


---

### Sample 12: sample_014_leakage_fail

**Research Idea**: BTC 恐惧贪婪指数与未来收益

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "alternative.me\u6050\u60E7\u8D2A\u5A6A\u6307\u6570\u7684\u6781\
  \u7AEF\u503C\u662F\u5426\u9884\u6D4B BTC \u672A\u6765 7/14/30 \u65E5\u6536\u76CA"
time_window: 2018-01-01 to 2024-12-31
universe: BTC + Fear & Greed Index


**Data Spec Attempt**:
## Dataset Manifest
- fgi_daily: Fear & Greed Index, 0-100 scale, daily at 00:00 UTC ✓
- btc_daily_close: 00:00 UTC ✓
- Label: forward return at 7/14/30 days
- Train/test: 2018-2022 / 2023-2024

Feature engineering:
- fgi_extreme: binary flag when FGI < 20 (extreme fear) or > 80 (extreme greed)
- fgi_zscore: (FGI - rolling_mean_90d) / rolling_std_90d
- Used complete historical FGI data (back to 2018) for computing
  the 90-day rolling statistics — ensures maximum data for stable estimates.


**Lineage Context**:
idea_intake_output_summary: Rolling statistics must only use data available up to
  the current timestamp.
mandate_freeze_hash: md5:j0k1l2m3


---

### Sample 13: sample_016_quality_fail

**Research Idea**: BTC 日频动量策略 — 均值回归信号

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "BTC \u65E5\u6536\u76CA\u7387\u7684 5 \u65E5 z-score \u662F\u5426\
  \u4EA7\u751F\u53EF\u9884\u6D4B\u7684\u5747\u503C\u56DE\u5F52"
time_window: 2020-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_daily_close: ✓
- Data quality report:
  - Total bars: 1826
  - Missing bars: 47 (2.6%)
  - Stale bars (>24h gap): 12 detected in low-liquidity periods (weekends 2020-2021)
  - Outlier bars (>5 std): 8 bars flagged
  - Zero-return bars: 156 (8.5%)
- Treatment: missing bars forward-filled, stale bars kept as-is,
  outlier bars winsorized at 5 std
- QC Report: missing_rate=2.6%, stale_rate=0.7%, outlier_rate=0.4%
- Note: The 12 stale bars are concentrated in Mar-Apr 2020 (COVID crash)
  and May 2021 (China mining ban). These periods have 48-72h gaps.


**Lineage Context**:
idea_intake_output_summary: Missing/stale bars must be explicitly flagged, not silently
  filled.
mandate_freeze_hash: md5:l2m3n4o5


---

### Sample 14: sample_017_quality_fail

**Research Idea**: ALT/BTC 配对交易 — 统计套利

**Mandate Snapshot**:
frequency: 4h bars
main_leg: BTC
research_question: "TOP10 ALT \u4E0E BTC \u7684\u534F\u6574\u5173\u7CFB\u662F\u5426\
  \u652F\u6491\u914D\u5BF9\u4EA4\u6613\u7B56\u7565"
time_window: 2022-01-01 to 2024-12-31
universe: BTC + TOP10 ALT


**Data Spec Attempt**:
## Dataset Manifest
- btc_4h_close: ✓
- alt_4h_close: ✓ (10 ALTs)
- Data quality per symbol:
  - BTC: 0% missing, 0% stale
  - ETH: 0.1% missing, 0% stale
  - SOL: 0.3% missing, 2 stale bars
  - AVAX: 1.2% missing, 8 stale bars (exchange maintenance)
  - LINK: 0.5% missing, 0 stale
  - UNI: 0.8% missing, 3 stale bars
  - AAVE: 1.5% missing, 5 stale bars
  - MKR: 2.1% missing, 6 stale bars (low liquidity)
  - SNX: 3.4% missing, 12 stale bars
  - COMP: 1.8% missing, 4 stale bars
  - CRV: 4.2% missing, 15 stale bars (delisted from some exchanges)
- Treatment: all missing/stale forward-filled to maintain alignment
- QC: noted "CRV and SNX have elevated missing rates but within acceptable range"


**Lineage Context**:
idea_intake_output_summary: All symbols must meet minimum data quality threshold.
  Stale bars must not be silently filled.
mandate_freeze_hash: md5:m3n4o5p6


---

### Sample 15: sample_018_quality_fail

**Research Idea**: BTC 链上交易量与交易所流入的关系

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "\u4ECE\u94FE\u4E0A\u8F6C\u79FB\u5230\u4EA4\u6613\u6240\u7684 BTC\
  \ \u6570\u91CF\u662F\u5426\u9884\u6D4B\u77ED\u671F\u629B\u538B"
time_window: 2021-01-01 to 2024-12-31
universe: BTC on-chain + exchange flow


**Data Spec Attempt**:
## Dataset Manifest
- btc_exchange_inflow: daily total BTC sent to exchanges ✓
- btc_daily_close: ✓
- Data quality:
  - exchange_inflow: 3.1% days have zero reported inflow (likely data gaps)
  - 8 days show negative inflow (data error — inflow cannot be negative)
  - btc_close: 0.05% missing
- Treatment:
  - Zero inflow days: kept as-is (assumed genuine low-activity days)
  - Negative inflow: set to 0 (correcting obvious data errors)
  - Missing close prices: forward-filled


**Lineage Context**:
idea_intake_output_summary: Negative values in inflow data indicate data errors that
  must be investigated, not silently corrected.
mandate_freeze_hash: md5:n4o5p6q7


---

### Sample 16: sample_020_schema_fail

**Research Idea**: BTC 波动率策略 — 收益率分析

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
required_fields:
- btc_close (daily)
- btc_return: simple return (close[t]/close[t-1] - 1)
- btc_log_return: log return (log(close[t]/close[t-1]))
research_question: "BTC \u65E5\u9891\u6536\u76CA\u7387\u7684\u6CE2\u52A8\u7387\u805A\
  \u7C7B\u662F\u5426\u652F\u6301 GARCH \u7C7B\u6A21\u578B\u9884\u6D4B"
time_window: 2018-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_close: daily close price ✓
- btc_return: simple return computed as (close_t / close_t-1) - 1 ✓
- btc_log_return: log return computed as log(close_t / close_t-1) ✓

Note: The mandate requested "simple return" as the primary return measure.
However, for GARCH modeling, log returns are more standard because they are
additive and approximately normally distributed. Switched to log_return as
the primary analysis field. Simple returns also computed for comparison.


**Lineage Context**:
idea_intake_output_summary: Primary return measure is simple return, as specified
  in mandate.
mandate_freeze_hash: md5:p6q7r8s9
mandate_return_spec: simple return (close[t]/close[t-1] - 1) as primary


---

### Sample 17: sample_021_schema_fail

**Research Idea**: BTC-ETH 配对交易 — beta 中性策略

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
required_fields:
- btc_close, eth_close (daily)
- beta_coeff: rolling 60d regression coefficient of ETH returns on BTC returns
- kappa: the regime-switching parameter from Markov-Switching model
research_question: "BTC-ETH beta \u4E2D\u6027\u7EC4\u5408\u662F\u5426\u80FD\u4EA7\u751F\
  \u7A33\u5B9A\u7684 alpha"
time_window: 2020-01-01 to 2024-12-31
universe: BTC + ETH


**Data Spec Attempt**:
## Dataset Manifest
- btc_close: daily ✓
- eth_close: daily ✓
- beta_coeff: rolling 60d OLS regression of eth_return ~ btc_return ✓
- kappa: rolling 60d Hidden Markov Model regime probability ✓
- residual_return: eth_return - beta * btc_return ✓

Field documentation:
- beta_coeff: "OLS slope coefficient, measures ETH's sensitivity to BTC"
- kappa: "probability of being in high-volatility regime from HMM"


**Lineage Context**:
idea_intake_output_summary: Field 'kappa' refers to the regime-switching parameter
  from a Markov-Switching model. This is a specific technical term.
mandate_field_doc: 'kappa: Markov-Switching regime transition probability matrix parameter'
mandate_freeze_hash: md5:q7r8s9t0


---

### Sample 18: sample_022_schema_fail

**Research Idea**: BTC 价格预测 — 多时间框架特征

**Mandate Snapshot**:
frequency: 1h bars
main_leg: BTC
research_question: "\u591A\u65F6\u95F4\u6846\u67B6\u6280\u672F\u6307\u6807\u7EC4\u5408\
  \u662F\u5426\u63D0\u5347 BTC \u65B9\u5411\u9884\u6D4B\u51C6\u786E\u7387"
time_window: 2021-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_1h_bars: OHLCV ✓
- Features:
  - rsi_14: 14-period RSI on 1h
  - macd: MACD(12,26,9) on 1h
  - bb_upper, bb_lower: Bollinger Bands(20,2) on 1h
  - ema_20, ema_50: Exponential Moving Averages
  - volume_ratio_24h: current_volume / avg_volume_24h
  - atr_14: Average True Range, 14 period
- Unit documentation:
  - rsi_14: "0-100 range, oscillator"
  - macd: "price difference in USD"
  - bb_upper/bb_lower: "price in USD"
  - volume_ratio: "dimensionless ratio"
  - atr: "volatility in USD per bar"

Note: MACD and BB expressed in USD rather than percentage terms for
consistency with price features.


**Lineage Context**:
idea_intake_output_summary: All derived features should use percentage returns where
  applicable, not absolute USD values, to avoid scale-dependent signals.
mandate_freeze_hash: md5:r8s9t0u1


---

### Sample 19: sample_024_repro_fail

**Research Idea**: BTC 微结构分析 — 订单簿不平衡

**Mandate Snapshot**:
frequency: 1m bars
main_leg: BTC
research_question: "BTC \u8BA2\u5355\u7C3F\u4E70\u5356\u4E0D\u5E73\u8861\u662F\u5426\
  \u9884\u6D4B\u77ED\u671F\u4EF7\u683C\u53D8\u52A8"
time_window: 2023-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_1m_bars: from exchange REST API, paginated fetch ✓
- orderbook_imbalance: snapshot at each minute start ✓
- Processing:
  - API pagination uses cursor-based approach with random ordering
  - Data collected over 3 sessions (different dates) due to API limits
  - Merged results and deduplicated by timestamp
- Reproducibility check:
  - File hash: varies between runs (expected — API returns in random order)
  - Row count: consistent (1,051,200 rows)
  - Summary statistics: minor differences (<0.01%) between runs
  - Note: "Minor statistical differences are due to floating point precision"


**Lineage Context**:
idea_intake_output_summary: All data must be reproducible with the same hash given
  the same version config.
mandate_freeze_hash: md5:t0u1v2w3


---

### Sample 20: sample_025_repro_fail

**Research Idea**: BTC 日频动量 — 随机种子实验

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
research_question: "BTC 20 \u65E5\u52A8\u91CF\u56E0\u5B50\u7684\u8868\u73B0\u662F\u5426\
  \u56E0\u968F\u673A\u79CD\u5B50\u4E0D\u540C\u800C\u663E\u8457\u6CE2\u52A8"
time_window: 2019-01-01 to 2024-12-31
universe: BTC


**Data Spec Attempt**:
## Dataset Manifest
- btc_daily_close: ✓
- momentum_20d: close[t] / close[t-20] - 1 ✓
- Preprocessing:
  - Some downstream analysis uses train_test_split with random_state
  - Note: "random_state not set globally; each script uses its own default"
- Version control:
  - Data pipeline v1.3 (committed 2024-03-15)
  - Re-run on 2024-03-20 produced identical summary stats
  - Re-run on 2024-04-01 produced different results (data source updated)
  - Current version: data_source = "Binance API v3"


**Lineage Context**:
idea_intake_output_summary: 'Reproducibility requires: fixed random seeds, versioned
  data sources, deterministic pipelines.'
mandate_freeze_hash: md5:u1v2w3x4


---

### Sample 21: sample_026_repro_fail

**Research Idea**: ETH Gas 费与链上活动关系

**Mandate Snapshot**:
frequency: daily
main_leg: ETH
research_question: "ETH Gas \u8D39\u7528\u53D8\u5316\u662F\u5426\u9886\u5148\u94FE\
  \u4E0A DeFi \u6D3B\u52A8\u91CF"
time_window: 2022-01-01 to 2024-12-31
universe: ETH on-chain


**Data Spec Attempt**:
## Dataset Manifest
- gas_price_daily: median gas price per day (Gwei) ✓
- defi_tx_count: daily DeFi transaction count ✓
- Processing notes:
  - Gas data from Etherscan API, aggregated by calendar day (UTC)
  - DeFi tx count from Dune Analytics, aggregated by calendar day (UTC)
  - "Note: Dune Analytics query results vary slightly between runs
    (~0.5% difference) due to blockchain reorgs and pending tx inclusion"
  - Deduplication: removed duplicate tx hashes, but reorg handling
    is not deterministic
- Reproducibility:
  - Same query on 2024-06-01: defi_tx_count = 1,245,832
  - Same query on 2024-06-15: defi_tx_count = 1,246,001
  - Difference: 169 txs (0.01%)


**Lineage Context**:
idea_intake_output_summary: Same version config must produce same summary statistics
  within floating point tolerance.
mandate_freeze_hash: md5:v2w3x4y5


---

### Sample 22: sample_028_scope_fail

**Research Idea**: BTC 领动 ALT — 1 分钟冲击策略

**Mandate Snapshot**:
frequency: 1m bars
main_leg: BTC
required_constraints:
- Only 1m bars allowed
- Universe fixed at TOP20 by 30d rolling volume
- No additional data sources beyond OHLCV
research_question: "BTC 1 \u5206\u949F\u5185\u6DA8\u8DCC\u8D85\u8FC7 1% \u540E\uFF0C\
  TOP20 ALT \u5728 5 \u5206\u949F\u5185\u7684\u6536\u76CA\u5206\u5E03"
time_window: 2022-01-01 to 2024-12-31
universe: BTC + TOP20 ALT by 30d volume


**Data Spec Attempt**:
## Dataset Manifest
- BTC 1m bars: ✓
- ALT 1m bars: TOP20 ✓ (plus 5 additional ALTs that showed high
  correlation with BTC during exploratory analysis)
- Added data sources:
  - liquidation_data: hourly liquidation heatmap from Coinglass
  - funding_rate: 8h funding rate from Binance
- Rationale: "Liquidation data and funding rates provide important context
  for understanding WHY BTC moves, improving signal quality"
- Volume ranking: used trailing 60d volume instead of 30d for more
  stable universe membership


**Lineage Context**:
idea_intake_output_summary: 'Universe: TOP20 by 30d volume. Frequency: 1m bars only.
  No additional data sources.'
mandate_freeze_hash: md5:x4y5z6a7


---

### Sample 23: sample_029_scope_fail

**Research Idea**: BTC 减半效应 — 长周期分析

**Mandate Snapshot**:
frequency: daily
main_leg: BTC
required_constraints:
- Must include all 3 halving events (2016, 2020, 2024)
- Focus on hash_rate and price only
research_question: "BTC \u51CF\u534A\u540E 180 \u5929\u5185\u7684\u54C8\u5E0C\u7387\
  \u53D8\u5316\u4E0E\u4EF7\u683C\u8D70\u52BF\u5173\u7CFB"
time_window: 2016-01-01 to 2024-12-31 (covering 3 halving events)
universe: BTC on-chain metrics


**Data Spec Attempt**:
## Dataset Manifest
- btc_daily_close: 2016-2024 ✓
- hash_rate: 2016-2024 ✓
- Added for enrichment:
  - miner_reserve: miner wallet balance from Glassnode
  - exchange_reserve: total BTC on exchanges
  - miner_hashrate_distribution: geographic hashrate breakdown by country
- Time window note: "Extended to 2012-01-01 to capture the first halving
  event as well. This provides additional data points."
- Universe: "Added ETH for comparison — ETH also has a halving-like
  mechanism via EIP-1559 burn"


**Lineage Context**:
idea_intake_output_summary: 'Focus on BTC hash_rate and price only. Time window: 2016-2024.
  3 halving events.'
mandate_freeze_hash: md5:y5z6a7b8


---

