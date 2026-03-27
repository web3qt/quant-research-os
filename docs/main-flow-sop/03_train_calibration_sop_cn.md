# 03\_train\_calibration\_sop — Train Calibration 阶段标准操作流程（机构级）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TRAINCAL-v1.0 |
| 日期 | 2026-03-27 |
| 状态 | Active |
| Owner | Strategy Research / Quant Dev |
| 依赖 | `research_workflow_master_spec`, `workflow_stage_gates.yaml`, `02_signal_ready` |

---

## 1. 文档目的

本文档是 Train Calibration 阶段的唯一正式 SOP。

它解决的核心问题只有一个：**如何在不接触未来窗口的前提下，把尺子定下来。**

这里的"尺子"包括：

- 分位阈值（用于区分信号强度分层的切点）；
- Regime 切点（用于区分市场状态的边界）；
- 质量过滤条件（用于排除不可研究对象的规则）；
- 波动分层标准（用于风险归类的分档条件）；
- 候选参数范围（用于限制后续 Test 阶段的搜索空间）。

本文档不负责解释 signal_ready 产物的含义（参见 `02_signal_ready_sop_cn.md`），也不负责 Test 阶段如何使用冻结产物（参见 `04_test_evidence_sop_cn.md`）。它只负责从 signal_ready 冻结产物出发，到 train 冻结产物交付为止的全部操作规范。

**根本立场**：Train 的职责是校准，不是验收。Train 应该冻结阈值、分位切点、质量过滤、波动分层和候选参数范围，不应宣布哪一组已经"成功"。

---

## 2. 阶段定位

### 2.1 在 Workflow 中的位置

```
data_ready → signal_ready → [train_calibration] → test_evidence → backtest → holdout → shadow
```

Train Calibration 位于 signal_ready 之后、test_evidence 之前。它的上游负责把信号实例化，它的下游负责用独立样本验证结构。本阶段处于两者之间，只做一件事：**用训练窗数据把度量标准定死**。

### 2.2 与 Test 阶段的分工

| 维度 | Train Calibration | Test Evidence |
|------|-------------------|---------------|
| 职责 | 冻结尺子 | 用冻结尺子验证结构 |
| 数据窗 | 仅训练窗 | 仅测试窗 |
| 产出 | 阈值、切点、参数台账 | 白名单、best\_h、frozen\_spec |
| 允许做的事 | 定标准、排除荒谬参数 | 对比冻结标准与新样本 |
| 禁止做的事 | 选最终赢家 | 重估 train 阈值 |

### 2.3 阶段核心问题

> 后续 Test 应该拿哪把已经冻结的尺子去验证，而不是边验证边重估。

如果 Train 没有把尺子定下来，Test 就没有锚点；如果 Train 定的尺子偷看了未来数据，整条研究线的独立性就被污染。

---

## 3. 适用范围

本 SOP 适用于所有正式进入研究管线的系统化研究线（lineage），包括：

- 信号研究的参数校准阶段；
- 因子筛选与白名单研究的训练阈值冻结；
- 多标的策略的 regime 定标与波动分层；
- 任何需要在独立测试前冻结度量标准的场景。

不适用于：

- 一次性 notebook 草稿探索；
- 没有冻结研究问题的临时分析；
- 不进入 test\_evidence 阶段的非正式实验。

---

## 4. 执行步骤

### 4.1 确认上游冻结产物

在开始任何 Train 操作之前，必须确认以下上游冻结产物存在且未被篡改：

- `signal_ready` 阶段的 `param_manifest.csv`、`signal_coverage.csv`、`signal_fields_contract.md`；
- Mandate 文档中定义的 `time_split.json`（含训练窗、测试窗、回测窗、holdout 窗的边界）；
- Mandate 文档中定义的参数网格（parameter grid）。

**核查方式**：对比上游 gate 文档中记录的文件哈希与本地文件哈希。如果不一致，停止操作并回退到 signal\_ready 审计。

### 4.2 定义训练窗边界

从 `time_split.json` 中读取训练窗的起止日期，确认：

