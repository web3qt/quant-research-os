# 06_holdout_validation_sop — Holdout Validation 阶段标准操作流程（机构级）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-HOLDOUT-v1.0 |
| 日期 | 2026-03-27 |
| 状态 | Active |
| Owner | Strategy Research / Quant Dev |
| 依赖 | `research_workflow_master_spec`, `workflow_stage_gates.yaml`, `05_backtest_ready` |

---

## 1. 文档目的

本文档是 Holdout Validation 阶段的唯一正式 SOP。

**核心问题只有一个**：最终冻结方案在最后一段完全未参与设计的窗口里，是否仍然没有翻向。

Holdout 的价值在于**它没有参与前面的任何定义、筛选和冻结**。一旦用它来调参，它就失去了"最终验证"的意义，整条研究线的证据独立性就已经被破坏。

本文档不负责解释 backtest 如何验证经济可行性（参见 `05_backtest_ready_sop_cn.md`），也不负责 promotion_decision 如何给出组织级结论（参见 `07_promotion_decision_sop_cn.md`）。它只负责从 backtest 冻结方案出发，到 holdout 验证结论与相关报告交付为止的全部操作规范。

**根本立场**：Holdout 必须保留到最后。它不是"多一段样本的回测"，而是整条研究线最后一道独立的事后验证。任何参数修改都必须发生在 holdout 之前，而不是之后。

---

## 2. 阶段定位

### 2.1 在 Workflow 中的位置

```
backtest_ready → [holdout_validation] → promotion_decision → shadow
```

Holdout Validation 是研究阶段的最后一道验证关卡。上游已经完成了双引擎回测和容量评估，本阶段用完全独立的样本做最终确认，下游做组织级晋级决策。

### 2.2 Holdout 与 Backtest 的区别

| 维度 | Backtest Ready | Holdout Validation |
|------|----------------|--------------------|
| 数据窗 | 独立回测窗口 | 最后一段从未参与任何阶段的窗口 |
| 允许调参 | 允许在正式流程内定义执行规则 | 完全不允许，冻结方案照单执行 |
| 目的 | 验证经济可行性、评估容量 | 确认方向未翻转、无重大结构漂移 |
| 失败后操作 | 允许 retry 并修复执行层 | 只能 NO-GO、RETRY（回退至上游）或 CHILD LINEAGE |

---

## 3. 适用范围

本 SOP 适用于：

- 所有在 backtest_ready 通过后进入 holdout_validation 阶段的研究线；
- 需要对最终冻结方案做独立最终验证的场景；
- 滚动 OOS 一致性检查、regime 平稳性审计和跨阶段性能退化追踪。

不适用于：

- 探索性回测；
- 使用 holdout 窗口调参数的任何场景（此类操作直接违反本阶段纪律）。

---

## 4. 执行步骤

### 4.1 确认上游冻结产物

在开始任何 Holdout 操作之前，必须确认以下上游冻结产物存在且完整：

- `backtest_gate_decision.md`（backtest 通过记录）；
- `engine_compare.csv`（双引擎一致性已验证）；
- `frozen_spec.json` 或等价的冻结交易规则说明；
- `selected_symbols_test.*`（白名单，来自 test_evidence）；
- `time_split.json`（含 holdout 窗口边界）。

**核查方式**：对比上游 gate 文档中记录的文件哈希。哈希不一致则停止并退回 backtest_ready。

### 4.2 确认冻结方案照单执行

在 holdout 中，**所有参数、规则、symbol 集合、阈值都必须严格来自 backtest 的冻结产物**：

1. Symbol 集合：完全来自 `selected_symbols_test.*`，不新增、不删除；
2. 持有期/best_h：来自 `test_gate_table.csv`，不修改；
3. 交易规则：来自 `frozen_spec.json` 或等价冻结文件，不修改；
4. 成本模型：与 backtest 保持一致；
5. 风控规则：与 backtest 保持一致。

**任何不一致都意味着 holdout 的独立性已被破坏**，须在 gate 文档中明确标注并说明原因。

### 4.3 运行 Holdout 回测

按 `time_split.json` 中的 holdout 窗口边界，运行回测并生成每个窗口下的：

- `portfolio_summary.parquet`（组合汇总指标）；
- `trades.parquet`（逐笔交易记录）；
- 其他与 backtest 对应的结果文件。

