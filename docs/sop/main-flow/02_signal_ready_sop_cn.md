# 02_signal_ready_sop

Doc ID: SOP-SIGNALREADY-v1.0
Title: `02_signal_ready_sop` — Signal Ready 阶段标准操作流程（机构级）
Date: 2026-03-27
Timezone: Asia/Tokyo
Status: Active
Owner: Strategy Research / Quant Dev
Audience:
- Research
- Quant Dev
- Reviewer / Referee
Depends On:
- `research_workflow_master_spec`
- `workflow_stage_gates.yaml`
- `00_mandate`
- `01_data_ready`

---

# 1. 文档目的

本 SOP 只回答一件事：

**当一个 research lineage 进入 `02_signal_ready` 阶段时，团队应当如何把 `00_mandate` 已冻结的信号表达式模板，实例化成统一 schema、统一 param_id 身份、统一时间语义的正式信号字段合同，并完成 gate 审查。**

它不是策略说明书，不是收益报告，不是信号机制发明手册。
它是 `02_signal_ready` 的**正式物化合同与操作流程**。

---

# 2. 阶段定位

## 2.1 核心问题

> 研究对象是否已经被定义成统一、可复现、可比较的信号字段合同。

`02_signal_ready` 在整个 workflow 中夹在 `01_data_ready`（数据可研究）和 `03_train_calibration`（训练冻结）之间。它回答的不是"信号是否有效"，而是：

- 后续 Train 和 Test 到底在消费哪个字段？
- 每个字段对应哪个 param_id？
- 每个 param_id 的时间语义是什么？
- 信号层产物是否可以被安全消费、可以被独立复现？

## 2.2 为什么不能直接从 Data Ready 跳到 Train

没有独立信号层，团队容易在不同阶段对同一信号用不同计算方式或时间标签：

- Train 用的 `ResidualZ` 和 Test 用的 `ResidualZ` 可能窗口不同。
- 不同研究员各自实现同一个表达式，出现隐性分歧。
- 调参和定义纠缠在一起，最终无法区分"机制不行"还是"定义混乱"。
- 没有字段合同，下游消费者无法验证自己拿到的字段是不是原研究问题对应的字段。

`02_signal_ready` 的存在，就是为了在 Data 和 Train 之间建立一道不可跳过的字段身份与 schema 冻结关卡。

## 2.3 与 Mandate 的边界

Signal Ready **不是**重新发明信号机制，而是把 Mandate 已冻结的表达式模板正式实例化。具体地：

- 把参数维度编码成稳定 `param_id`。
- 把表达式模板落成固定 schema。
- 物化 baseline 或 search batch 的正式信号时序。
- 写清本阶段实例化了哪些参数组和字段。

如果本阶段需要改变信号机制模板本身（而不仅仅是实例化），则必须回退到 Mandate 或开新谱系。

---

# 3. 适用范围

本 SOP 适用于所有需要在 `02_signal_ready` 正式物化信号字段的研究线，包括但不限于：

- 方向 / 结构类字段，如 `DC_up`、`DC_down`、`DownLinkGap`
- 截面 / 排名 / 状态类字段
- `ResidualZ`、`OB/OS`、`OBRate/OSRate`、`kappa`
- 质量门禁字段，如 `low_sample`、`missing_rate_window`、`pair_missing`
- 任何下游 `03_train_calibration` 会正式消费的信号字段、状态字段、质量字段、审计字段

只要研究线需要回答以下问题，本 SOP 就适用：

- 信号表达式是否严格按 Mandate 冻结模板物化？
- param_id 身份是否清晰、可溯源、可被下游稳定消费？
- 时间语义和未来收益对齐方式是否已冻结？
- 覆盖报告和质量门禁是否足以保护下游 Train / Test / Backtest？

---

# 4. 执行步骤

## 4.1 确认上游冻结产物

本阶段启动前，必须确认以下上游产物已冻结且可消费：

| 上游阶段 | 必须存在的冻结产物 | 用途 |
|---|---|---|
| `00_mandate` | mandate 冻结文档、表达式模板、参数维度声明、Universe 定义 | 信号机制定义来源 |
| `01_data_ready` | `aligned_bars/`、`rolling_stats/`、data gate 文档 | 底表与统计基础层 |

**检查清单**：