1. 训练窗的终止日期严格早于测试窗的起始日期；
2. 训练窗与测试窗之间如有 gap（隔离带），记录 gap 的长度和理由；
3. 训练窗的实际可用交易日数量满足 mandate 要求的最低样本量。

将训练窗定义写入 `train_thresholds.json` 的 `window` 字段，作为后续所有估计的时间约束。

### 4.3 计算分位阈值

在训练窗内，对信号列（或因子列）计算分位切点。典型做法：

1. 确定分位档位（例如 5 档：0-20%, 20-40%, 40-60%, 60-80%, 80-100%）；
2. 按标的或按 pooled 方式计算分位边界值；
3. 记录每个分位的样本量和边界值；
4. 如果存在极端值处理规则（winsorize、clip），在此步骤执行并记录处理前后的分位差异。

**输出**：分位阈值写入 `train_thresholds.json` 的 `quantile_cuts` 字段。

### 4.4 冻结 Regime 切点

Regime 切点是区分市场状态（如高波 / 低波、上行 / 下行、高流动性 / 低流动性）的边界值。

1. 在训练窗内估计 regime 切点，使用的指标（例如 VIX 分位、realized vol 阈值、turnover 分位）必须明确记录；
2. **在 gate 文档中写明切点所依据的样本特征**，包括：
   - 用于估计切点的具体指标名称和计算方式；
   - 训练窗内该指标的均值、标准差、中位数、极值；
   - 切点对应的分位位置（例如"高波 regime 定义为 realized vol > 训练窗 75th percentile"）；
   - 训练窗内各 regime 的样本占比。
3. 冻结 regime 切点写入 `train_thresholds.json` 的 `regime_cuts` 字段。

### 4.5 执行信号可研究性过滤

在冻结阈值之后，对参数空间中的候选对象执行可研究性过滤：

1. **数据充分性检查**：训练窗内有效观测数量低于阈值的 symbol-param 组合标记为不可研究；
2. **信号方差检查**：信号在训练窗内几乎恒定（方差接近零）的标记为不可研究；
3. **极端集中度检查**：信号值超过 95% 落在单一分位的标记为不可研究；
4. **缺失率检查**：训练窗内缺失率超过指定上限的标记为不可研究。

被过滤的对象写入 `train_rejects.csv`，**每条记录必须标注拒绝原因代码和对应的阈值**。

### 4.6 参数粗筛

参数粗筛的目的是**排除荒谬区间**，而不是选出最优参数。

1. 定义参数的合理区间上下界（例如回看窗口 < 5 天视为噪声过多，> 250 天视为信号过慢）；
2. 对参数网格中落在荒谬区间的参数组合标记为 rejected；
3. **不允许在此步骤使用收益最大化、Sharpe 排名或任何样本外指标**来筛选参数；
4. 粗筛理由只能基于经济学直觉、信号定义的物理约束或数据可用性约束。

通过粗筛的参数和被拒绝的参数分别写入 `train_param_ledger.csv` 和 `train_rejects.csv`。

### 4.7 记录搜索过程统计

这是本阶段的新增强制要求。目的是防止"只保留通过参数、不保留搜索轨迹"的黑箱操作。

**必须记录以下统计量并保存到 `search_statistics.json`**：

| 字段 | 含义 | 说明 |
|------|------|------|
| `total_configurations_evaluated` | 参与评估的配置总数 | 包括 symbol-param 所有组合 |
| `configurations_passed` | 通过所有过滤的配置数 | 进入 train\_param\_ledger 的数量 |
| `configurations_rejected` | 被拒绝的配置数 | 进入 train\_rejects 的数量 |
| `median_metric` | 全部配置的中位指标值 | 使用 train 窗内的指定评估指标 |
| `best_metric` | 最佳配置的指标值 | 同上 |
| `best_vs_median_z` | 最佳 vs 中位的 z-score | `(best - median) / std_of_all` |

`configurations_passed + configurations_rejected` 必须等于 `total_configurations_evaluated`。如果不等，必须在文档中说明差异原因（例如某些配置因数据不足被排除在评估之外）。

### 4.8 生成 train\_param\_ledger 和 train\_rejects

**train\_param\_ledger.csv**：保留所有通过粗筛和可研究性过滤的参数配置，每行至少包含：