同时生成 `holdout_backtest_compare.csv`，对比 holdout 与 backtest 的核心指标：

| 指标 | Backtest 值 | Holdout 值 | 变化幅度 |
|------|-------------|------------|----------|
| 年化收益 | - | - | - |
| Sharpe | - | - | - |
| 最大回撤 | - | - | - |
| 胜率 | - | - | - |

### 4.4 滚动 OOS 一致性检查

单一 holdout 窗口的统计检验力有限。必须对 holdout 窗口做子窗口分析：

1. 将 holdout 窗口切成 3-5 个**非重叠**子窗口（按持有期周期或自然时间）；
2. 分别计算每个子窗口的核心指标（Sharpe、命中率、盈亏比）；
3. 要求**多数子窗口（≥ 60%）方向一致**（如正收益），而不只是合并窗口结果好看；
4. 如子窗口不足 3 个（holdout 太短），须在 gate 文档中显式说明样本不足。

生成 `rolling_oos_consistency.json`，至少包含：

```json
{
  "holdout_window": {"start": "2025-01-01", "end": "2025-12-31"},
  "sub_windows": [
    {"start": "2025-01-01", "end": "2025-03-31", "sharpe": 0.82, "win_rate": 0.54},
    {"start": "2025-04-01", "end": "2025-06-30", "sharpe": 1.21, "win_rate": 0.57},
    {"start": "2025-07-01", "end": "2025-09-30", "sharpe": 0.65, "win_rate": 0.52},
    {"start": "2025-10-01", "end": "2025-12-31", "sharpe": -0.31, "win_rate": 0.46}
  ],
  "consistent_direction_ratio": 0.75,
  "conclusion": "moderate"
}
```

**Formal gate 要求**：如果 `consistent_direction_ratio < 0.6` 但合并窗口 Sharpe > 0，gate 文档必须显式讨论为什么合并结果与分段结果不一致，不能直接写 `PASS`。

### 4.5 Regime 平稳性审计

Holdout 窗口的 regime 分布可能与训练窗显著不同，这可能导致结果退化，但不一定意味着策略失效。必须对 regime 偏移做显式审计。

生成 `regime_stationarity_audit.json`，至少包含：

```json
{
  "train_regime_distribution": {"low_vol": 0.60, "high_vol": 0.40},
  "test_regime_distribution": {"low_vol": 0.55, "high_vol": 0.45},
  "holdout_regime_distribution": {"low_vol": 0.30, "high_vol": 0.70},
  "max_regime_shift": 0.30,
  "regime_shift_significant": true,
  "interpretation": "holdout 窗口高波动 regime 占比比训练窗高出 30pp，结果退化需与 regime 不匹配区分讨论"
}
```

**Audit-only（非独立 formal gate）**：如果 `regime_shift_significant = true` 且 gate 文档没有讨论其影响，holdout 阶段的 gate 结论可信度会被降级。

### 4.5.1 结构突变与关系连续性审计

如果 holdout 阶段的 verdict 依赖“结构仍连续”或“结果退化只是 regime 不匹配而非机制断裂”的判断，必须在 `holdout_gate_decision.md` 中说明结构突变检验口径，或明确写出免做理由。

至少要回答三件事：

1. **你要证明哪种连续性**：是系数方向、lead-lag 关系、threshold 机制，还是某个核心 beta/残差关系没有断裂；
2. **当前采用的 structural-break protocol 是什么**：若断点事先已知，可用 `Chow`；若断点未知或可能有多个，可用 `Bai-Perron`；若更关注持续漂移，可补充 `CUSUM / CUSUMSQ` 或 `rolling / expanding coefficient stability`；
3. **如果检出了 break，如何解释**：先区分 regime 组成变化、样本太短、实现偏差与机制断裂；只有在核心结构崩塌且缺乏合理解释时，才应进一步走向 `NO-GO` 或 `CHILD LINEAGE`。

原则上，**significant break 不是自动失败条件**；但如果 reviewer 想用“只是 regime 变了”来支撑 formal `PASS` 或 `CONDITIONAL PASS`，就必须有对应 protocol 或免做理由。

### 4.6 跨阶段性能退化追踪

从 train → test → backtest → holdout 的性能退化率本身是重要的审计指标。