1. `00_mandate` 的 gate 结论是 `PASS` 或 `CONDITIONAL PASS`。
2. `01_data_ready` 的 gate 结论是 `PASS` 或 `CONDITIONAL PASS`。
3. 已冻结的 signal expression template 存在且版本号可追溯。
4. Universe 口径与 data_ready 一致。
5. 时间窗定义与 mandate 一致。

如果上游任一必备产物缺失或 gate 未通过，本阶段不得启动。

## 4.2 编码 param_id 体系

`param_id` 是 Signal Ready 的身份基石。每一组参数实例化必须对应唯一、稳定的 `param_id`。

**编码规则**：

1. `param_id` 必须由参数维度的组合唯一确定。
2. 不得仅靠文件名或目录名推断 `param_id`——必须有显式的 `param_manifest.csv` 记录。
3. `param_id` 一旦进入 `param_manifest.csv`，在本谱系后续阶段不可变更。
4. 如果搜索批次分多轮物化，每轮新增的 `param_id` 必须追加到 manifest，不可覆盖已有条目。

**`param_manifest.csv` 最小必备字段**：

```csv
param_id,expression_template,param_dim_1,param_dim_2,...,scope,batch_tag,materialized_at,status
```

- `param_id`：唯一标识。
- `expression_template`：来源表达式模板名称或版本号。
- `param_dim_*`：各参数维度值。
- `scope`：`baseline` | `search_batch` | 其他声明值。
- `batch_tag`：物化批次标签。
- `materialized_at`：物化完成时间戳。
- `status`：`ok` | `failed` | `skipped`。

## 4.3 实例化表达式模板为固定 schema

将 Mandate 冻结的表达式模板转换为本阶段正式的信号计算实现：

1. 确认表达式模板版本与 Mandate 冻结版本一致。
2. 将模板中的参数占位符替换为 `param_id` 对应的具体值。
3. 固定输出 schema：字段名、字段类型、字段单位、字段语义、允许缺失值、主时间标签。
4. 确认主时间标签 (`anchor_timestamp`) 与未来收益对齐方式 (`forward_return_alignment`) 已冻结。

**schema 冻结后不可变更**。如需变更字段名或字段语义，必须回退到本阶段重新过 gate。

## 4.4 物化 baseline 信号时序

Baseline 是本阶段最核心的产出：

1. 按 `param_manifest.csv` 中 `scope=baseline` 的 param_id 列表逐一物化。
2. 输出到 `params/{param_id}/` 目录。
3. 每个 param_id 目录下包含完整的 timeseries 文件和元数据。
4. 物化完成后，检查：
   - 无 NaN / Inf 泄漏到下游应消费的字段。
   - 时序长度与 data_ready 对齐。
   - 主时间标签连续性。
   - 覆盖 symbol 数与 Universe 一致。

**baseline 物化不允许部分完成后声称 PASS**。`param_manifest.csv` 中 `scope=baseline` 且 `status=failed` 的条目数必须为零。

## 4.5 物化 search_batch 信号时序（如适用）

如果 Mandate 声明了参数搜索空间：

1. 按 `param_manifest.csv` 中 `scope=search_batch` 的 param_id 列表逐批物化。
2. 不要求一次物化完整参数空间。
3. **但必须**把已物化的 `param_id` 集合写进 `param_manifest.csv`。
4. Train 阶段只能消费 Signal Ready 已物化的 `param_id`——不允许 Train 临时扩充未物化的 param_id。
5. 每批物化完成后更新 `signal_coverage.csv`。

未物化的 `param_id` 不得标记为 `ok`；如果因资源限制跳过，标记为 `skipped` 并注明原因。

## 4.6 生成覆盖报告和 symbol_summary

物化完成后，必须生成以下覆盖报告：

### signal_coverage.csv

```csv
param_id,symbol,bar_count,nan_count,inf_count,coverage_ratio,low_sample_flag,pair_missing_flag,status
```

### signal_coverage.md / signal_coverage_summary.md

人类可读的覆盖摘要，至少包含：

- 总 param_id 数、已物化数、失败数、跳过数。
- 按 symbol 维度的覆盖率统计。
- 按 param_id 维度的覆盖率统计。
- 质量告警汇总（low_sample、pair_missing、finite_residual_z_ratio 异常等）。

### symbol_summary.parquet（如适用）

按 symbol 粒度聚合的信号摘要，供下游快速引用。

## 4.7 执行最小质量保留项检查

以下质量指标为 **audit-only**，不构成 formal gate 阻断条件，但必须记录并留档：