- `param_id`：参数配置的唯一标识；
- `symbol`：标的标识（如适用）；
- `param_values`：参数值（JSON 或展开列）；
- `pass_reason`：标注为何保留（例如"区间合理 + 数据充分 + 信号可研究"）；
- `train_metric`：训练窗内的评估指标值。

**train\_rejects.csv**：保留所有被拒绝的参数配置，每行至少包含：

- `param_id`、`symbol`、`param_values`（同上）；
- `reject_reason`：拒绝原因代码（例如 `INSUFFICIENT_DATA`、`ZERO_VARIANCE`、`ABSURD_RANGE`）；
- `reject_threshold`：触发拒绝的具体阈值。

### 4.9 生成 train\_thresholds

`train_thresholds.json` 是本阶段最核心的冻结产物，下游 Test 阶段直接消费。其结构应至少包含：

```json
{
  "version": "1.0",
  "frozen_at": "2026-03-27T00:00:00Z",
  "window": {
    "train_start": "2020-01-01",
    "train_end": "2023-12-31",
    "gap_days": 30
  },
  "quantile_cuts": {
    "method": "pooled",
    "bins": 5,
    "boundaries": [0.12, 0.34, 0.58, 0.81]
  },
  "regime_cuts": {
    "indicator": "realized_vol_20d",
    "high_threshold": 0.025,
    "low_threshold": 0.012,
    "estimation_sample_stats": {
      "mean": 0.018,
      "std": 0.007,
      "median": 0.016,
      "p25": 0.013,
      "p75": 0.022,
      "min": 0.005,
      "max": 0.061
    }
  },
  "quality_filters": {
    "min_observations": 120,
    "max_missing_rate": 0.15,
    "min_signal_variance": 1e-6
  },
  "param_range": {
    "lookback_min": 10,
    "lookback_max": 120,
    "excluded_reason": "物理约束"
  }
}
```

### 4.10 生成 artifact\_catalog 和 field\_dictionary

**artifact\_catalog.md**：列出本阶段生成的所有文件，每个文件注明：

- 文件名与路径；
- 格式（JSON / Parquet / CSV / Markdown）；
- 用途说明；
- 是否为冻结产物（frozen = true/false）；
- 下游消费者（哪些阶段读取此文件）。

**field\_dictionary.md**：对所有 machine-readable artifact 中的字段给出定义：

- 字段名、类型、单位、取值范围、业务含义；
- 对于枚举字段，列出所有合法取值；
- 对于 JSON 嵌套结构，给出层级路径。

这两份文档是 gate 审计的必要前提。如果缺少，formal gate 无法通过。

### 4.11 自审与 gate 文档

完成上述步骤后，执行自审：

1. 检查所有 required\_outputs 是否存在并可解析；
2. 检查 `train_thresholds.json` 中的所有估计是否仅来源于训练窗；
3. 检查 `train_param_ledger.csv` 和 `train_rejects.csv` 的行数之和是否等于 `search_statistics.json` 中的 `total_configurations_evaluated`；
4. 检查每一条 reject 记录是否有明确的 `reject_reason`；
5. 检查每一条 pass 记录是否有明确的 `pass_reason`。

自审通过后，撰写 `train_gate_decision.md`，内容包括：

- Formal gate 各条的逐项检查结果；
- Audit-only 检查项的发现（不阻断晋级，但需记录）；
- Verdict（`PASS` / `CONDITIONAL PASS` / `PASS FOR RETRY` / `RETRY` / `CHILD LINEAGE`）；
- 如果不是 `PASS`，写明需要修复的具体事项和允许的修改范围。

---

## 5. 必备输出与 Artifact 规范

### 5.1 必备输出清单

