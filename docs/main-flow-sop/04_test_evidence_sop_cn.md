# 04_test_evidence_sop — Test Evidence 阶段标准操作流程（机构级）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TESTEV-v1.0 |
| 日期 | 2026-03-27 |
| 状态 | Active |
| Owner | Strategy Research / Quant Dev |
| 依赖 | `research_workflow_master_spec`, `workflow_stage_gates.yaml`, `03_train_calibration` |

---

## 1. 文档目的

本文档是 Test Evidence 阶段的唯一正式 SOP。

**核心问题只有一个**：冻结后的信号结构，是否在独立样本里仍然成立。

Test 的职责是**验证结构，不是做收益最大化**。它应该回答"这个机制在新样本里是否继续存在"，而不是"怎么把这一段样本调到最好看"。

本文档不负责解释 train 如何冻结阈值（参见 `03_train_calibration_sop_cn.md`），也不负责 backtest 如何使用白名单（参见 `05_backtest_ready_sop_cn.md`）。它只负责从 train 冻结产物出发，到 test 白名单和候选集交付为止的全部操作规范。

**根本立场**：Test 只验证结构是否在独立样本中延续，不得在测试窗重估 train 阈值，也不允许为了让结果好看而回改上游冻结边界。

---

## 2. 阶段定位

### 2.1 在 Workflow 中的位置

```
data_ready → signal_ready → train_calibration → [test_evidence] → backtest_ready → holdout → shadow
```

Test Evidence 位于 train_calibration 之后、backtest_ready 之前。上游负责把尺子冻结，本阶段负责用独立样本验证这把尺子是否有效，下游负责把验证通过的候选集落地为可交易策略。

### 2.2 与 Train 的分工

| 维度 | Train Calibration | Test Evidence |
|------|-------------------|---------------|
| 数据窗 | 仅训练窗 | 仅测试窗 |
| 职责 | 冻结尺子 | 用冻结尺子验证结构 |
| 产出 | 阈值、切点、参数台账 | 白名单、best_h、frozen_spec |
| 允许做的事 | 定标准、排除荒谬参数 | 对比冻结标准与新样本 |
| 禁止做的事 | 选最终赢家 | 重估 train 阈值 |

### 2.3 统计证据 vs 策略证据

> Test 回答的是"信号结构是否存在"，不是"这个策略是否赚钱"。后者由 Backtest 负责。

把这两件事混在一起，是最常见的证据层次混淆。Test 给出的结论只能是"结构成立/不成立"，不能直接等于"可以上 backtest"。晋级的决定需要同时满足 formal gate 和多重检验校正要求。

---

## 3. 适用范围

本 SOP 适用于：

- 所有正式进入研究管线的系统化研究线，在 train_calibration 通过后进入 test_evidence 阶段；
- 对冻结信号结构的独立样本验证；
- 多重假设检验校正的执行与记录。

不适用于：

- 一次性 notebook 草稿；
- 没有冻结 train 阈值就直接在测试窗分析的场景；
- 探索性试验（不应进入正式 gate 流程）。

---

## 4. 执行步骤

### 4.1 确认上游冻结产物

在开始任何 Test 操作之前，必须确认以下上游冻结产物存在且完整：

- `train_thresholds.json`（含分位阈值、regime 切点、质量过滤条件）；
- `train_param_ledger.csv`（通过粗筛的候选参数配置）；
- `search_statistics.json`（搜索过程统计，供多重检验校正引用）；
- `signal_fields_contract.md`（信号字段定义）；
- `time_split.json`（含测试窗边界）。

**核查方式**：对比上游 gate 文档中记录的文件哈希与本地文件哈希。如不一致，停止操作并退回 train_calibration。

### 4.2 定义测试窗边界

从 `time_split.json` 中读取测试窗起止日期，确认：

1. 测试窗严格晚于训练窗终止日期；
2. 如有 gap（隔离带），记录 gap 长度；
3. 测试窗的实际可用交易日满足最低样本量要求。

**禁止**：在测试窗中混入训练窗的任何数据点。

### 4.3 复用 Train 冻结阈值

按 `train_thresholds.json` 中记录的分位切点、regime 切点和质量过滤条件，对测试窗信号进行分层和过滤。

**要求**：

- 所有阈值直接读取 `train_thresholds.json`，不得在本阶段重算；
- 任何参数的调整（哪怕幅度很小）都属于信息泄露，必须走回退流程；
- 如果发现 train 阈值不适合测试窗，应写入 gate 文档的 residual_risks，不得静默重估。

