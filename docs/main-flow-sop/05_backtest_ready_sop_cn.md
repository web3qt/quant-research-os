# 05\_backtest\_ready\_sop — Backtest Ready 阶段标准操作流程（机构级）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-BACKTEST-v1.0 |
| 日期 | 2026-03-27 |
| 状态 | Active |
| Owner | Strategy Research / Quant Dev |
| 依赖 | `research_workflow_master_spec`, `workflow_stage_gates.yaml`, `04_test_evidence` |

---

## 1. 文档目的

本文档是 Backtest Ready 阶段的唯一正式 SOP。

**核心问题只有一个**：冻结后的交易规则，在独立 OOS 窗口里能否成立。

Backtest 的职责是**把上游已冻结的信号和候选集映射成正式可交易规则，并验证其经济可行性**。它不是重新发明 alpha，也不是靠回测调参来美化结果。

本文档不负责解释 test_evidence 如何验证信号结构（参见 `04_test_evidence_sop_cn.md`），也不负责 holdout 如何做最终验证（参见 `06_holdout_validation_sop_cn.md`）。它只负责从 test 冻结候选集出发，到 backtest 结论与容量评估交付为止的全部操作规范。

**根本立场**：Backtest 晚于 Test，是为了保持证据层次清晰。如果先做 backtest 再定白名单，那个 backtest 就不再是 OOS，而是在替流程做隐性调参。

---

## 2. 阶段定位

### 2.1 在 Workflow 中的位置

```
test_evidence → [backtest_ready] → holdout_validation → shadow
```

Backtest Ready 位于 test_evidence 之后、holdout 之前。上游已经验证了信号结构，本阶段验证冻结规则在正式资金口径下是否可交易，下游用完全未参与的样本做最终确认。

### 2.2 与 Test 的分工

| 维度 | Test Evidence | Backtest Ready |
|------|---------------|----------------|
| 核心问题 | 信号结构是否成立 | 冻结规则是否可交易 |
| 数据窗 | 测试窗 | 独立回测窗口 |
| 职责 | 验证方向与结构 | 验证成本后经济可行性 |
| 产出 | 白名单、候选集 | 资金曲线、容量评估 |
| 禁止做的事 | 重估 train 阈值 | 重新选币、重估 best_h |

### 2.3 双引擎要求

> 必须完成 `vectorbt` 和 `backtrader` 两套正式回测，不允许只跑单一引擎就宣布 Backtest Ready。

双引擎的目的是通过语义交叉验证，排除单一实现的系统性偏差。如果两套引擎的结论方向不一致，必须在 `engine_compare.csv` 中定位偏差来源，而不是取平均或选较好的那个。

---

## 3. 适用范围

本 SOP 适用于：

- 所有正式进入研究管线、在 test_evidence 通过后进入 backtest_ready 阶段的研究线；
- 需要双引擎（vectorbt + backtrader）验证的正式策略回测；
- 容量评估与异常收益复核。

不适用于：

- 探索性回测（不涉及正式冻结候选集）；
- 单引擎快速验证的临时分析。

---

## 4. 执行步骤

### 4.1 确认上游冻结产物

在开始任何 Backtest 操作之前，必须确认以下上游冻结产物存在且完整：

- `selected_symbols_test.*`（test_evidence 冻结的候选 symbol 列表）；
- `test_gate_table.csv`（含 best_h 或等价候选参数）；
- `frozen_spec.json`（如已生成）；
- `train_thresholds.json`（含 regime 切点、成本相关阈值）；
- `time_split.json`（含回测窗口边界）。

**核查方式**：对比上游 gate 文档中记录的文件哈希。哈希不一致则停止并退回 test_evidence。

### 4.2 定义回测窗口与分层规则

从 `time_split.json` 中读取回测窗口，确认：

1. 回测窗口严格晚于测试窗终止日期；
2. 使用的 symbol 集合来自 `selected_symbols_test.*`，无擅自新增；
3. 使用的 best_h 或持有期参数来自 `test_gate_table.csv`，无擅自修改。

### 4.3 定义交易规则与策略层分级