| 文件 | 格式 | 性质 | 说明 |
|------|------|------|------|
| `train_thresholds.json` | JSON | 冻结产物 | 所有分位阈值、regime 切点、质量过滤条件、参数范围 |
| `train_quality.parquet` | Parquet | 冻结产物 | 训练窗内的质量评估数据（信号覆盖率、缺失率、方差等） |
| `train_param_ledger.csv` | CSV | 冻结产物 | 通过粗筛和过滤的所有参数配置及保留理由 |
| `train_rejects.csv` | CSV | 冻结产物 | 被拒绝的所有参数配置及拒绝理由 |
| `search_statistics.json` | JSON | 冻结产物 | 搜索过程统计摘要 |
| `train_gate_decision.md` | Markdown | 人工文档 | Gate 审计结果与 verdict |
| `artifact_catalog.md` | Markdown | 人工文档 | 本阶段所有产物目录 |
| `field_dictionary.md` | Markdown | 人工文档 | 所有 machine-readable 字段定义 |

### 5.2 search\_statistics.json 示例

```json
{
  "version": "1.0",
  "generated_at": "2026-03-27T10:30:00Z",
  "total_configurations_evaluated": 4800,
  "configurations_passed": 312,
  "configurations_rejected": 4488,
  "rejection_breakdown": {
    "INSUFFICIENT_DATA": 1200,
    "ZERO_VARIANCE": 88,
    "ABSURD_RANGE": 2400,
    "HIGH_MISSING_RATE": 800
  },
  "metric_name": "train_ic_mean",
  "median_metric": 0.012,
  "best_metric": 0.048,
  "std_metric": 0.015,
  "best_vs_median_z": 2.40,
  "notes": "metric 计算仅使用训练窗数据"
}
```

---

## 6. Formal Gate 规则

Formal gate 是阻断性检查。任何一条 fail\_any\_of 被触发，本阶段**不得**推进到 test\_evidence。

### 6.1 通过条件（pass\_all\_of，全部满足）

1. 所有训练阈值、regime 切点和辅助条件切点**仅使用训练窗估计**；
2. `train_param_ledger.csv` 和 `train_rejects.csv` 都已保存且非空；
3. 保留与拒绝的每一条记录都有明确原因（`pass_reason` / `reject_reason` 字段不得为空）；
4. `required_outputs` 中的全部文件存在，且 machine-readable artifact 都有 companion field documentation。

### 6.2 失败条件（fail\_any\_of，任一触发即失败）

1. **用 test 或 backtest 结果回写 train 阈值**——这是最严重的信息泄露，直接导致整条研究线的独立性丧失；
2. **只保留通过参数，不保留完整搜索轨迹**——缺少搜索轨迹就无法审计参数选择偏差；
3. **没有冻结阈值就进入 Test**——没有锚点的 Test 等于没有对照的实验。

---

## 7. Audit-Only 检查项

以下检查项不阻断晋级，但必须在 `train_gate_decision.md` 中如实记录发现：

1. **参数空间是否仍可 coarse-to-fine**：如果当前参数网格的粒度仍然很粗，后续是否需要在 child lineage 中进一步细化？记录当前网格的步长和覆盖范围。
2. **辅助条件切点是否需要在 child lineage 升级**：某些辅助变量（如波动率、成交量、市值分档）在当前 train 中只是附加条件。如果审计发现它们对结果有显著影响，应标记为"建议在 child lineage 中升级为正式机制"。

---

## 8. 常见陷阱与误区

### 8.1 "定尺子不是选赢家"详解

这是 Train Calibration 阶段最核心也最容易违反的原则。

**误区一：用 Train 窗内的 Sharpe/IC 排名选参数。**

Train 的参数台账应该记录所有通过合理性筛选的参数，而不是只保留表现最好的那几组。如果你在 Train 阶段就按 Sharpe 排名只保留 Top 5，那你实际上已经在 Train 窗内做了一次隐式的样本内选择，Test 阶段的独立性就打了折扣。

**正确做法**：Train 阶段只负责排除"物理上不合理"或"数据上不可研究"的参数。通过这两关的参数全部进入 ledger，等到 Test 阶段再看谁在独立样本中表现一致。

**误区二：看了 Test 结果觉得阈值定得不好，回头修 Train。**

这是信息泄露的典型路径。一旦你用 Test 窗的信息修正了 Train 的阈值，这把尺子就不再是在训练窗独立估计的了。

**正确做法**：如果确实需要修改 Train 阈值，必须走回退流程（见第 9 节），且修改后的所有下游结果必须重新生成。

**误区三：只保留通过参数不保留搜索轨迹。**