生成 `performance_decay_summary.json`，至少包含：

```json
{
  "metric_name": "annualized_sharpe",
  "train_value": 2.10,
  "test_value": 1.65,
  "backtest_value": 1.38,
  "holdout_value": 0.92,
  "total_decay_rate": 0.56,
  "decay_flag": "high_decay"
}
```

**Audit-only**：如果 `decay_flag = high_decay`（总退化率 > 50%），gate 文档应讨论可能原因（过拟合、regime 不匹配、样本量不足），但不自动触发 `FAIL`。

### 4.7 解释无交易或低触发场景

如果 holdout 窗口内出现：

- 触发次数明显少于 backtest；
- 某些 symbol 完全没有触发；
- 持续的空仓期。

须在 gate 文档中明确说明：这是正常的信号稀疏现象、还是策略机制出现了结构性失效？如果是后者，应给出 `RETRY` 或 `NO-GO` 结论。

### 4.8 自审与 gate 文档

撰写 `holdout_gate_decision.md`，内容包括：

- Formal gate 各条逐项检查结果；
- 滚动 OOS 一致性结论；
- Regime 平稳性审计发现（如有显著偏移，说明对结论的影响）；
- 若 verdict 依赖结构连续性或 regime mismatch 解释，写明结构突变检验 protocol 或免做理由；
- 跨阶段性能退化评估；
- Verdict（`PASS` / `CONDITIONAL PASS` / `RETRY` / `NO-GO` / `CHILD LINEAGE`）；
- 如不是 `PASS`，写明 rollback_stage 和 allowed_modifications。

---

## 5. 必备输出与 Artifact 规范

| 文件 | 格式 | 性质 | 说明 |
|------|------|------|------|
| `holdout_run_manifest.json` | JSON | 冻结产物 | 本次 holdout 运行的完整元信息 |
| `holdout_backtest_compare.csv` | CSV | 冻结产物 | Holdout 与 backtest 的核心指标对比 |
| `portfolio_summary.parquet` | Parquet | 冻结产物 | 每个 holdout 窗口的组合汇总 |
| `trades.parquet` | Parquet | 冻结产物 | 逐笔交易记录 |
| `rolling_oos_consistency.json` | JSON | 冻结产物 | 滚动 OOS 子窗口一致性报告 |
| `regime_stationarity_audit.json` | JSON | 冻结产物 | Regime 平稳性审计报告 |
| `performance_decay_summary.json` | JSON | 冻结产物 | 跨阶段性能退化摘要 |
| `holdout_gate_decision.md` | Markdown | 人工文档 | Gate 审计结果与 verdict |
| `artifact_catalog.md` | Markdown | 人工文档 | 本阶段所有产物目录 |
| `field_dictionary.md` | Markdown | 人工文档 | 所有 machine-readable 字段定义 |

---

## 6. Formal Gate 规则

### 6.1 通过条件（pass_all_of，全部满足）

1. 使用的交易规则与 backtest 冻结方案完全一致，未做任何修改；
2. 合并窗口 holdout 方向未翻转（Sharpe > 0 或等价主指标满足最低要求）；
3. 滚动 OOS 一致性检查已完成（`rolling_oos_consistency.json` 存在且 `conclusion` 已填写）；
4. Regime 平稳性审计已完成；
5. 若 verdict 依赖“结构仍连续”或“结果退化只是 regime 不匹配而非机制断裂”的判断，已记录结构突变检验 protocol 或免做理由；
6. 跨阶段性能退化已记录；
7. `required_outputs` 中全部文件存在，且 machine-readable 产物都有 companion field documentation。

### 6.2 失败条件（fail_any_of，任一触发即失败）

1. **holdout 期间修改了任何交易规则、symbol 集合或阈值**——holdout 独立性立即丧失；
2. **滚动 OOS 一致性 < 0.6 且 gate 文档未讨论不一致原因**——合并窗口结论不可信；
3. **合并窗口方向翻转且无合理解释**（非 regime 不匹配等外部因素）——策略机制在 holdout 不成立；
4. **把“只是 regime 变了”或“关系仍连续”作为 holdout 通过依据，却没有说明结构突变检验 protocol 或免做理由**——连续性解释缺少审计边界；
5. **把 holdout 直接并入前面的 test 或 backtest 当作更多样本**——破坏整个证据独立性架构。