| 质量指标 | 阈值 | 含义 |
|---|---|---|
| `finite_residual_z_ratio` | < 0.01 | 非有限值（NaN/Inf）占比过高 |
| `low_sample_rate` | > 0.98 | 低样本标记占比过高 |
| `pair_missing_rate` | > 0.70 | pair 缺失率过高 |

如果上述指标异常但不阻断 gate，必须在 `signal_gate_decision.md` 中以 `reservations` 记录，并说明对下游可能的影响。

search batch 中出现非阻断性稀疏参数组，同样记录为 audit-only finding。

## 4.8 生成 signal_fields_contract

`signal_fields_contract.md` 是本阶段最重要的人类可读合同文档之一。

**必备内容**：

1. **字段清单表**：列出本阶段产出的全部信号字段、状态字段、质量字段、审计字段。
2. **字段定义**：每个字段的名称、类型、单位、语义、允许范围、缺失处理。
3. **字段来源**：每个字段对应的表达式模板版本和 param_id 范围。
4. **时间语义**：主时间标签定义、forward return 对齐方式、滞后约定。
5. **消费合同**：下游 `03_train_calibration` 可消费的字段列表和约束条件。
6. **冻结声明**：本合同冻结后，未经 gate 重审不可变更。

**字段清单表示例**：

```markdown
| 字段名 | 类型 | 单位 | 语义 | 来源模板 | 允许 NaN | 下游消费者 |
|---|---|---|---|---|---|---|
| ResidualZ | float64 | z-score | 残差标准化得分 | expr_template_v2 | 否 | train, test |
| DC_up | bool | — | Donchian 上破 | expr_template_v2 | 否 | train, test |
| low_sample | bool | — | 低样本标记 | quality_gate | 是 | train, test, audit |
```

## 4.9 生成 param_manifest

确认 `param_manifest.csv` 已完整更新：

1. 所有 baseline param_id 状态已标注（`ok` / `failed` / `skipped`）。
2. 所有 search_batch param_id 状态已标注。
3. 无孤立 param_id（即存在于文件系统但不在 manifest 中的参数目录）。
4. 无幽灵 param_id（即存在于 manifest 但文件系统中无对应产物）。

验证命令示例：

```bash
# 检查文件系统 param_id 与 manifest 的一致性
diff <(ls params/ | sort) <(cut -d',' -f1 param_manifest.csv | tail -n+2 | sort)
```

## 4.10 生成 artifact_catalog 和 field_dictionary

### artifact_catalog.md

列出本阶段所有关键产物：

```markdown
| Artifact | 路径 | 粒度 | 主键 | 机器可读 | 消费者 |
|---|---|---|---|---|---|
| param_manifest.csv | ./param_manifest.csv | param_id | param_id | 是 | train, gate |
| signal_coverage.csv | ./signal_coverage.csv | param_id × symbol | (param_id, symbol) | 是 | gate, audit |
| signal_fields_contract.md | ./signal_fields_contract.md | — | — | 否 | train, reviewer |
| params/ | ./params/{param_id}/ | bar | (timestamp, symbol) | 是 | train |
```

### field_dictionary.md

对本阶段产出的每一个机器可读 artifact 中的每一个字段进行定义。至少包含：

- 字段名、数据类型、单位、允许范围、缺失语义、计算逻辑或来源。

`artifact_catalog.md` 和 `field_dictionary.md` 是 `workflow_stage_gates.yaml` 的 `required_outputs`，不可跳过。

## 4.11 自审与 gate 文档

### signal_contract.md

对本阶段的信号合同做整体描述，至少包含：

- 信号机制摘要（引用 Mandate 冻结的表达式模板，不重新定义）。
- 本阶段实例化的 scope（baseline / search_batch）。
- 已冻结的 schema 版本号。
- 下游可消费边界。

### signal_gate_decision.md

Gate 文档是本阶段的正式结论。结构如下：

```markdown
# Signal Ready Gate Decision

## Verdict: [PASS | CONDITIONAL PASS | PASS FOR RETRY | RETRY | CHILD LINEAGE]

## Formal Gate Checklist
- [ ] 已显式物化 baseline 或 declared search_batch 的全部 param_id
- [ ] param_id 身份清晰且有 param_manifest
- [ ] 正式 timeseries schema、参数元数据和时间语义已冻结
- [ ] signal gate 文档已生成
- [ ] required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation

## Audit-Only Findings
- finite_residual_z_ratio: [值]
- low_sample_rate: [值]
- pair_missing_rate: [值]
- [其他 audit-only 发现]

## Reservations (如适用)
- [具体保留意见]

## Rollback Stage: signal_ready
## Downstream Permissions: may_advance_to train_calibration
```