如果审计者只能看到 312 组通过的参数，看不到另外 4488 组被拒绝的参数，就无法判断通过率是否合理、拒绝标准是否一致、是否存在选择性报告。

**正确做法**：`train_param_ledger.csv` 和 `train_rejects.csv` 一起提交，缺一不可。`search_statistics.json` 提供汇总视角。

### 8.2 其他常见错误

- **训练窗边界模糊**：没有在 `train_thresholds.json` 中明确记录训练窗的起止日期，导致无法验证估计的时间纯洁性。
- **Regime 切点没有样本背景**：只写了"高波阈值 = 0.025"，没有写明这个值对应训练窗的什么分位、训练窗内的分布特征是什么。
- **质量过滤条件没有版本化**：过滤阈值在迭代过程中多次修改，但只保留了最终版本，无法审计变更历史。

---

## 9. 失败与回退

当 Train Calibration 阶段的 formal gate 未通过时，按以下流程处理：

### 9.1 允许的修改范围

在不污染研究线的前提下，允许在本阶段内修改：

- 训练阈值的估计方法或参数；
- 质量过滤条件和对应阈值；
- Ledger 生成逻辑（例如修正 `pass_reason` 的记录格式）。

修改后必须重新生成所有下游产物（`train_thresholds.json`、`train_param_ledger.csv`、`train_rejects.csv`、`search_statistics.json`），并重新执行自审。

### 9.2 必须开启 Child Lineage 的情况

以下情况视为信息污染，不允许在当前研究线内修复，必须开启 child lineage：

- **借用 test 或 backtest 信息修改 train 尺子**：无论修改幅度多小，只要 train 阈值的修改动机来自下游窗口的观察，就必须整体回退并开启新的研究线；
- **引入新的正式机制变量**：如果需要把某个辅助条件变量升级为正式的信号输入或过滤条件，而该变量未在上游 signal\_ready 阶段冻结，必须回退到 signal\_ready 并开启 child lineage。

### 9.3 详细失败处理流程

请参阅：[`../第二层-阶段失败 sop/03_train_freeze_failure_sop_cn.md`](../第二层-阶段失败%20sop/03_train_freeze_failure_sop_cn.md)

---

## 10. 阶段专属要求

### 10.1 搜索过程统计要求详解

搜索过程统计是本阶段的强制审计支撑。其目的不是评估策略好坏，而是确保搜索过程的透明度和可审计性。

**为什么需要 `total_configurations_evaluated`**：审计者需要知道搜索空间的全貌。如果只看到 312 组通过的参数，无法判断搜索空间是 500 组还是 50000 组，无法评估通过率是否合理。

**为什么需要 `configurations_rejected` 及其分类**：拒绝的理由分布比通过率本身更重要。如果 90% 的拒绝是因为"数据不足"，说明数据覆盖可能有问题；如果 90% 是因为"参数范围荒谬"，说明参数网格的设计可能过于宽泛。

**为什么需要 `median_metric` 和 `best_metric`**：如果 best 远好于 median，而中间没有连续过渡（即 best 是一个孤立的异常值），这可能是过拟合的信号。`best_vs_median_z` 就是衡量这一距离的简明指标。

### 10.2 best\_vs\_median\_z 解读指南

| z-score 范围 | 解读 | 建议 |
|-------------|------|------|
| < 1.0 | best 与 median 差异不大 | 正常，参数空间内结构平坦 |
| 1.0 - 2.0 | best 有一定优势 | 正常，可正常推进 |
| 2.0 - 3.0 | best 明显优于 median | 需检查是否为孤立峰，建议在审计中标注 |
| > 3.0 | best 异常偏离 median | 高度警惕过拟合或数据问题，建议 audit 重点关注 |

注意：z-score 本身不是 formal gate 的通过/失败条件，但 > 3.0 的情况应在 `train_gate_decision.md` 中专门讨论。

### 10.3 Regime 切点样本特征记录

冻结 regime 切点时，必须同时在 `train_thresholds.json` 的 `estimation_sample_stats` 字段和 `train_gate_decision.md` 中记录以下信息：

