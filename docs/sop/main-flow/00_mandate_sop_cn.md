# 00_mandate_sop

Doc ID: SOP-MANDATE-v1.0
Title: `00_mandate_sop` — Mandate 阶段标准操作流程（机构级）
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

---

# 1. 文档目的

本 SOP 只回答一件事：

**Mandate 阶段应该如何执行、交什么 artifact、怎么判 gate。**

它不是主流程 SOP 的替代品，也不是某条具体研究线的专题说明。它是 Mandate 阶段的**标准执行合同**

与周边文档的关系：

| 文档 | 角色 | 本 SOP 如何使用 |
|------|------|-----------------|
| `research_workflow_sop.md` | 全流程解释层 | 本 SOP 是其 §4.1 的执行展开 |
| `workflow_stage_gates.yaml` | Gate contract 真值 | 本 SOP 的 gate 规则必须与 YAML 一致；如有冲突，以 YAML 为准 |
| `docs/sop/failures/` | 各阶段失败处置 | Mandate 失败后的回退纪律参考该层（注：专属 mandate failure SOP 尚未建立） |
| `docs/sop/review/` | 审查模板 | 提供 Mandate gate 审查的具体检查模板 |

---

# 2. 阶段定位

## 2.1 核心问题

> **这条研究线到底研究什么，不研究什么。**

Mandate 不是在回答"能不能赚钱"或"数据够不够"。它回答的是更上游的问题：**后续一切证据的解释边界从哪里来。**

## 2.2 为什么必须独立存在

Mandate 是全流程里最容易被低估、也最关键的阶段。它的价值不是"写一份说明"，而是**冻结后续一切证据的解释边界**。

没有它，团队无法分辨：

- 哪些修改属于实现修复（允许）；
- 哪些修改已经改变了研究问题（必须回退或开子谱系）。

一旦研究问题没冻结就开始看数据和扫参数，所有后续阶段的显著性和收益结论都无法被信任——因为无法排除"先看结果、再补问题"的可能性。

## 2.3 上游输入合同

Mandate 的前置阶段是 `idea_intake`。进入 Mandate 的必要条件：

- `idea_gate_decision.yaml.verdict == GO_TO_MANDATE`；
- 已通过 `run_research_session.py --confirm-mandate` 完成四组交互式确认（`research_intent` / `scope_contract` / `data_contract` / `execution_contract`）。

Mandate 消费的 Idea Intake 输出：

| Intake Artifact | Mandate 使用方式 |
|-----------------|-----------------|
| `qualification_scorecard.yaml` | 提取 approved dimensions 作为研究问题边界参考 |
| `research_question_set.md` | 作为 `mandate.md` 研究主问题的起草基础 |
| `scope_canvas.yaml` | 作为 universe 与时间窗提案的初始输入 |
| `idea_gate_decision.yaml` | 提取 `approved_scope` 作为 Mandate 边界约束 |

除上述 Intake 产物外，Mandate 还可接收：

- 候选 universe 与时间边界提案（补充说明）；
- 字段族、公式模板、实现栈和并行计划提案。

## 2.4 下游消费者

| 下游阶段 | 消费内容 |
|----------|----------|
| `01_data_ready` | `time_split.json`, `parameter_grid.yaml`, `run_config.toml`, `field_dictionary.md`, `research_scope.md` |
| `02_signal_ready` | mandate frozen outputs（表达式模板、参数边界、字段分层） |
| `03_train_freeze` | `time_split.json`, `parameter_grid.yaml` |
| 全流程各阶段 | `mandate.md` 作为研究问题冻结的真值文档 |

---

# 3. 适用范围

## 3.1 适用于

所有需要进入正式研究管线的系统化研究，包括但不限于：

- 信号研究；
- 因子筛选与白名单研究；
- Pair / spread / relative value 研究；
- 事件研究；
- 多因子 / 截面研究；
- 回测晋级研究；
- 任何需要先冻结研究路线，再按路线分流后续 stage contract 的研究线；
- 任何需要 holdout 或 shadow 验证的研究线。

## 3.2 不适用于

- 一次性 notebook 草稿；
- 临时灵感验证；
- 没有冻结研究问题的探索性试验；
- 只为"看一眼分布"的临时分析。