Gate 文档写完后，Reviewer 才有依据给出最终 verdict。

---

# 5. 必备输出与 Artifact 规范

| # | Artifact | 类型 | 是否 formal gate 必备 | 说明 |
|---|---|---|---|---|
| 1 | `param_manifest.csv` | machine | 是 | 全部 param_id 身份与状态台账 |
| 2 | `params/` | machine | 是 | 各 param_id 的正式信号时序目录 |
| 3 | `signal_coverage.csv` | machine | 是 | 覆盖率与质量摘要（机器可读） |
| 4 | `signal_coverage.md` | human | 是 | 覆盖率人类可读报告 |
| 5 | `signal_coverage_summary.md` | human | 是 | 覆盖率高层摘要 |
| 6 | `signal_contract.md` | human | 是 | 信号合同整体描述 |
| 7 | `signal_fields_contract.md` | human | 是 | 字段合同（最重要的下游消费合同） |
| 8 | `signal_gate_decision.md` | human | 是 | Gate 决策文档 |
| 9 | `artifact_catalog.md` | human | 是 | 本阶段产物清单 |
| 10 | `field_dictionary.md` | human | 是 | 字段字典 |

**machine artifact 必须有 companion field documentation**。缺少 companion docs 的 machine artifact 等同于未产出。

---

# 6. Formal Gate 规则

## 6.1 判定矩阵

| Verdict | 条件 |
|---|---|
| **PASS** | `formal_gate.pass_all_of` 全部满足；failed symbols = 0；failed params = 0；skipped params = 0 |
| **CONDITIONAL PASS** | baseline 或 required scope 已完整可用；存在明确 reservations（例如 skipped params、退化参数组或覆盖率告警） |
| **PASS FOR RETRY** | required artifacts 基本齐全，但物化范围或 gate 文档需要当前阶段受控补跑 |
| **RETRY** | `formal_gate.fail_any_of` 被触发，且问题仍属于实现或落盘缺陷 |
| **CHILD LINEAGE** | 想改变主信号机制定义；想新增 mandate 未允许的参数维度 |

## 6.2 formal_gate.pass_all_of

以下条件必须**全部满足**才能给出 `PASS`：

1. 已显式物化 baseline 或 declared search_batch 的全部 param_id。
2. param_id 身份清晰且有 param_manifest。
3. 正式 timeseries schema、参数元数据和时间语义已冻结。
4. signal gate 文档已生成。
5. `required_outputs` 全部存在，且 machine-readable artifact 都有 companion field documentation。

## 6.3 formal_gate.fail_any_of

以下条件触发**任意一条**即 FAIL：

1. baseline 或 required param_id 物化失败。
2. failed symbols 或 failed params 大于零。
3. 下游才发现 signal contract 缺失或字段越层。
4. 在 Train 阶段才首次引入未曾在 Signal Ready 物化过的 param_id。

---

# 7. Audit-Only 检查项

以下项目不构成 formal gate 的阻断条件，但必须检查并记录到 `signal_gate_decision.md`：

| 检查项 | 说明 |
|---|---|
| `finite_residual_z_ratio` | 非有限值占比（NaN / Inf）。audit 阈值 < 0.01。 |
| `low_sample_rate` | 低样本标记占比。audit 阈值 > 0.98。 |
| `pair_missing_rate` | pair 缺失率。audit 阈值 > 0.70。 |
| 稀疏参数组 | search batch 中物化成功但覆盖率显著低于 baseline 的参数组。 |
| 覆盖率分布偏斜 | 部分 symbol 覆盖率显著低于整体均值。 |
| 退化参数 | 物化成功但信号值方差极低或常量化的 param_id。 |

Audit-only 发现不可偷换成 formal gate 条件。Reviewer 应在 gate 文档中单独列出 audit-only findings 并标注其对下游的潜在影响。

---

# 8. 常见陷阱与误区

## 8.1 在 Train 里边算边改信号定义

**禁止**。Signal Ready 冻结的字段合同就是 Train 的输入合同。Train 不得修改信号的计算方式、字段含义或时间语义。如果 Train 发现信号定义需要调整，必须回退到 Signal Ready。