### 4.4 计算统计证据

在测试窗内，对 `train_param_ledger.csv` 中所有候选参数组计算以下统计量（按研究机制选择适用指标）：

- **IC / 方向命中率**：信号与未来收益的相关性方向是否延续；
- **分层收益**：按 train 分位切点分层后，各层收益是否仍然单调或符合预期；
- **Regime 分层结果**：在各 regime 下，信号方向是否一致；
- **覆盖率与样本量**：确认测试窗内有效样本量充足。

结果保存到 `report_by_h.parquet`（按持有期粒度）和 `symbol_summary.parquet`（按标的汇总）。

### 4.5 生成可准入性报告

对每个 symbol-param 组合，综合以下维度判断是否进入白名单候选：

1. **方向一致性**：测试窗信号方向是否与 train 窗一致；
2. **最低统计阈值**：使用 `train_thresholds.json` 中冻结的质量过滤条件；
3. **覆盖充分性**：测试窗有效样本量满足最低要求。

保存到 `admissibility_report.parquet`，每行至少包含：`symbol`、`param_id`、`admit_status`（admitted/rejected）、`reject_reason`（如适用）。

### 4.6 多重检验校正

**这是本阶段的强制要求。** 参数搜索本质是多重假设检验，不做校正则报告的显著性被严重高估。

从 `search_statistics.json` 中读取 `total_configurations_evaluated`，按以下规则执行：

| 搜索总数 | 要求 |
|----------|------|
| ≥ 20 | 必须生成 `data_mining_adjustment.json`，使用推荐方法之一 |
| < 20 | 在 `test_gate_decision.md` 中显式说明搜索规模足够小、免做校正，但必须记录实际搜索数 |

**推荐校正方法**（选用一种或多种）：

| 方法 | 适用场景 |
|------|----------|
| Deflated Sharpe Ratio（Bailey & López de Prado, 2014） | 从多组回测选最优 Sharpe 后判断是否仍显著 |
| White's Reality Check（2000） | 检验最优策略是否真的优于 benchmark |
| Hansen's SPA test（2005） | Reality Check 的改进版 |

`data_mining_adjustment.json` 至少包含：

```json
{
  "total_configurations_searched": 4800,
  "final_candidates": 12,
  "best_test_sharpe": 1.45,
  "adjustment_method": "deflated_sharpe_ratio",
  "adjusted_significance": "positive (DSR = 0.82)",
  "conclusion": "PASS — 校正后仍显著"
}
```

如果校正后显著性不成立（例如 DSR ≤ 0），最终结论不应为 `PASS`；应评估 `RETRY`、`NO-GO` 或 `CHILD LINEAGE`。

### 4.7 拥挤度与可区分性审计

生成 `crowding_review.md`，记录：

1. **与已知风格/拥挤因子的相关性**：信号与已知 momentum、size、volatility 等常见因子的重叠程度；
2. **策略独特性证据**：去除公共因子暴露后，信号的增量信息是否仍然存在；
3. **结论**：属于 audit evidence，不直接替代 formal gate，但如发现显著风格重叠应在 gate 文档中标注。

### 4.8 冻结白名单与候选集

在通过 formal gate 后，冻结以下产物供下游 Backtest 消费：

- `selected_symbols_test.*`：正式候选 symbol 列表；
- `test_gate_table.csv`：紧凑 gate 总表，每行一个候选，含关键统计指标和 admit 状态；
- `frozen_spec.json`（推荐）：机器可读冻结规范，包含白名单、best_h、使用的阈值版本等。

**原则**：一旦白名单冻结，Backtest 阶段不得回写修改，除非走正式 retry 记账。

### 4.9 自审与 gate 文档

完成上述步骤后执行自审，撰写 `test_gate_decision.md`：

- Formal gate 各条逐项检查结果；
- 多重检验校正结论（或免校正理由）；
- 拥挤度审计发现；
- Verdict（`PASS` / `CONDITIONAL PASS` / `PASS FOR RETRY` / `RETRY` / `NO-GO` / `CHILD LINEAGE`）；
- 如不是 `PASS`，写明需修复的具体事项和允许修改范围。

---

## 5. 必备输出与 Artifact 规范