Backtest 的策略规则搜索必须**按层拆分为有限集合**，禁止混合暴力全搜索：

| 层级 | 内容 | 允许搜索？ |
|------|------|------------|
| execution | 开平仓条件、触发逻辑 | 有限集合 |
| sizing | 仓位规模、名义本金规则 | 有限集合 |
| portfolio | 组合权重、再平衡频率 | 有限集合 |
| risk_overlay | 止损、熔断、强制退出 | 有限集合 |

每层的搜索空间应事先定义并写入对应的 `*_grid.yaml`（参见"建议附加输出"）。

**先定义 baseline，再做 coarse-to-fine 搜索**：不要一开始就把四层规则一起暴力全搜。

### 4.4 验证资金曲线口径

回测必须基于**正式资金记账口径**，至少写清：

- 初始资金；
- 仓位规则或名义本金计算方式；
- 费用模型（手续费、滑点、资金费率）；
- 资金曲线更新方式（逐日更新、逐笔更新）；
- 杠杆/名义本金的处理逻辑。

**禁止**：用 `spread-unit`、`Δs_level` 或任何非资金单位的分数冒充正式回测收益。

### 4.5 运行双引擎回测

分别在 `vectorbt/` 和 `backtrader/` 子目录下完成以下产物：

| 文件 | 说明 |
|------|------|
| `selected_symbols.*` | 本次回测使用的 symbol 集合 |
| `trades.parquet` | 逐笔交易记录 |
| `symbol_metrics.parquet` | 按标的的关键指标汇总 |
| `portfolio_timeseries.parquet` | 组合层面的资金曲线 |
| `portfolio_summary.parquet` | 组合层面的汇总指标 |
| `summary.txt` | 人类可读的简短回测摘要 |

### 4.6 生成多引擎对照

生成 `engine_compare.csv`，对比两套引擎在以下维度的结论：

- 总收益、年化收益、Sharpe ratio；
- 最大回撤；
- 换手率；
- 胜率、盈亏比；
- 是否存在语义差异（`semantic_gap` 字段：true/false）。

如果 `semantic_gap = true`，**必须在 `backtest_gate_decision.md` 中定位偏差来源**，不允许忽略差异直接晋级。

### 4.7 异常高收益强制复核

当出现以下任一情况，**必须触发 `abnormal performance sanity check`**：

- 收益、Sharpe、Calmar 明显超出该策略机制和市场微观结构的常识范围；
- 大部分收益集中在极少数 symbol、极少数交易、极少数日期或极少数 regime；
- 双引擎结果方向一致，但收益高得离谱，而解释仍停留在"结果很好看"。

**触发后必须完成以下检查**：

1. **前视检查**：时间标签、未来收益对齐、白名单冻结、best_h 冻结、阈值冻结是否被破坏；
2. **成本口径检查**：手续费、滑点、资金费率、杠杆/名义本金、强平/爆仓语义是否与正式规则一致；
3. **数据质量检查**：坏 bar、缺失、outlier、stale、极端跳变、成交异常是否放大了收益；
4. **收益集中度拆解**：至少能按 symbol、交易、日期、方向、regime 解释主要收益来源；
5. **多引擎 spot check**：逐笔或逐日验证高收益来自同一批交易语义，而非引擎实现偏差。

**复核未完成前**：

- 不允许写 `PASS`；
- 不允许写 `CONDITIONAL PASS`；
- 不允许进入 Holdout 或 Promotion；
- 阶段状态只能写 `RETRY` 或 `PASS FOR RETRY`。

### 4.8 晋级预算控制

防止 backtest 层搜索过度，导致样本外验证失去意义：

| 层级 | 晋级上限 |
|------|----------|
| 快速筛选层 → 正式 bar 级回测 | `min(5, ceil(候选总数 × 20%))` |
| 正式 bar 级回测 → 压力测试/holdout 准备 | 3 个候选 |
| 最终进入 holdout/shadow 的主方案 | 默认 1 个；主备双轨最多 2 个，须明确 primary/backup |

如有豁免，须在 `backtest_gate_decision.md` 中明确记录。