## 8.2 不记录参数身份，只靠文件名猜

**禁止**。文件名不是 param_id 的正式来源。`param_manifest.csv` 是唯一的 param_id 台账。靠 `params/h24_w60/` 之类的目录名猜测参数含义，在团队协作和自动化审计中会导致严重歧义。

## 8.3 在 Train 临时扩充未物化的 param_id

**禁止**。Train 只能消费 Signal Ready 已物化并记录在 `param_manifest.csv` 中的 param_id。如果需要扩充参数空间，必须回退到 Signal Ready 追加物化。

## 8.4 把信号可用性问题留给 Test 发现

**禁止**。信号覆盖不足、字段缺失、schema 不一致等问题，必须在 Signal Ready 阶段发现并处理。如果 Test 阶段才发现 signal contract 缺失或字段越层，本阶段的 gate 将被追溯判定为 FAIL。

## 8.5 混淆信号层与交易层

Signal Ready 只负责字段物化和 schema 冻结。白名单、阈值、入场/出场规则、仓位分配不属于本阶段产物。不要在 signal_fields_contract 中嵌入交易逻辑。

## 8.6 把 audit-only 发现当成 FAIL 理由

Audit-only 检查项的异常不构成 formal gate 阻断。Reviewer 不得因为 `low_sample_rate` 超标就直接判 FAIL——应记录为 reservation 并评估对下游的影响。

## 8.7 跳过 companion field documentation

Machine artifact 没有 companion docs 等同于未产出。`param_manifest.csv` 必须有 `field_dictionary.md` 解释每一列的含义。`signal_coverage.csv` 同理。

---

# 9. 失败与回退

当本阶段 gate 结论不是 `PASS` 或 `CONDITIONAL PASS` 时，进入失败处置流程。

**详细失败处置标准请参阅**：[`02_signal_ready_failure_sop_cn.md`](../failures/02_signal_ready_failure_sop_cn.md)

## 9.1 回退规则摘要

| 场景 | 回退目标 | 说明 |
|---|---|---|
| 信号实现 bug | `signal_ready` | 在本阶段修正，重新过 gate |
| 字段命名错误 | `signal_ready` | 在本阶段修正，重新过 gate |
| 标签对齐错误 | `signal_ready` | 在本阶段修正，重新过 gate |
| companion docs 不全 | `signal_ready` | 在本阶段补全，重新过 gate |
| 改变信号机制模板 | `mandate` 或开 child lineage | 不允许在本阶段原地修改 |
| 改变字段分层边界 | `mandate` 或开 child lineage | 不允许在本阶段原地修改 |
| 新增 mandate 未声明的参数维度 | 开 child lineage | 不允许在原谱系继续 |

## 9.2 允许的修正

在本阶段回退时，以下修改不需要开 child lineage：

- signal 实现（bug fix、效率优化）
- 字段命名（修正拼写、统一命名风格）
- 标签对齐（修正时间对齐方式）
- companion docs（补全 artifact_catalog、field_dictionary）

## 9.3 必须开 child lineage 的修改

以下修改必须开新谱系或回退到 Mandate：

- 改变信号机制模板（例如从 Z-score 改为 rank-based）
- 改变字段分层边界（例如把 Train 才应处理的逻辑下移到信号层）

---

# 10. 阶段专属要求

## 10.1 param_id 体系详解

### 设计原则

`param_id` 是 Signal Ready 中参数身份管理的核心，贯穿后续所有阶段。

1. **唯一性**：同一谱系中不允许出现两个 param_id 指向不同参数组合。
2. **不可变性**：param_id 一旦写入 `param_manifest.csv` 并被下游消费，不可更改其对应的参数值。
3. **可溯源性**：每个 param_id 必须能追溯到 Mandate 声明的表达式模板和参数维度。
4. **机器可消费性**：param_id 的格式必须支持自动化流水线（无空格、无特殊字符、无歧义缩写）。

### 推荐编码格式

```
{expression_short}_{dim1}_{dim2}_..._{dimN}
```

示例：`rz_h24_w60`、`dc_h4_w20_gap5`。

### 常见错误

- 用自增数字编码（`param_001`, `param_002`）——丢失参数语义。
- 用文件路径做 param_id——换目录就失效。
- 同一 param_id 在不同批次指向不同参数值——身份污染。