| 文件 | 格式 | 性质 | 说明 |
|------|------|------|------|
| `report_by_h.parquet` | Parquet | 冻结产物 | 最细粒度测试证据，按持有期分组 |
| `symbol_summary.parquet` | Parquet | 冻结产物 | 按标的汇总的统计摘要 |
| `admissibility_report.parquet` | Parquet | 冻结产物 | 每个 symbol-param 的准入判断与原因 |
| `test_gate_table.csv` | CSV | 冻结产物 | 紧凑 gate 总表 |
| `selected_symbols_test.*` | CSV/JSON | 冻结产物 | 下游 Backtest 允许消费的正式候选集 |
| `crowding_review.md` | Markdown | 人工文档 | 拥挤度与风格重叠审计 |
| `data_mining_adjustment.json` | JSON | 冻结产物 | 多重检验校正报告（搜索≥20时必须） |
| `test_gate_decision.md` | Markdown | 人工文档 | Gate 审计结果与 verdict |
| `artifact_catalog.md` | Markdown | 人工文档 | 本阶段所有产物目录 |
| `field_dictionary.md` | Markdown | 人工文档 | 所有 machine-readable 字段定义 |

---

## 6. Formal Gate 规则

### 6.1 通过条件（pass_all_of，全部满足）

1. 复用了 train 冻结阈值，未在测试窗重估；
2. 正式 gate 与 audit-only gate 已分开记录；
3. 白名单或候选集已冻结并以机器可读格式保存；
4. 多重检验校正已完成（或免校正理由已记录）；
5. `required_outputs` 中全部文件存在，且机器可读产物都有 companion field documentation。

### 6.2 失败条件（fail_any_of，任一触发即失败）

1. **在测试窗重估 train 分位阈值**——直接污染研究线独立性；
2. **看了 backtest 再回写 test 白名单而不做明确 retry 记账**——等同于把 backtest 变成了训练集；
3. **搜索空间 ≥ 20 但没有 `data_mining_adjustment.json`**——无法证明显著性不是搜索噪声；
4. **校正后显著性不成立但仍给 PASS**——结论与证据矛盾。

---

## 7. Audit-Only 检查项

以下检查项不阻断晋级，但须在 `test_gate_decision.md` 中如实记录：

1. **分段一致性**：是否存在信号在测试窗早期成立但后期退化的迹象？
2. **Regime 分层稳定性**：各 regime 下信号方向是否均匀，还是只在某一 regime 下有效？
3. **辅助条件升级潜力**：某个 audit-level 辅助条件是否显示出足够的增量效果，建议在 child lineage 中升级为正式机制？

---

## 8. 常见陷阱与误区

### 8.1 "看了测试结果再调 train 阈值"

最常见的信息泄露路径。哪怕只是把某个分位阈值从 0.33 调到 0.35，只要调整动机来自测试窗的观察，研究线就已经被污染。

**正确做法**：发现 train 阈值不合适时，走回退流程，在 gate 文档中记录 rollback_stage 和 allowed_modifications，下游所有产物重新生成。

### 8.2 "只报告最好的 best_h 而不报告完整分布"

如果只展示 best_h 的结果，审计者无法判断这是真实结构还是在搜索空间中随机挑中的好点。

**正确做法**：`report_by_h.parquet` 必须包含所有评估过的 horizon 或参数组合的完整结果，不只是最优的那个。

### 8.3 "把统计显著和经济显著混为一谈"

p 值 < 0.05 不等于这个策略在合理成本下可盈利。Test 阶段只负责统计结构，经济性由 Backtest 负责。

**正确做法**：`test_gate_decision.md` 中明确写清楚"以下结论属于统计层面，不等于策略层面的可行性"。

### 8.4 "辅助条件在测试窗被升级为正式规则"

在 test 阶段临时新增一个过滤条件（例如"只保留波动率低于某阈值的 symbol"），而这个条件在 train 和 mandate 中没有被正式声明，属于事后追加规则。

**正确做法**：如果确实有价值，应开 child lineage，在新谱系里从 mandate 开始正式声明该条件。

---

## 9. 失败与回退

### 9.1 允许的修改范围

- 修正 test 阶段的实现 bug（时间标签、对齐、计算逻辑）；
- 补充 audit evidence（例如补充拥挤度分析维度）；
- 修改 `data_mining_adjustment.json` 的校正方法选择（不改变候选集）。

修改后必须重新自审并更新 `test_gate_decision.md`。

### 9.2 必须开启 Child Lineage 的情况