### 4.9 容量评估

生成 `capacity_review.md`，必须包含以下定量分析：

1. **市场冲击估算**：至少采用一种市场冲击模型（例如 square-root model：$\Delta P / P \propto \sigma \sqrt{Q/V}$）估算不同持仓规模下的执行成本；
2. **AUM-Sharpe 衰减曲线**：给出 `AUM → 净 Sharpe` 的衰减关系，标注 `max_deployable_capital`（净 Sharpe 衰减到可接受下限时的 AUM）；
3. **参与率分析**：按 symbol 给出日均成交量的参与率估算，标注参与率超过阈值（建议 ≤ 5%）的 symbol；
4. **容量瓶颈定位**：写清容量瓶颈是由少数 symbol 的流动性决定，还是由整体组合的换手率决定。

如果微观结构数据不足以支撑定量冲击模型，须显式说明数据限制和估算精度，而不是跳过定量分析。

### 4.10 自审与 gate 文档

撰写 `backtest_gate_decision.md`，内容包括：

- Formal gate 各条逐项检查结果；
- 多引擎对照结论（`semantic_gap` 是否为 false）；
- 异常收益复核结论（是否触发、查了什么、结论是什么）；
- 晋级预算遵守情况；
- 容量评估摘要；
- Verdict（`PASS` / `CONDITIONAL PASS` / `PASS FOR RETRY` / `RETRY` / `NO-GO`）；
- 如不是 `PASS`，写明 rollback_stage 和 allowed_modifications。

---

## 5. 必备输出与 Artifact 规范

| 文件 | 格式 | 性质 | 说明 |
|------|------|------|------|
| `engine_compare.csv` | CSV | 冻结产物 | 双引擎对照，含 semantic_gap 字段 |
| `vectorbt/selected_symbols.*` | CSV/JSON | 冻结产物 | vectorbt 使用的 symbol 集合 |
| `vectorbt/trades.parquet` | Parquet | 冻结产物 | vectorbt 逐笔交易记录 |
| `vectorbt/symbol_metrics.parquet` | Parquet | 冻结产物 | vectorbt 按标的指标汇总 |
| `vectorbt/portfolio_timeseries.parquet` | Parquet | 冻结产物 | vectorbt 资金曲线 |
| `vectorbt/portfolio_summary.parquet` | Parquet | 冻结产物 | vectorbt 组合汇总指标 |
| `vectorbt/summary.txt` | Text | 人工文档 | vectorbt 简短摘要 |
| `backtrader/`（同上） | — | — | backtrader 对应产物 |
| `capacity_review.md` | Markdown | 人工文档 | 容量评估，含定量分析 |
| `backtest_gate_decision.md` | Markdown | 人工文档 | Gate 审计结果与 verdict |
| `artifact_catalog.md` | Markdown | 人工文档 | 本阶段所有产物目录 |
| `field_dictionary.md` | Markdown | 人工文档 | 所有 machine-readable 字段定义 |

### 建议附加输出（搜索了多套策略组合时）

| 文件 | 说明 |
|------|------|
| `execution_grid.yaml` | 开平仓条件搜索空间 |
| `portfolio_grid.yaml` | 组合权重/再平衡规则搜索空间 |
| `risk_overlay_grid.yaml` | 风控层规则搜索空间 |
| `strategy_combo_ledger.csv` | 所有评估过的策略组合及其指标 |
| `selected_strategy_combo.json` | 最终保留的策略组合说明 |

---

## 6. Formal Gate 规则

### 6.1 PASS 条件

- 至少 1 套策略组合通过预设的收益、回撤、换手、容量和风险约束；
- `vectorbt / backtrader` 双引擎均成功且 `semantic_gap = false`；
- 最终保留组合、成本模型、仓位规则和风控规则已冻结；
- 若触发了异常收益复核，复核已完成且未发现阻断性问题；
- 若存在多套候选，晋级预算和 ledger 记录完整且无保留事项。

### 6.2 CONDITIONAL PASS 条件