1. **指标名称与计算方式**：例如"realized\_vol\_20d = 过去20个交易日收益率的标准差"；
2. **训练窗内的描述统计**：均值、标准差、中位数、P25、P75、最小值、最大值；
3. **切点的分位定位**：例如"高波阈值 0.025 对应训练窗的 P78"；
4. **各 regime 的样本占比**：例如"高波 regime 占训练窗 22%，低波 regime 占 35%，中间 regime 占 43%"；
5. **时间分布**：各 regime 在训练窗内的时间分布是否集中在某一段，还是相对均匀。

记录这些信息的目的是让审计者能够判断：（a）切点是否基于足够的样本估计；（b）切点在经济学上是否有意义；（c）切点是否对训练窗的特殊时期（如 COVID 期间的高波峰值）过度敏感。

---

## 11. Checklist 速查表

执行 Train Calibration 阶段时，依次核对以下清单：

**准备阶段**

- [ ] 上游 signal\_ready 冻结产物已确认存在且哈希一致
- [ ] `time_split.json` 中训练窗定义已读取
- [ ] 训练窗终止日期严格早于测试窗起始日期
- [ ] 训练窗实际可用交易日数量满足 mandate 最低要求

**阈值冻结**

- [ ] 分位阈值已在训练窗内计算并写入 `train_thresholds.json`
- [ ] Regime 切点已在训练窗内估计并写入 `train_thresholds.json`
- [ ] Regime 切点的样本特征已记录（含描述统计和分位定位）
- [ ] 质量过滤条件已定义并写入 `train_thresholds.json`
- [ ] 参数合理区间已定义并写入 `train_thresholds.json`

**参数台账**

- [ ] 信号可研究性过滤已执行，不可研究对象已写入 `train_rejects.csv`
- [ ] 参数粗筛已执行，荒谬区间参数已写入 `train_rejects.csv`
- [ ] `train_param_ledger.csv` 已生成，所有保留配置均有 `pass_reason`
- [ ] `train_rejects.csv` 已生成，所有拒绝配置均有 `reject_reason` 和 `reject_threshold`
- [ ] `search_statistics.json` 已生成，`passed + rejected == total` 校验通过

**产物完整性**

- [ ] `train_quality.parquet` 已生成
- [ ] `artifact_catalog.md` 已撰写，覆盖所有产物
- [ ] `field_dictionary.md` 已撰写，覆盖所有 machine-readable 字段
- [ ] 所有 required\_outputs 文件存在且可解析

**Formal Gate 自审**

- [ ] 所有估计仅来源于训练窗（无 test/backtest 数据泄露）
- [ ] Ledger 和 rejects 同时提交（非单独提交 ledger）
- [ ] 每条记录的理由字段非空
- [ ] Gate 文档 `train_gate_decision.md` 已撰写，含 verdict

**禁止事项确认**

- [ ] 未使用收益最大化或 Sharpe 排名选择最终策略参数
- [ ] 未根据 test/backtest 结果回写 train 阈值
- [ ] 未省略被拒绝参数的搜索轨迹

---

## 12. 关联文档

| 文档 | 路径 | 关系 |
|------|------|------|
| 研究 Workflow 总规范 | `docs/all-sops/第一层-主流程sop/research_workflow_sop.md` | 上位规范 |
| 阶段 Gate Contract | `docs/all-sops/workflow_stage_gates.yaml` | Gate 真值（优先级高于本文档） |
| Signal Ready SOP | `docs/all-sops/第一层-主流程sop/02_signal_ready_sop_cn.md` | 上游阶段 SOP |
| Test Evidence SOP | `docs/all-sops/第一层-主流程sop/04_test_evidence_sop_cn.md` | 下游阶段 SOP |
| Train 失败处理 SOP | `docs/all-sops/第二层-阶段失败 sop/03_train_freeze_failure_sop_cn.md` | 失败与回退流程 |
| 审查 Checklist | `docs/all-sops/第四层-check/review_checklist_master.yaml` | 审查核对表 |

---

> **文档优先级提醒**：当本文档与 `workflow_stage_gates.yaml` 出现表述差异时，以 `workflow_stage_gates.yaml` 为 gate contract 真值。本文档是解释层和操作指南层。