如果一个研究主题处于上述探索阶段，它不需要走 Mandate；但一旦决定正式推进，必须先完成 Mandate 冻结。

---

# 4. 执行步骤

Mandate 阶段至少要冻结以下内容。每一步以"输入 → 动作 → 输出 → 验证点"四要素展开。

## 步骤 1：定义研究主问题与不研究项

- **输入**：研究主题说明或专题草稿。
- **动作**：
  1. 用一到三句话写清楚本研究线的主问题（what we study）。
  2. 显式列出不研究什么（what we do NOT study）。
  3. 写清楚研究的预期贡献：它回答什么问题，不回答什么问题。
- **输出**：`mandate.md` 中的"研究主问题"和"明确排除项"段落。
- **验证点**：
  - 主问题是否可以在不看任何结果的情况下被理解？
  - 排除项是否足够具体，能阻止后续偷换？

## 步骤 1.5：冻结研究路线与排除路线

- **输入**：`idea_intake` 输出的 `route_assessment`。
- **动作**：
  1. 从 `candidate_routes` 中确认最终 `research_route`。
  2. 明确写出 `excluded_routes`，禁止只写推荐路线不写排除项。
  3. 对 `cross_sectional_factor` 进一步冻结 `factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy`。
  4. 解释为什么当前问题属于这条 route，而不是另一条。
  5. 写明 `route_change_policy`：在下游冻结前如何回退，在下游冻结后如何开子谱系。