---

## 7. Audit-Only 检查项

以下检查项不阻断晋级，但须在 gate 文档中记录：

1. **Regime 不匹配下的结论可信度**：如果 holdout 的 regime 分布与 train 差异显著，结论的泛化性如何？
2. **结构突变与参数稳定性**：如果结论依赖关系连续性，是否补充了 `Chow` / `Bai-Perron` / `CUSUM` / rolling coefficient stability 等证据，并解释 break 更像 regime mismatch 还是机制断裂？
3. **低触发场景的解释**：稀疏触发是正常稀疏还是策略机制失效？
4. **性能退化的可接受性**：`total_decay_rate > 50%` 时，退化是否在可预期范围内？
5. **子窗口不足的说明**：如 holdout 太短导致子窗口不足 3 个，holdout 检验力不足应在 reservations 中注明。

---

## 8. 常见陷阱与误区

### 8.1 "holdout 结果不好看，改一下 symbol 白名单"

这是最严重的 holdout 污染。一旦用 holdout 结果来指导白名单修改，holdout 就变成了第三个训练集。

**正确做法**：holdout 期间发现 symbol 表现差，只能记录在 gate 文档的 audit-only 发现中，不得修改白名单。如需修改，必须走回退流程并开 child lineage。

### 8.2 "只看合并窗口 Sharpe，不做子窗口分析"

合并窗口 Sharpe 可能被极少数表现很好的交易拉高，而大多数子窗口实际上是负的。

**正确做法**：必须完成滚动 OOS 一致性检查，`consistent_direction_ratio ≥ 0.6` 才是稳定信号。

### 8.3 "regime 变了，结果退化，直接归因于策略失效"

Holdout 窗口的 regime 分布可能与训练窗差异显著，这种情况下的结果退化需要分开讨论：是策略机制本身不成立，还是 regime 不匹配导致的暂时退化？

**正确做法**：先完成 `regime_stationarity_audit.json`，再根据 regime 偏移情况分开讨论原因。

### 8.4 "把 holdout 窗口并入 backtest 以获得更多样本"

研究员认为 holdout 样本量太少，希望把它和 backtest 合并来增加统计检验力。

**正确做法**：这是明确禁止的操作。holdout 的价值在于完全独立，一旦并入 backtest 就不再是最终验证。

---

## 9. 失败与回退

### 9.1 允许的动作

| 场景 | 允许动作 | 注意 |
|------|----------|------|
| Holdout 方向未翻转但性能显著退化 | `CONDITIONAL PASS` + 在 reservations 中记录 | 退化须有解释 |
| 发现实现 bug（非策略问题） | `RETRY`，修复后重新运行 holdout | 不允许修改策略规则 |
| 信号结构在 holdout 不成立 | `NO-GO` 或开 `CHILD LINEAGE` | 不允许回调 train/test 阈值 |
| Regime 不匹配导致退化，机制本身可能仍有效 | `CHILD LINEAGE`，在新谱系中针对该 regime 做专项研究 | 当前主线保持不变 |

### 9.2 明确禁止的操作

- 用 holdout 调任何参数；
- 因 holdout 不好看就改 symbol 白名单；
- 重新定义研究问题来"解释" holdout 结果；
- 把 holdout 直接并入前面的样本。

### 9.3 详细失败处理流程

参阅：[`../fail-sop/06_holdout_failure_sop_cn.md`](../第二层-阶段失败%20sop/06_holdout_failure_sop_cn.md)

---

## 10. 阶段专属要求

### 10.1 `consistent_direction_ratio` 解读指南

| 值域 | 解读 | gate 建议 |
|------|------|-----------|
| ≥ 0.80 | 强一致性，各子窗口方向高度一致 | 可 PASS，有力支撑晋级 |
| 0.60 – 0.80 | 中等一致性，多数窗口方向一致 | 可 CONDITIONAL PASS，在 reservations 中注明 |
| < 0.60 | 弱一致性或不一致，多个子窗口方向相反 | 不可直接 PASS，须在 gate 文档中显式讨论 |

注意：`consistent_direction_ratio` 本身不是唯一决策标准，须结合合并窗口结果、regime 分布和退化原因综合判断。

### 10.2 跨阶段退化率的参考区间