- 至少 1 套策略组合通过 formal gate，双引擎无语义冲突；
- 仍存在明确保留事项（容量假设待补强、压力测试未完成等）；
- 若触发了异常收益复核，阻断性问题已排除，仅保留非阻断性 reservations；
- 保留事项写入 `backtest_gate_decision.md`。

### 6.3 FAIL 条件（任一触发）

1. 没有任何策略组合通过正式资金口径下的成本后门槛；
2. 双引擎存在语义冲突（`semantic_gap = true`）且未定位原因；
3. 候选组合没有留下完整 ledger / 冻结规则，导致后续阶段无法照单执行；
4. 异常收益复核发现阻断性问题但仍给出 PASS。

---

## 7. Audit-Only 检查项

以下检查项不阻断晋级，但须在 gate 文档中记录：

1. **压力测试覆盖度**：是否覆盖了历史上的极端行情区间（如高波段、流动性危机期）？
2. **风控叠层的独立性**：`risk_overlay` 规则是否与 alpha 机制混合记账？
3. **容量评估的精度**：市场冲击模型是否基于充足的微观结构数据？若数据不足，估算精度如何？
4. **换手率合理性**：实际换手率是否在 mandate 声明的参与率边界内？

---

## 8. 常见陷阱与误区

### 8.1 "在 backtest 里重新选币"

在 backtest 阶段发现某些 symbol 表现很差，于是悄悄把它们从候选集里去掉，而不做正式 retry 记账。

**正确做法**：backtest 使用的 symbol 集合必须来自 `selected_symbols_test.*`。如需修改候选集，必须走回退到 test_evidence 的正式流程，并重新通过 gate。

### 8.2 "用 spread-unit 充当正式收益"

在资金曲线中用价差点数、比例变化或 Δs_level 代替基于实际资金的 P&L，使收益看起来更漂亮。

**正确做法**：收益和 Sharpe 必须基于正式资金曲线口径，初始资金、仓位规则、费用模型必须明确记录。

### 8.3 "风控叠层被包装成 alpha 的一部分"

把停开仓逻辑（如高波动期暂停、交易所熔断期回避）算进信号收益，而不是单独记录为风险管理层。

**正确做法**：`risk_overlay` 和 alpha 必须分开记账，各自贡献的收益在 `strategy_combo_ledger.csv` 中单独列示。

### 8.4 "只做了 backtrader 没做 vectorbt（或反之）"

以为一套引擎的结果已经足够，跳过了第二套引擎。

**正确做法**：双引擎是 formal gate 的强制要求，缺任何一套都不能 PASS。

---

## 9. 失败与回退

### 9.1 失败类型与对应决策

参考 `docs/guides/backtest-fail-sop.md` 的失败治理框架：

| 失败类型 | 描述 | 正式决策 |
|----------|------|----------|
| `ENG_FAIL` | 实现 bug、数据 bug、撮合逻辑错误 | `RETRY`（回退到本阶段内修复） |
| `EXEC_FAIL` | 执行语义、成本或容量问题 | `RETRY`（回退到本阶段内修复） |
| `RESEARCH_FAIL` | test/train 证据层问题 | `RETRY`（rollback_stage 必须回到 03 或 04） |
| `THESIS_FAIL` | 机制不成立或经济性不可接受 | `NO-GO` |
| 研究主问题变化 | 机制、Universe、时间切分发生实质变化 | `CHILD LINEAGE` |

### 9.2 允许的修改范围

- 修正实现 bug（时间标签、撮合逻辑、费用计算）；
- 调整执行参数（如换手率上限、仓位分配权重），但**不允许动 train 冻结尺子**；
- 补充 capacity_review 中的定量分析。

### 9.3 详细失败处理流程

参阅：[`../第二层-阶段失败 sop/05_backtest_failure_sop_cn.md`](../第二层-阶段失败%20sop/05_backtest_failure_sop_cn.md)

---

## 10. 阶段专属要求

### 10.1 双引擎语义对齐检查

双引擎对照的目的不是"两套结果一样就行"，而是**通过语义对齐验证实现的正确性**。

具体要求：