- **输出**：`mandate.md` 中的"研究路线与排除路线"段落；`research_route.yaml`。
- **验证点**：
  - `research_route` 是否唯一？
  - `excluded_routes` 是否非空？
  - `cross_sectional_factor` 的 `factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是否都已明确？
  - 路线说明是否足以让 reviewer 判断为什么不是另一类问题？

### 1.5.1 cross_sectional_factor 路线附加冻结

当 `research_route = cross_sectional_factor` 时，`mandate` 必须额外冻结下列研究身份字段：

- `factor_role`：`standalone_alpha` / `regime_filter` / `combo_filter`
- `factor_structure`：`single_factor` / `multi_factor_score`
- `portfolio_expression`：
  - `standalone_alpha`：`long_short_market_neutral` / `long_only_rank` / `short_only_rank` / `benchmark_relative_long_only` / `group_relative_long_short`
  - `regime_filter`：`target_strategy_filter`
  - `combo_filter`：`target_strategy_filter` / `target_strategy_overlay`
- `neutralization_policy`：`none` / `market_beta_neutral` / `group_neutral`

上述四项是 `mandate` 冻结的身份字段，不是后续阶段可以重新定义的可调参数。
当且仅当这些身份字段在 `mandate` 中被冻结后，CSF 路线才允许进入独立的 `01_csf_data_ready` → `06_csf_holdout_validation` 流程。

附加必需引用：

- 若 `factor_role != standalone_alpha`，必须同时冻结 `target_strategy_reference`，用来说明该 CSF 作为筛选器或组合过滤器服务哪个主策略/目标组合
- 若 `neutralization_policy = group_neutral`，必须同时冻结 `group_taxonomy_reference`，用来说明组别口径来自哪一版 taxonomy
- 若上述引用缺失，则该 CSF 线路不算身份冻结完成，后续 review 不得将其视为可继续推进的正式研究线

同时必须明确说明：

- `standalone_alpha` 进入独立 `01_csf_data_ready` → `06_csf_holdout_validation` 流程，主证据是横截面排序能力
- `regime_filter` / `combo_filter` 也进入同一条 CSF 流程，但 `04_csf_test_evidence` 的证据语义改为对目标策略或组合的条件改善
- 一旦 `mandate` 冻结后，CSF 路线不得再回退成旧的时序 `signal_ready / train / test / backtest` 主线

若上述字段任一缺失，`cross_sectional_factor` 的 mandate 不得 formal pass。

## 步骤 2：冻结时间窗与切分方式

- **输入**：候选时间边界提案。
- **动作**：
  1. 确定正式研究的总时间窗（start date ~ end date）。
  2. 定义 train / test / backtest / holdout / shadow 的切分方式。
  3. 确定时间标签（time label）的语义：bar close 定义、对齐频率、session 边界。
  4. 写清楚无前视约定（no-lookahead convention）：哪些字段可以在 t 时刻使用、哪些不可以。
- **输出**：`time_split.json`（机器可读）；`mandate.md` 中的时间窗描述段落。
- **验证点**：
  - `time_split.json` 是否覆盖 train / test / backtest / holdout 四段？
  - 时间标签语义是否明确（bar close 定义、TZ、session）？
  - 无前视约定是否能被代码验证？

## 步骤 3：冻结 Universe 与准入口径

- **输入**：候选 universe 提案。
- **动作**：
  1. 定义正式 universe（symbol list / pair list / asset class scope）。
  2. 定义准入口径：什么 symbol 可以进入研究，什么不可以。
  3. 写清楚退市、停牌、低流动性的处理约定。
  4. 写清楚 universe 变更条件：什么情况下必须开子谱系。
- **输出**：`research_scope.md` 中的 universe 段落；`mandate.md` 中的准入约定。
- **验证点**：
  - Universe 是否是一个显式列表或显式规则，而不是"大概这些"？
  - 准入口径是否可以被代码判断？

## 步骤 4：定义字段分层与字段字典

- **输入**：字段族提案、已有数据源的字段清单。
- **动作**：
  1. 按研究语义对字段进行分层（例如：raw data fields / derived fields / signal fields / label fields）。
  2. 对每个字段写清楚：字段名、类型、单位、计算公式或来源、时间语义、是否允许前视。
  3. 对研究中用到的每一个符号（symbol in formulas），写清楚它对应哪个字段、什么含义、什么时间语义。
- **输出**：`field_dictionary.md`（人类可读的字段字典）；配套的 `*_fields.md` 文件。
- **验证点**：
  - 是否存在只有裸字段名但没有解释的字段？
  - 字段分层是否清楚到下游可以判断"哪些字段属于哪一层"？
  - 公式中的符号是否都能追溯到字段字典？

## 步骤 5：冻结信号机制与表达式模板

- **输入**：公式模板提案、信号机制描述。
- **动作**：
  1. 定义允许使用的信号机制族（例如：mean reversion / momentum / event-driven）。
  2. 写出带参数的表达式模板（expression template），用占位符标记可调参数。
  3. 写清楚禁止使用的信号机制或字段组合。
  4. 对每个表达式模板，写清楚：符号说明、研究含义（为什么这个公式有意义）、时间语义（公式输入在 t 时刻是否已知）。
- **输出**：`mandate.md` 或 `research_scope.md` 中的信号机制段落；表达式模板文档。
- **验证点**：
  - 每个表达式模板是否都有符号说明和时间语义？
  - 禁止事项是否足够具体，能被代码或 reviewer 验证？

## 步骤 6：编写参数字典与参数网格

- **输入**：信号机制表达式模板、研究主问题。
- **动作**：
  1. 对表达式模板中的每个可调参数，定义：参数名、类型、允许范围、默认值、步长或枚举值。
  2. 生成参数网格文件，列出首轮需要扫描的参数组合。
  3. 写清楚参数边界的研究依据（为什么这个范围合理）。
- **输出**：`parameter_grid.yaml`（机器可读参数网格）；`mandate.md` 中的参数边界段落。
- **验证点**：
  - 是否存在只有参数名但没有类型、范围和解释的参数？
  - 参数网格是否与表达式模板中的占位符一一对应？

## 步骤 7：冻结容量与拥挤审计口径

- **输入**：研究主问题、universe 定义。
- **动作**：
  1. 定义后续 crowding / capacity 审计的比较基准（benchmark）。
  2. 定义流动性代理变量（liquidity proxy）与参与率边界（participation rate threshold）。
  3. 写清楚容量审计的口径，使后续阶段的 crowding 分析有统一标准。
- **输出**：`mandate.md` 或 `research_scope.md` 中的容量审计段落。
- **验证点**：
  - 比较基准是否明确（哪个 benchmark、什么时间段）？
  - 流动性代理与参与率边界是否可以被代码消费？

## 步骤 8：确定实现栈与并行规划划

- **输入**：研究规模估算、团队资源。
- **动作**：
  1. 确定实现栈（主语言、框架、计算平台）。
  2. 写清楚并行计划（parallelization plan）：哪些计算可以并行、需要多少资源。
  3. 如果有非 Rust 实现的例外，显式列出 `non_rust_exceptions` 及其理由。
- **输出**：`run_config.toml`（机器可读运行配置）；`mandate.md` 中的实现栈段落。
- **验证点**：
  - `run_config.toml` 是否覆盖了并行计划和资源需求？
  - 非标准实现是否有理由？

## 步骤 9：生成 artifact_catalog 和 field_dictionary

- **输入**：步骤 1-8 的所有输出。
- **动作**：
  1. 汇总所有已生成的 artifact，登记到 `artifact_catalog.md`。
  2. 检查 `field_dictionary.md` 是否覆盖所有已使用字段。
  3. 确认每个机器可读产物都有对应的 companion field documentation。
- **输出**：`artifact_catalog.md`（完整 artifact 登记）；`field_dictionary.md`（完整字段字典）。
- **验证点**：
  - `artifact_catalog.md` 是否列出了所有 required_outputs？
  - 是否有字段在代码或公式中被使用，但未出现在 `field_dictionary.md` 中？

## 步骤 10：完成自审与 gate 文档

- **输入**：步骤 1-9 的所有输出。
- **动作**：
  1. 对照第 6 节 Formal Gate 规则逐条自审。
  2. 对照第 11 节 Checklist 逐项勾选。
  3. 标注未覆盖项及其处理计划。
  4. 准备 gate 文档提交 reviewer。
- **输出**：自审记录、gate 文档。
- **验证点**：
  - `pass_all_of` 是否全部满足？
  - `fail_any_of` 是否全部不触发？

---

# 5. 必备输出与 Artifact 规范

## 5.1 Artifact 总览

| Artifact | 类型 | 用途 |
|----------|------|------|
| `mandate.md` | 人类可读 | 研究主问题、冻结边界、排除项、参数边界的主文档 |
| `research_scope.md` | 人类可读 | Universe、准入口径、字段分层、容量审计口径 |
| `time_split.json` | 机器可读 | 正式时间窗定义与切分 |
| `parameter_grid.yaml` | 机器可读 | 首轮参数网格 |
| `run_config.toml` | 机器可读 | 实现栈、并行计划、运行配置 |
| `research_route.yaml` | 机器可读 | mandate 冻结的研究路线真值 |
| `artifact_catalog.md` | 人类可读 | 所有产物的登记清单 |
| `field_dictionary.md` | 人类可读 | 全字段字典，覆盖所有公式、信号、标签字段 |

## 5.2 机器可读 Artifact Schema 示例

### time_split.json

```json
{
  "version": "1.0",
  "timezone": "UTC",
  "bar_close_definition": "period end timestamp, inclusive",
  "no_lookahead_convention": "field value at t must be known at or before bar close of t",
  "splits": {
    "train": {
      "start": "2020-01-01",
      "end": "2022-12-31"
    },
    "test": {
      "start": "2023-01-01",
      "end": "2023-06-30"
    },
    "backtest": {
      "start": "2023-07-01",
      "end": "2024-06-30"
    },
    "holdout": {
      "start": "2024-07-01",
      "end": "2025-06-30"
    }
  }
}
```

### parameter_grid.yaml

```yaml
version: "1.0"
expression_template: "signal = f(x, lookback, threshold)"
parameters:
  lookback:
    type: int
    min: 5
    max: 60
    step: 5
    unit: bars
    rationale: "覆盖短期到中期的均值回复窗口"
  threshold:
    type: float
    min: 0.5
    max: 3.0
    step: 0.25
    unit: sigma
    rationale: "标准差倍数作为触发门槛"