退化率是审计工具，不是硬性 gate。以下区间供参考：

| 退化率 | 描述 | 建议 |
|--------|------|------|
| < 30% | 正常退化 | 无需额外说明 |
| 30% – 50% | 中等退化 | 在 reservations 中注明，说明原因 |
| > 50% | 高退化（`high_decay`） | 必须在 gate 文档中讨论原因（过拟合、regime 不匹配等） |

即使退化率 > 50%，如果能清楚归因（例如 holdout 覆盖了极端市场条件而 train 没有），gate 仍可以给出有保留的 PASS。

---

## 11. Checklist 速查表

**准备阶段**

- [ ] 上游 backtest_ready 冻结产物已确认存在且哈希一致
- [ ] `frozen_spec.json` 已读取，冻结方案已确认
- [ ] `time_split.json` 中 holdout 窗口已读取
- [ ] 确认所有交易规则将照单执行，无任何参数修改

**Holdout 运行**

- [ ] Holdout 回测已完成，`portfolio_summary.parquet` 和 `trades.parquet` 已生成
- [ ] `holdout_backtest_compare.csv` 已生成，与 backtest 的指标对比已完成
- [ ] `holdout_run_manifest.json` 已生成

**滚动 OOS 一致性**

- [ ] Holdout 窗口已切分为 3-5 个非重叠子窗口（或已说明样本不足原因）
- [ ] 每个子窗口的核心指标已计算
- [ ] `rolling_oos_consistency.json` 已生成
- [ ] `consistent_direction_ratio` 已计算，结论已记录

**Regime 平稳性审计**

- [ ] `regime_stationarity_audit.json` 已生成
- [ ] Train/test/holdout 窗口的 regime 分布已对比
- [ ] `regime_shift_significant` 已填写
- [ ] 如有显著偏移，对结论的影响已在 gate 文档中讨论

**结构突变与连续性审计**

- [ ] 若 verdict 依赖“结构仍连续”或“只是 regime 不匹配而非机制断裂”的判断，结构突变检验 protocol 或免做理由已写入 `holdout_gate_decision.md`
- [ ] 若做了 `Chow` / `Bai-Perron` / `CUSUM` / rolling coefficient stability 等审计，结果已解释为 regime 变化、样本问题或机制断裂中的哪一种

**跨阶段退化追踪**

- [ ] `performance_decay_summary.json` 已生成
- [ ] Train/test/backtest/holdout 的指标值均已填写
- [ ] `total_decay_rate` 已计算
- [ ] 若 `decay_flag = high_decay`，退化原因已在 gate 文档中讨论

**产物完整性**

- [ ] `artifact_catalog.md` 已撰写，覆盖所有产物
- [ ] `field_dictionary.md` 已撰写，覆盖所有 machine-readable 字段

**Formal Gate 自审**

- [ ] 未在 holdout 期间修改任何规则或白名单
- [ ] Gate 文档 `holdout_gate_decision.md` 已撰写，含 verdict
- [ ] 若 verdict 依赖结构连续性或 regime mismatch 解释，相关 structural-break 口径已明确写出

**禁止事项确认**

- [ ] 未用 holdout 结果调参
- [ ] 未因 holdout 不好看而修改白名单
- [ ] 未把 holdout 并入 test 或 backtest 样本

---

## 12. 关联文档

| 文档 | 路径 | 关系 |
|------|------|------|
| 研究 Workflow 总规范 | `docs/main-flow-sop/research_workflow_sop.md` | 上位规范 |
| 阶段 Gate Contract | `contracts/stages/workflow_stage_gates.yaml` | Gate 真值（优先级高于本文档） |
| Backtest Ready SOP | `docs/main-flow-sop/05_backtest_ready_sop_cn.md` | 上游阶段 SOP |
| Promotion Decision SOP | `docs/main-flow-sop/07_promotion_decision_sop_cn.md` | 下游阶段 SOP |
| Holdout 失败处理 SOP | `docs/fail-sop/06_holdout_failure_sop_cn.md` | 失败与回退流程 |

---

> **文档优先级提醒**：当本文档与 `workflow_stage_gates.yaml` 出现表述差异时，以 `workflow_stage_gates.yaml` 为 gate contract 真值。本文档是解释层和操作指南层。