1. 两套引擎使用**完全相同的 symbol 集合、时间窗、持有期、开平仓条件和费用模型**；
2. 如两套引擎的 Sharpe 差异超过 0.3（或团队预设阈值），必须定位原因；
3. 允许的合理差异来源：引擎内部的撮合时序差异、报价价格使用差异；
4. 不允许的差异来源：不同的 symbol 集合、不同的持有期、不同的费用假设。

### 10.2 容量定量化的最低要求

`capacity_review.md` 不能只有定性判断。若市场微观结构数据不足，须在文档中显式说明：

- 缺失的数据类型（如逐笔成交量、委托薄深度）；
- 基于现有数据的估算方法和精度；
- 容量结论的置信区间（定性描述）。

即使有数据限制，也必须提供某种量化估算，而不是完全省略。

---

## 11. Checklist 速查表

**准备阶段**

- [ ] 上游 test_evidence 冻结产物已确认存在且哈希一致
- [ ] `selected_symbols_test.*` 已读取，symbol 集合已确认
- [ ] `time_split.json` 中回测窗口已读取
- [ ] 回测窗口严格晚于测试窗终止日期

**策略规则定义**

- [ ] execution / sizing / portfolio / risk_overlay 四层规则已分开定义
- [ ] 若做了多套组合搜索，对应的 `*_grid.yaml` 已生成
- [ ] 资金曲线口径已明确（初始资金、仓位规则、费用模型、更新方式）

**双引擎回测**

- [ ] vectorbt 回测已完成，所有必备子产物已生成
- [ ] backtrader 回测已完成，所有必备子产物已生成
- [ ] `engine_compare.csv` 已生成，`semantic_gap` 字段已填写
- [ ] 若 `semantic_gap = true`，差异原因已定位并记录

**异常收益复核**

- [ ] 是否触发 `abnormal performance sanity check`？已在 gate 文档中明确记录
- [ ] 若触发，前视/成本/数据质量/收益集中度/多引擎 spot check 均已完成
- [ ] 复核结论已写入 `backtest_gate_decision.md`

**晋级预算**

- [ ] 晋级预算控制已遵守，或有明确豁免记录
- [ ] 若有多套候选，primary/backup 已明确标注

**容量评估**

- [ ] `capacity_review.md` 已生成
- [ ] 市场冲击估算已完成（或数据限制已说明）
- [ ] AUM-Sharpe 衰减曲线已提供
- [ ] 参与率分析已完成
- [ ] 容量瓶颈已定位

**产物完整性**

- [ ] `artifact_catalog.md` 已撰写，覆盖所有产物
- [ ] `field_dictionary.md` 已撰写，覆盖所有 machine-readable 字段

**Formal Gate 自审**

- [ ] 未在 backtest 重新选币或重估 best_h
- [ ] 未根据 backtest 结果回改 train 冻结尺子
- [ ] Gate 文档 `backtest_gate_decision.md` 已撰写，含 verdict

---

## 12. 关联文档

| 文档 | 路径 | 关系 |
|------|------|------|
| 研究 Workflow 总规范 | `docs/all-sops/第一层-主流程sop/research_workflow_sop.md` | 上位规范 |
| 阶段 Gate Contract | `docs/all-sops/workflow_stage_gates.yaml` | Gate 真值（优先级高于本文档） |
| Test Evidence SOP | `docs/all-sops/第一层-主流程sop/04_test_evidence_sop_cn.md` | 上游阶段 SOP |
| Holdout Validation SOP | `docs/all-sops/第一层-主流程sop/06_holdout_validation_sop_cn.md` | 下游阶段 SOP |
| Backtest 失败处理 SOP | `docs/all-sops/第二层-阶段失败 sop/05_backtest_failure_sop_cn.md` | 失败与回退流程 |
| Backtest 失败治理指南 | `docs/guides/backtest-fail-sop.md` | 失败分类与决策树 |

---

> **文档优先级提醒**：当本文档与 `workflow_stage_gates.yaml` 出现表述差异时，以 `workflow_stage_gates.yaml` 为 gate contract 真值。本文档是解释层和操作指南层。