grid_mode: cartesian
total_combinations: 132
```

### run_config.toml

```toml
[implementation]
primary_language = "rust"
framework = "polars"
non_rust_exceptions = ["visualization: python/plotly"]

[parallelization]
strategy = "symbol-level"
max_workers = 16
chunk_size = 50

[resources]
estimated_memory_gb = 32
estimated_runtime_hours = 4.0

[versioning]
config_version = "1.0"
mandate_hash = "abc123"
```

### research_route.yaml

```yaml
research_route: cross_sectional_factor
excluded_routes:
  - time_series_signal
route_rationale:
  - "问题本质是横截面排序，而不是单资产时间序列预测"
  - "下游证据应该优先看 Rank IC 和分组收益"
route_change_policy:
  before_downstream_freeze: rollback_to_mandate
  after_downstream_freeze: child_lineage
route_contract_version: v1
```

## 5.3 Companion Field Documentation 制度

每个机器可读 artifact 必须有对应的 companion field doc。要求：

- `time_split.json` 的 companion doc 在 `mandate.md` 的时间窗段落。
- `parameter_grid.yaml` 的 companion doc 在 `mandate.md` 的参数边界段落。
- `run_config.toml` 的 companion doc 在 `mandate.md` 的实现栈段落。
- 任何新增字段必须同步更新 `field_dictionary.md`。

规则：**没有 companion doc 的机器可读产物，不算完成。**

---

# 6. Formal Gate 规则

## 6.1 通过条件（pass_all_of）

以下条件**全部满足**方可通过：

| # | 条件 | 对应步骤 |
|---|------|----------|
| 1 | 研究主问题与明确禁止事项已冻结 | 步骤 1 |
| 1.5 | 研究路线与排除路线已冻结 | 步骤 1.5 |
| 2 | 正式时间窗、切分方式、time label、no-lookahead 约定已冻结 | 步骤 2 |
| 3 | 正式 universe、准入口径、字段分层已冻结 | 步骤 3, 4 |
| 4 | 参数字典、公式模板、实现栈、parallelization_plan、non_rust_exceptions 已写清 | 步骤 5, 6, 8 |
| 5 | 后续 crowding / capacity 的比较基准已写清 | 步骤 7 |
| 6 | required_outputs 全部存在且有 companion field docs | 步骤 9 |

## 6.2 失败条件（fail_any_of）

以下条件**任一触发**即判失败：

| # | 条件 | 严重性 |
|---|------|--------|
| 1 | required_outputs 缺失 | 硬性 |
| 2 | 时间窗、universe 或无前视边界未冻结 | 硬性 |
| 3 | 只有裸字段名或裸参数名，没有字段解释和参数字典 | 硬性 |
| 4 | 研究问题或研究路线被后验结果倒逼修改但没有重置 mandate | 硬性 |

## 6.3 Verdict 规则

| Verdict | 适用条件 |
|---------|----------|
| **PASS** | `pass_all_of` 全部满足，`fail_any_of` 全部不触发 |
| **CONDITIONAL PASS** | 不建议常态使用。仅当 mandate 内容已冻结，且允许阶段内补充非阻断性说明时使用 |
| **PASS FOR RETRY** | Gate 逻辑已明确，但存在可修复的文档或 artifact 缺口，且 rollback_stage 仍为 mandate |
| **RETRY** | `fail_any_of` 被触发，且问题仍可在当前研究主问题下修复 |
| **CHILD LINEAGE** | 主问题改变、universe 改变、time split 改变、机制模板改变 |

---

# 7. Audit-Only 检查项

以下项目不影响 formal gate verdict，但会被记录在审查报告中：

- 专题样板写法是否足够清楚；
- 字段命名是否优雅或便于新成员阅读；
- 文档组织结构是否便于后续阶段引用；
- 参数边界的研究依据是否充分（不要求完美，但要求有依据）。

Audit-only 发现**不得**被 reviewer 偷换为 formal gate 阻断条件。

---

# 8. 常见陷阱与误区

## 8.1 看了结果再补研究问题

**表现**：先扫一轮参数或看一轮回测结果，再回来修改 mandate 中的研究主问题。

**危害**：研究问题变成了对结果的追认，后续所有统计检验的假设检验框架都被污染。无法区分"先有假设"和"先有结果"。

**正确做法**：如果看了结果后确实需要修改主问题，必须回退到 Mandate 重新冻结，或开子谱系。

## 8.2 Universe 边界模糊导致后续阶��偷换

**表现**：mandate 只写"大约这些 symbol"或"流动性好的 symbol"，没有显式列表或显式规则。

**危害**：后续阶段可以根据结果好坏随意增减 symbol，实质性地改变了研究对象，但没有触发子谱系。

**正确做法**：Universe 必须是一个显式列表或显式的、可被代码执行的准入规则。

## 8.3 字段分层不清导致越层

**表现**：raw data fields、derived fields、signal fields 混在一起，没有明确分层。

**危害**：下游 signal_ready 可能直接使用了不该在该层出现的字段，或者 train 阶段使用了 label 层字段作为特征。

**正确做法**：每个字段必须在 `field_dictionary.md` 中标注所属层级。

## 8.4 参数只有名字没有字典

**表现**：`parameter_grid.yaml` 里列了参数名和一组值，但没有写参数类型、范围依据和研究含义。

**危害**：reviewer 无法判断参数范围是否合理；后续修改参数范围时无法判断是否偏离了 mandate 冻结的边界。

**正确做法**：每个参数必须有 type、min、max、step、unit、rationale。

## 8.5 时间标签约定不明确导致前视

**表现**：mandate 没有写清楚 bar close 的定义、时间戳的归属规则，导致下游计算中某些字段实际使用了未来信息。

**危害**：前视污染会导致 train 和 test 的证据不可信，且这种 bug 通常很难被发现。

**正确做法**：在 `time_split.json` 中明确 `bar_close_definition` 和 `no_lookahead_convention`；在 `field_dictionary.md` 中对每个字段标注"t 时刻是否已知"。

## 8.6 一边抽数据一边临时改 Universe

**表现**：数据准备过程中发现某些 symbol 数据不好，就临时从 universe 中移除，而不回退 mandate。

**危害**：实质性地改变了研究对象，但没有走正式流程。

**正确做法**：如果 universe 需要改变，必须回退 mandate 或开子谱系。

## 8.7 先扫一轮结果再回写研究边界

**表现**：先跑完 signal_ready 甚至 train，看到哪些参数"效果好"，再回来修改 mandate 中的参数边界或表达式模板。

**危害**：所有后续的 out-of-sample 验证都不再可信。

**正确做法**：参数边界在 mandate 阶段冻结后，后续不得回写。

## 8.8 在没有冻结 time_split 前先看 test 或 backtest

**表现**：时间切分还没正式冻结就开始看 test 或 backtest 的分布。

**危害**：一旦看了 test 的分布再调整 time_split，就已经造成了信息泄漏。

**正确做法**：time_split 必须在 mandate 阶段冻结，冻结前不得查看 test 或 backtest 窗口的任何结果。

---

# 9. 失败与回退

## 9.1 失败后的允许动作

当 Mandate gate 未通过时，允许的修改范围如下：

| 情形 | 允许动作 | 需要开子谱系？ |
|------|----------|---------------|
| 文档不清楚 | 澄清文档表述 | 否 |
| Artifact 缺失 | 补全缺失 artifact | 否 |
| 字段解释不完整 | 修正字段解释 | 否 |
| 主问题需要改变 | 回退 mandate 重新冻结 | **是** |
| Universe 需要改变 | 回退 mandate 重新冻结 | **是** |
| Time split 需要改变 | 回退 mandate 重新冻结 | **是** |
| 机制模板需要改变 | 回退 mandate 重新冻结 | **是** |

## 9.2 Rollback 规则

```yaml
default_rollback_stage: mandate
allowed_modifications:
  - 澄清文档表述
  - 补全缺失 artifact
  - 修正字段解释