- 在测试窗临时新增了正式规则或辅助条件，导致候选集发生变化；
- 需要修改 train 阈值才能让 test 结果变好；
- 发现信号机制本身在测试窗失效，需要修改机制定义。

### 9.3 详细失败处理流程

参阅：[`../第二层-阶段失败 sop/04_test_evidence_failure_sop_cn.md`](../第二层-阶段失败%20sop/04_test_evidence_failure_sop_cn.md)

---

## 10. 阶段专属要求

### 10.1 条件分层与辅助条件层纪律

辅助条件（如波动率分层、流动性过滤）默认作为 test 阶段的 audit evidence：

- **只能使用上游已冻结的辅助字段定义和阈值**，不得在 test 临时重估；
- 静态跨对象效应（符号间差异）与动态时变效应（regime 切换）必须分开审计；
- 只有在 mandate 阶段已正式声明可作为 gate 条件的辅助变量，才可在此升级为 formal rule；
- 未经正式声明的辅助条件若要升级，应开 child lineage。

### 10.2 多重检验校正与 search_statistics 的关系

`Train Calibration` 的 `search_statistics.json` 记录搜索分布（总数、中位数、最优距中位数的距离），是本阶段多重检验校正的**输入**。

`data_mining_adjustment.json` 是**输出**，引用 search_statistics 的数据做正式统计校正。

两者配合：前者是输入，后者是结论。缺少前者，后者无法完成。

---

## 11. Checklist 速查表

**准备阶段**

- [ ] 上游 train 冻结产物已确认存在且哈希一致
- [ ] `time_split.json` 中测试窗定义已读取
- [ ] 测试窗严格晚于训练窗终止日期
- [ ] `search_statistics.json` 已读取，准备供多重检验校正使用

**统计验证**

- [ ] 所有阈值来自 `train_thresholds.json`，未在测试窗重算
- [ ] `report_by_h.parquet` 已生成，包含所有候选的完整结果
- [ ] `symbol_summary.parquet` 已生成
- [ ] `admissibility_report.parquet` 已生成，每条记录有明确准入状态和原因

**多重检验校正**

- [ ] `total_configurations_searched` 已确认
- [ ] 若 ≥ 20 个组合，`data_mining_adjustment.json` 已生成且校正方法已记录
- [ ] 若 < 20 个组合，gate 文档中已显式写明免校正理由和实际搜索数
- [ ] 校正后显著性结论已明确

**候选集冻结**

- [ ] `test_gate_table.csv` 已生成
- [ ] `selected_symbols_test.*` 已生成并冻结
- [ ] `crowding_review.md` 已生成

**产物完整性**

- [ ] `artifact_catalog.md` 已撰写，覆盖所有产物
- [ ] `field_dictionary.md` 已撰写，覆盖所有 machine-readable 字段

**Formal Gate 自审**

- [ ] 未在测试窗重估 train 阈值
- [ ] 正式 gate 与 audit-only gate 已分开记录
- [ ] Gate 文档 `test_gate_decision.md` 已撰写，含 verdict
- [ ] 若校正后显著性不成立，verdict 不是 PASS

**禁止事项确认**

- [ ] 未使用测试窗信息回写 train 阈值
- [ ] 未在 test 临时新增 mandate 中未声明的正式规则
- [ ] 未把审计子集和正式白名单混为一回事

---

## 12. 关联文档

| 文档 | 路径 | 关系 |
|------|------|------|
| 研究 Workflow 总规范 | `docs/all-sops/第一层-主流程sop/research_workflow_sop.md` | 上位规范 |
| 阶段 Gate Contract | `docs/all-sops/workflow_stage_gates.yaml` | Gate 真值（优先级高于本文档） |
| Train Calibration SOP | `docs/all-sops/第一层-主流程sop/03_train_calibration_sop_cn.md` | 上游阶段 SOP |
| Backtest Ready SOP | `docs/all-sops/第一层-主流程sop/05_backtest_ready_sop_cn.md` | 下游阶段 SOP |
| Test Evidence 失败处理 SOP | `docs/all-sops/第二层-阶段失败 sop/04_test_evidence_failure_sop_cn.md` | 失败与回退流程 |
| 审查 Checklist | `docs/all-sops/第四层-check/review_checklist_master.yaml` | 审查核对表 |

---

> **文档优先级提醒**：当本文档与 `workflow_stage_gates.yaml` 出现表述差异时，以 `workflow_stage_gates.yaml` 为 gate contract 真值。本文档是解释层和操作指南层。