## 10.2 最小质量保留项

最小质量保留项是 audit-only 级别的检查，用于在不阻断 gate 的前提下记录信号质量风险。

| 指标 | 含义 | audit 阈值 | 超阈值时的建议动作 |
|---|---|---|---|
| `finite_residual_z_ratio` | 非有限值占全部值的比率 | < 0.01 | 检查数据源与计算逻辑 |
| `low_sample_rate` | 被标记为低样本的记录占比 | > 0.98 | 检查 Universe 覆盖与数据可用性 |
| `pair_missing_rate` | pair 缺失占比 | > 0.70 | 检查 pair 匹配逻辑与数据完整性 |

这些指标的异常**不阻断 gate**，但如果 Reviewer 评估后认为会实质性影响下游证据质量，应在 verdict 中记为 reservation。

## 10.3 与 Mandate 的边界（详细）

| 属于 Mandate 的职责 | 属于 Signal Ready 的职责 |
|---|---|
| 定义信号机制的假设和理论依据 | 把假设落成具体的计算代码 |
| 声明允许的参数维度和搜索空间 | 编码 param_id 并物化时序 |
| 冻结表达式模板的数学定义 | 实例化模板为固定 schema |
| 声明 Universe 和时间窗 | 在 Universe 和时间窗内生成覆盖报告 |
| 声明研究问题边界 | 验证物化产物仍在研究问题边界内 |

**关键判断标准**：如果修改只涉及"怎么算"（实现层），留在 Signal Ready；如果修改涉及"算什么"（定义层），必须回退 Mandate。

---

# 11. Checklist 速查表

以下 checklist 供执行者在提交 gate 审查前自查：

```
[ ] 上游冻结产物
    [ ] mandate gate = PASS / CONDITIONAL PASS
    [ ] data_ready gate = PASS / CONDITIONAL PASS
    [ ] signal expression template 版本已确认

[ ] param_id 体系
    [ ] param_manifest.csv 已生成
    [ ] 所有 baseline param_id 状态 = ok
    [ ] 所有 search_batch param_id 状态已标注
    [ ] 文件系统与 manifest 一致（无孤立 / 无幽灵）

[ ] 信号物化
    [ ] baseline 时序已完整物化
    [ ] schema 已冻结（字段名、类型、时间语义）
    [ ] 主时间标签与 forward return 对齐方式已冻结
    [ ] 无 NaN / Inf 泄漏到下游应消费字段

[ ] 覆盖报告
    [ ] signal_coverage.csv 已生成
    [ ] signal_coverage.md 已生成
    [ ] signal_coverage_summary.md 已生成

[ ] 质量检查
    [ ] finite_residual_z_ratio 已计算并记录
    [ ] low_sample_rate 已计算并记录
    [ ] pair_missing_rate 已计算并记录

[ ] 字段合同
    [ ] signal_fields_contract.md 已生成
    [ ] 字段清单表完整
    [ ] 时间语义已声明
    [ ] 消费合同已声明

[ ] 文档
    [ ] signal_contract.md 已生成
    [ ] signal_gate_decision.md 已生成
    [ ] artifact_catalog.md 已生成
    [ ] field_dictionary.md 已生成

[ ] 禁止项自查
    [ ] 未在信号层嵌入交易逻辑
    [ ] 未新增 mandate 未声明的参数维度
    [ ] 未使用未来函数或未来冻结对象
    [ ] 未跳过 companion field documentation
```

---

# 12. 关联文档

| 文档 | 路径 | 关系 |
|---|---|---|
| 研究 Workflow 总指南 | `docs/sop/main-flow/research_workflow_sop.md` | 上层规范 |
| 阶段 Gate Contract | `contracts/stages/workflow_stage_gates.yaml` | Gate 真值 |
| Mandate SOP | `docs/sop/main-flow/00_mandate_sop_cn.md`（如适用） | 上游阶段 |
| Data Ready SOP | `docs/sop/main-flow/01_data_ready_sop_cn.md`（如适用） | 上游阶段 |
| Signal Ready 失败处置 SOP | `docs/sop/failures/02_signal_ready_failure_sop_cn.md` | 失败处置 |
| Train Calibration SOP | `docs/sop/main-flow/03_train_calibration_sop_cn.md`（如适用） | 下游阶段 |

---

*本文档与 `contracts/stages/workflow_stage_gates.yaml` 存在表述差异时，以该 YAML 为准。*