must_open_child_lineage_when:
  - 主问题改变
  - universe 改变
  - time split 改变
  - 机制模板改变
```

## 9.3 关联失败 SOP

Mandate 阶段目前尚无专属的失败处置 SOP（即 `docs/sop/failures/` 下没有 `00_mandate_failure_sop_cn.md`）。当 Mandate gate 触发失败时，按上述 9.1-9.2 的规则处理。

如果后续建立了专属的 mandate failure SOP，应放置在：
`docs/sop/failures/00_mandate_failure_sop_cn.md`

---

# 10. 阶段专属要求

## 10.1 字段/参数/表达式冻结的详细要求

### 字段冻结

- 每个字段必须在 `field_dictionary.md` 中有条目。
- 条目必须包含：字段名、类型（int / float / bool / string / timestamp）、单位、来源（raw / derived / signal / label）、计算公式或数据源、时间语义（t 时刻是否已知）。
- 如果字段来自外部数据源，必须写清楚数据源版本和更新频率。

### 参数冻结

- 每个可调参数必须在 `parameter_grid.yaml` 中有条目。
- 条目必须包含：参数名、类型、min、max、step 或枚举值、unit、rationale。
- 参数边界的 rationale 不要求完美，但必须有研究依据（哪怕是"基于文献 / 基于经验 / 基于预实验"）。

### 表达式冻结

- 每个表达式模板必须有：公式本身、符号说明、研究含义（为什么有意义）、时间语义（输入在 t 时刻是否都已知）。
- 禁止使用的机制或组合必须显式列出。

## 10.2 Companion Field Documentation 制度

Companion field doc 是本阶段的强制要求，不是可选项：

- 每个机器可读 artifact 必须在 `mandate.md` 或 `research_scope.md` 中有对应的人类可读解释。
- `field_dictionary.md` 必须覆盖所有在公式、代码、配置中出现过的字段。
- 如果某个字段在多个 artifact 中出现，`field_dictionary.md` 中应只有一个权威条目，其他地方引用它。

## 10.3 mandate.md vs research_scope.md 的分工

| 内容 | 归属文档 |
|------|----------|
| 研究主问题与不研究什么 | `mandate.md` |
| 时间窗与切分说明 | `mandate.md` |
| 参数边界与表达式模板 | `mandate.md` |
| 实现栈与并行计划 | `mandate.md` |
| Universe 与准入口径 | `research_scope.md` |
| 字段分层与字段族定义 | `research_scope.md` |
| 容量与拥挤审计口径 | `research_scope.md` |
| 退市、停牌、低流动性处理约定 | `research_scope.md` |

原则：`mandate.md` 偏重"研究问题和方法论边界"，`research_scope.md` 偏重"数据和执行边界"。

---

# 11. Checklist 速查表

提交 gate review 前，逐项勾选：

- [ ] 主问题已冻结
- [ ] 不研究什么已写清
- [ ] 时间窗和切分已冻结
- [ ] Universe 已冻结
- [ ] 时间标签与无前视约定已冻结
- [ ] 字段分层和字段解释已写清
- [ ] 参数字典已写清
- [ ] 信号机制与表达式模板已冻结
- [ ] 公式的符号说明、研究含义和时间语义已写清
- [ ] crowding / capacity 的比较口径、流动性代理与参与率边界已写清
- [ ] `mandate.md` 已生成
- [ ] `research_scope.md` 已生成
- [ ] `time_split.json` 已生成
- [ ] `parameter_grid.yaml` 已生成
- [ ] `run_config.toml` 已生成
- [ ] `artifact_catalog.md` 已生成
- [ ] `field_dictionary.md` 已生成
- [ ] 所有机器可读产物已登记到 `artifact_catalog.md`
- [ ] 所有字段都能追到 `field_dictionary.md` 或 `*_fields.md`
- [ ] 每个机器可读产物都有 companion field doc
- [ ] 自审已通过 formal gate 规则（§6.1 全满足、§6.2 全不触发）

---

# 12. 关联文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 主流程 SOP | `docs/sop/main-flow/research_workflow_sop.md` | 全流程解释层，Mandate 的上下文 |
| Gate YAML | `contracts/stages/workflow_stage_gates.yaml` | Gate contract 真值 |
| Data Ready 失败 SOP | `docs/sop/failures/01_data_ready_failure_sop_cn.md` | 下一阶段的失败处置 |
| Signal Ready 失败 SOP | `docs/sop/failures/02_signal_ready_failure_sop_cn.md` | 信号阶段失败处置 |
| Lineage 变更控制 | `docs/sop/failures/lineage_change_control_sop_cn.md` | 子谱系开立流程 |
| 审查模板 | `contracts/review/review_checklist_master.yaml` | Gate 审查检查模板 |
| Mandate 失败 SOP | `docs/sop/failures/00_mandate_failure_sop_cn.md` | **尚未建立** |
