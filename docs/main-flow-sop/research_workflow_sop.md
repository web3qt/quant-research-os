# 团队研究 Workflow 指导文档

## 0. 文档分工与默认核查顺序

### 0.1 双层文档分工

这份总指南现在承担的是解释层，不再假设自己同时也是唯一的 gate 真值。

正式研究流程默认使用两层文档：

- `docs/all-sops/第一层-主流程sop/research_workflow_sop.md`
  - 负责解释阶段目的、术语、常见误区、artifact 治理逻辑和回退纪律；
  - 负责回答“为什么要这样分阶段”“每个阶段在方法论上想防什么错误”。
- `docs/all-sops/workflow_stage_gates.yaml`
  - 负责提供 machine-readable 的阶段 gate contract；
  - 负责回答“当前阶段必须检查什么、哪些是 formal gate、哪些只是 audit-only、什么条件下可以写 `PASS / CONDITIONAL PASS / PASS FOR RETRY / RETRY / NO-GO / GO / CHILD LINEAGE`”。

如果两者之间出现表述差异，默认按下面的优先级解释：

1. `docs/all-sops/workflow_stage_gates.yaml` 是 gate contract 真值。
2. `docs/all-sops/第一层-主流程sop/research_workflow_sop.md` 是解释层和写作层补充。
3. 具体谱系自己的阶段 gate 文档，必须同时满足上面两者，而不是自创状态词或自创例外。

### 0.2 Agent / Reviewer 默认核查顺序

不论是人工 reviewer，还是 agent reviewer，默认都按同一顺序核查：

1. 先识别当前正在核查的正式阶段。
2. 读取 `docs/all-sops/workflow_stage_gates.yaml` 中该阶段的 contract。
3. 核对 `required_inputs / required_outputs / formal_gate / audit_only / verdict_rules / rollback_rules`。
4. 再读取该研究线对应阶段的 gate 文档、`artifact_catalog.md` 和 `field_dictionary.md`。
5. 先判断 formal gate，再记录 audit-only 发现；不得把 audit-only 发现偷换成 formal gate，也不得把 formal gate 埋进 prose。
6. 最后给出统一 verdict，并写清楚 `rollback_stage`、`allowed_modifications` 和 `downstream_permissions`。

这条顺序的意义是：先看 contract，再看实例；先看 formal gate，再看补充证据；先给 verdict，再谈感觉。

## 1. 文档定位

这份文档不是某个因子的研究报告，也不是某一条策略线的专项操作手册。

它的目标只有一个：把团队内正式研究应该如何推进，沉淀成统一的 workflow、统一的门禁语言、统一的 artifact 契约和统一的回退纪律。

它解决的不是“研究员会不会做分析”，而是下面这些更常见、也更容易把研究做坏的问题：

- 研究问题还没冻结，就已经开始扫参数和看回测。
- 数据口径、信号口径、交易口径混在一起，最后没有人能说清楚结论来自哪里。
- 团队里每个人都觉得自己“已经看过结果”，但没有统一 artifact，后续无法复盘。
- 某阶段失败后，大家默认是在原地继续修，结果把 `test`、`backtest`、`holdout` 都修成了训练集。
- 最后只保留通过的版本，不保留负结果和失败路径，团队无法积累真实经验。

这份文档适用于正式进入团队研究管线的系统化研究，尤其适用于：

- 信号研究。
- 因子筛选与白名单研究。
- 回测晋级。
- `holdout` 验证。
- `shadow` 准入前的研究治理。

它不适用于：

- 一次性的 notebook 草稿。
- 临时灵感验证。
- 没有冻结研究问题的探索性试验。
- 只为了“看一眼分布”的临时分析。

专题研究文档应该视为本规范的样板或实例，而不是替代本规范。如果某条研究线需要保留专题样板，应明确把它视为补充材料，而不是新的总规范。

## 2. 指导思想

### 2.1 Hypothesis before results

先定义研究问题，再看结果。

如果主问题、研究边界、Universe、时间窗、允许信号族都没有冻结，后面的所有显著性和收益都可能只是对结果的追认。团队规范里最先冻结的不是参数，而是问题本身。

### 2.2 Data contract before evidence

先确认数据可研究，再讨论是否存在 alpha。

正式研究不允许跳过数据契约。原始数据的覆盖、对齐、缺失语义、QC 结果、时间标签一致性，必须先审计清楚。否则 later stage 看到的“结构”，很可能只是坏数据、补值方式或时间戳错位造成的假信号。

### 2.3 Freeze first, verify later

先在 `train` 定尺子，再用 `test` 验证尺子，最后用 `backtest` 和 `holdout` 检查交易能否成立。

这个顺序不能反过来。只要出现“看了 `test` 再改阈值”“看了 `backtest` 再改白名单”“看了 `holdout` 再调参数”，研究就已经被污染。

### 2.4 Separate evidence layers

统计证据、策略证据、执行证据不是一回事。

- `test` 回答的是信号结构是否存在。
- `backtest` 回答的是冻结后的规则是否可交易。
- `shadow` 回答的是执行语义和真实运行条件下是否还成立。

把这三件事分开，团队才能知道失败到底是出在机制、交易规则还是执行层。

### 2.5 Artifact over memory

正式结论必须依赖 artifact，而不是依赖“谁看过”“谁记得”。

每个阶段都必须留下机器可读结果、机器可读配置、人类可读结论和 gate 决策。没有 artifact，就等于这个阶段没有正式完成。

### 2.6 Controlled retry, not silent mutation

允许重试，但重试必须受控、记账、可审计。

如果只是实现错误、数据 bug 或执行层 bug，可以回退到允许修改的阶段做 controlled retry；如果研究问题、机制假设、信号定义发生了实质变化，就不能在原线继续修，必须开 `child lineage`。

### 2.7 Rust-first and efficient search

正式流程默认采用 `Rust-first` 实现栈，并优先使用成熟、维护活跃的主流库。参数较多的研究默认采用 `coarse-to-fine` 搜索、缓存可复用特征和并行执行，而不是直接做暴力全量 `grid search`。

原因很简单：

- 研究工程要能复现，而不是靠个人临时脚本。
- 大规模搜索如果没有并行计划和 ledger，最后只会剩下“一个最好结果”，而失去搜索过程本身的审计价值。
- 对正式研究而言，计算效率不是锦上添花，而是能否保留完整试验轨迹的基础条件。

### 2.8 Companion field documentation is mandatory

任何阶段只要生成机器可读 artifact，就必须同时生成 companion field documentation。

这里的“机器可读 artifact”包括但不限于：

- `csv`
- `parquet`
- `json`
- `yaml`
- `toml`
- `ledger`
- `manifest`
- `summary`

正式研究最低要求有两层：

- `artifact_catalog.md`
  - 列出本阶段所有关键产物；
  - 写清用途、粒度、主键、消费者、是否机器可读；
  - 指向对应的字段说明文档。
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`
  - 逐项解释机器产物里的字段；
  - 最少写清字段名、类型、含义、单位、是否可空、空值语义、约束、所属层、下游消费阶段。

允许一个小阶段用一份 `field_dictionary.md` 覆盖全阶段，也允许大阶段按产物拆成多个 `*_fields.md`；但无论采用哪种形式，都必须通过 `artifact_catalog.md` 建立完整映射。

这条要求是 formal gate，不是写作建议。任何阶段如果出现下面任一情况，默认不能 `PASS`，也不能 `CONDITIONAL PASS`：

- 缺少 `artifact_catalog.md`
- 某个机器可读产物没有 companion 字段说明
- 人类可读文档里使用了字段，但在正式字段说明文档中找不到

## 3. 个人研究中的职责与约束

这份 workflow 也适用于个人研究，但这里不再强调多人组织分工，而是强调单人必须显式切换的职责视角。

一个人可以兼任所有职责，但不能把“提出假设、实现研究、审查证据、决定晋级”混成同一个动作；否则研究很容易退化成边看结果边改定义。

| 职责视角 | 核心责任 | 明确不能做的事 |
| --- | --- | --- |
| `Explorer` | 提出研究主问题、冻结边界、解释机制、明确不研究什么 | 不能在看到后验结果后悄悄改主问题或扩大研究范围 |
| `Builder` | 落地数据、信号、统计检验、回测、artifact 与复现流程 | 不能用实现便利替代研究纪律，也不能把验证层字段偷渡成在线信号 |
| `Critic` | 以独立审查视角检查泄漏、字段越层、样本污染、artifact 完整性与负结果保留 | 不能因为结果“看起来不错”就跳过证据审查 |
| `Auditor` | 基于已有 artifact 给出 gate verdict，决定是晋级、回退重试，还是开新谱系 | 不能把“先继续调一调”当成默认动作，也不能把自我说服当成正式结论 |
| `Orchestrator` | 维护阶段顺序、lineage、目录结构、参数追踪和 retry 记账 | 不能跳阶段，也不能在没有记录 rollback 范围时静默重试 |

执行纪律：

- 单人可以兼任全部职责，但每个正式 gate 前必须先完成 `Builder` 产物，再切到 `Critic` 做书面自审，最后由 `Auditor` 给出明确 verdict。
- 如果没有外部 reviewer，至少要留下自审记录，写清楚通过理由、主要风险、禁止修改项和下一阶段允许消费的对象。
- 个人研究允许 self-gate 进入下一研究阶段，但这只代表“个人流程内通过”，不自动等价于团队正式批准。
- 若要进入 `Shadow Admission`、`Canary` 或真实资金环境，强烈建议补外部复核；没有第二人复核时，应在结论里明确标注这一限制。

## 4. 标准阶段流转

正式研究必须按下面顺序推进，不允许跳阶段：

1. `Mandate`
2. `Data Ready`
3. `Signal Ready`
4. `Train Calibration`
5. `Test Evidence`
6. `Backtest Ready`
7. `Holdout Validation`
8. `Promotion Decision`
9. `Shadow Admission`
10. `Canary / Production`

上面这组阶段的 machine-readable gate 真值统一记录在 `docs/all-sops/workflow_stage_gates.yaml` 中。下面各节继续负责解释阶段目的、artifact 角色、常见误区和推荐 gate 语义，但不再假设 prose 自己就是唯一 contract。

下面按阶段说明为什么这样切、每一步要交什么、失败后允许怎么处理。

### 4.1 Mandate

**核心问题**

这条研究线到底研究什么，不研究什么。

**为什么必须单独存在**

`Mandate` 是全流程里最容易被低估、也最关键的阶段。它的价值不是“写一份说明”，而是冻结后续一切证据的解释边界。没有它，团队无法分辨哪些修改属于实现修复，哪些修改已经改变了研究问题。

**至少要冻结的内容**

- 研究主问题。
- 正式时间窗与切分方式。
- Universe 与准入口径。
- 允许与禁止的研究字段族以及解释，不能只列字段名，必须说明字段属于哪一层、回答什么问题、为什么存在以及后续由哪个阶段消费。
- 带参数的信号机制与表达式模板，至少写清核心主信号、底层状态、状态/过滤字段与验证层专用字段。
- 时间标签和无前视约定。
- 首轮参数边界，以及每个参数的字段字典、单位、作用层和约束。
- 容量与拥挤审计口径，至少写清后续使用的流动性代理、参与率上限、自冲击假设边界，以及要比较的已知拥挤/风格基准。
- 实现栈、并行计划、非 Rust 例外说明。

**必备输出**

- `mandate.md`
- `research_scope.md`
- `time_split.json`
- `parameter_grid.yaml` 或等价参数网格
- `run_config.toml` 或等价运行配置
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**说明**

上面这组文件共同冻结研究主问题、边界、时间切分、参数身份和运行合同。总指南只要求它们齐备且互相一致，不在这里展开专题样板。

`00_mandate` 的制度要求只有三条：

- 所有机器可读产物都必须登记到 `artifact_catalog.md`。
- 所有正式字段都必须能追到 `field_dictionary.md` 或 `*_fields.md`。
- 更细的字段、参数和公式解释，应写在具体谱系自己的 `outputs/<lineage>/00_mandate/` 产物里，而不是在总指南里重复展开。

**晋级标准**

只有当研究问题、样本边界和禁止事项都写清楚，团队才允许进入 `Data Ready`。

**字段、参数与表达式要求**

- 不允许只给裸字段名。每个字段至少要说明含义、所属层、消费阶段，以及能否进入正式 schema。
- 不允许只给裸参数名。每个参数至少要说明作用层、单位、约束，以及当前只是候选还是已经冻结。
- `Mandate` 必须把信号机制收敛成可物化的表达式模板，并补自然语言解释，写清符号含义、研究作用、时间语义和无前视边界。
- 如果字段解释、参数字典或表达式模板缺失，默认不得进入 `Data Ready`。

**明确禁止**

- 一边抽数据一边临时改 Universe。
- 先扫一轮结果，再回写研究边界。
- 在没有冻结 `time_split` 前先看 `test` 或 `backtest`。

**失败后的允许动作**

- 如果只是文档不清楚、边界缺失，可以停留在本阶段补齐。
- 如果后续阶段发现主问题本身要改，必须回退到这里重新冻结。

### 4.2 Data Ready

**核心问题**

原始数据能否被转换为共享、可审计、可复用的数据基础层。

**为什么必须独立于信号研究**

团队最常见的伪发现之一，就是把数据问题误当成 alpha。缺失、对齐、去重、开收盘标签混用、补值语义不清，这些都足以制造“看起来有结构”的结果。把 `Data Ready` 单独成阶段，是为了强制团队先解决这些问题，再允许研究信号。

**必做事项**

- 对齐统一时间栅格。所有 symbol 必须按同一 `ts` 对齐，缺失也要显式保留，避免时间错位制造伪结构。
- 保留缺失与脏数据语义，不得静默吞掉。缺失、坏价格、停滞和异常跳变都应显式标记，而不是通过填值、删点或隐式修复悄悄抹平。
- 生成 QC 汇总。团队需要快速看到每个标的的缺失率、坏价率、stale 率、outlier 率和可用率，而不是只知道“数据跑出来了”。
- 审计基础腿和核心资产的覆盖。要先确认 `BTC` 或其他基准腿本身覆盖合格，否则整条研究线的相对关系和回归检验都不成立。
- 输出可复用 rolling statistics 或缓存。把后续信号层、检验层和回测层会反复使用的 rolling 均值、波动或 pair 统计提前固化，避免各阶段各算各的。

**必备输出**

- `aligned_bars/`
- `rolling_stats/`
- `qc_report.parquet`
- `dataset_manifest.json`
- `data_contract.md`
- `dedupe_rule.md`
- `universe_summary.md`
- `universe_exclusions.*`
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**说明**

这些输出共同回答三件事：底表是否可复用、质量问题是否被显式记录、Universe 排除是否可审计。

- `aligned_bars/` 与 `rolling_stats/` 是后续阶段复用的统一输入。
- `qc_report.parquet`、`dataset_manifest.json`、`data_contract.md`、`dedupe_rule.md`、`universe_summary.md`、`universe_exclusions.*` 负责说明质量、版本、边界与排除理由。
- `01_data_ready` 中所有机器可读产物都必须登记到 `artifact_catalog.md`，并能追到 companion 字段说明。

**晋级标准**

团队能够明确回答“这份数据为什么能研究”，而不是只知道“程序跑完了”。

**明确禁止**

- 在原始层把缺失秒静默 forward-fill。
- 混用 `open_time` 和 `close_time` 作为主键。
- 发现覆盖问题后直接静默删币，不留下排除报告。

**失败后的允许动作**

- 允许修数据抽取、对齐、QC 和覆盖审计逻辑。
- 如果发现要改正式时间窗、准入规则或 Universe 口径，必须回退到 `Mandate`。

### 4.3 Signal Ready

**核心问题**

研究对象是否已经被定义成统一、可复现、可比较的信号字段合同。

**为什么不能直接从数据跳到 Train**

如果没有独立的信号层，团队就很容易在不同阶段对“同一个信号”用不同计算方式或不同时间标签解释。到最后即使结果看起来一致，实际比较的也不是同一个对象。

**必做事项**

- 固定信号字段定义。
- 固定主时间标签与未来收益对齐方式。
- 生成每个对象的信号时序和覆盖报告。
- 显式记录本阶段已经物化的 `param_id` 集合，以及它属于 `baseline`、`search_batch` 还是 `full_frozen_grid`。
- 为后续 `Train` 和 `Test` 提供统一字段合同。

**与 `Mandate` 的边界**

`Signal Ready` 的职责不是重新发明信号机制，而是把 `Mandate` 已冻结的表达式模板正式实例化。

具体来说，本阶段应完成：

- 把 `Mandate` 中已经允许的参数维度编码成稳定 `param_id`；
- 把表达式模板落成固定 schema、固定字段命名和固定时间语义；
- 物化 baseline 或 search batch 的正式信号时序；
- 显式写清“本阶段到底实例化了哪些参数组、哪些字段”。

如果本阶段发现需要改变核心主信号、底层状态定义或表达式机制，那不是 `Signal Ready` 内的小修，而是应回退到 `Mandate` 或开新谱系。

**必备输出**

- `param_manifest.csv` 或等价的参数物化清单
- `timeseries/`
- `symbol_summary.parquet`
- `signal_coverage.*`
- `signal_fields_contract.md`
- `signal_gate_decision.md` 或等价的 `signal_ready.md`
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**说明**

这组产物的作用是冻结“后续到底在用什么信号”：

- `param_manifest.csv` 定义已物化的 `param_id` 集合与 materialization scope。
- `timeseries/` 是下游统一消费的正式信号时序；`signal_coverage.*` 和 `symbol_summary.parquet` 用来审计覆盖与退化情况。
- `signal_fields_contract.md` 定义 schema、字段分层、参数身份和时间语义；`signal_gate_decision.md` 记录正式阶段结论。
- `02_signal_ready` 中所有机器可读产物都必须登记到 `artifact_catalog.md`，并能追到 companion 字段说明。

**晋级标准**

团队能够明确回答“后续所有阶段到底在用哪个字段、哪个标签、哪个参数身份”。

**Signal Ready formal gate 规则**

为了避免 `Signal Ready` 阶段长期只有“文件都生成了，但状态一律还是 `CONDITIONAL PASS`”的语义漂移，建议本阶段显式采用下面这套 formal gate：

- `PASS`
  - 必备 artifact 已生成；
  - `failed symbols / failed params = 0`；
  - `skipped params = 0`；
  - 未触发最小质量保留项。
- `CONDITIONAL PASS`
  - 必备 artifact 已生成；
  - 允许进入下一阶段；
  - 但存在显式保留事项，例如 `skipped params`、退化参数组、或已明显不可研究的 `symbol-param_id` 覆盖退化。
- `FAIL`
  - baseline 或必需对象物化失败；
  - `failed symbols / failed params > 0`；
  - 或关键 gate artifact 缺失，导致本阶段不能形成正式信号层合同。

`Signal Ready` 的最小质量保留项建议显式冻结为：

- `finite_residual_z_ratio < 0.01`
- `low_sample_rate > 0.98`
- `pair_missing_rate > 0.70`

这里要明确：

- 这些阈值不是 `Train Calibration` 的最终保留标准；
- 它们只是 `Signal Ready` 用来识别“虽然文件已经落盘，但信号实际上已明显退化”的最小保底线；
- 一旦触发，就不应再写成无保留的 `PASS`，而应写成带 reservations 的 `CONDITIONAL PASS`。

**额外要求**

- 总规范不要求所有研究线都在 `Signal Ready` 一次性物化完整参数空间。
- 但无论本阶段只物化单组 baseline，还是物化一整批 `search_batch`，都必须把“当前已经落盘的 `param_id` 集合”写进 artifact。
- `Train Calibration` 只能消费这批已经在 `Signal Ready` 显式物化过的 `param_id`，不能在训练阶段临时新增参数组。

如果一条研究线只有 `timeseries/`、`signal_fields_contract.md`、`signal_coverage.*`，但没有单独的阶段结论或 gate 文档，那么它更准确的表述应是：

- “已经产出 signal layer artifacts”

而不是：

- “已经正式关闭 `Signal Ready` 阶段”

因为前者代表“信号结果已经落盘”，后者代表“阶段门禁已经被正式记录并允许晋级”。两者不能混用。

**明确禁止**

- 在 `Train` 里边算边改信号定义。
- 不记录参数身份，只靠文件名猜是哪组参数。
- 在 `Train` 阶段临时扩充未在 `Signal Ready` 物化过的 `param_id`。
- 把信号可用性问题留给 `Test` 才发现。

**失败后的允许动作**

- 允许修正信号实现、字段命名、标签对齐。
- 如果要改变研究信号的机制定义，则必须回退到 `Mandate` 或开新谱系。

### 4.4 Train Calibration

**核心问题**

如何在不接触未来窗口的前提下，把尺子定下来。

**为什么它只能负责“定尺子”**

`Train` 的职责是校准，不是验收。它应该冻结阈值、分位切点、质量过滤、波动分层和候选参数范围，而不应该宣布哪一组已经“成功”。一旦 `Train` 开始承担“宣布胜利”的角色，后面的 `Test` 就会沦为走流程。

**必做事项**

- 冻结分位阈值。
- 冻结 regime 切点。
- 做信号可研究性过滤。
- 在必要时做参数粗筛，但只排除荒谬区间。
- 记录完整参数 ledger。

**说明**

`Train` 只负责定尺子，不负责宣布胜利。

- 阈值、regime 切点和条件层切点都应在训练窗内冻结，供下游复用，不得在 `Test` 或 `Backtest` 重估。
- 训练阶段可以排除根本不可研究的 `symbol-param_id` 组合，但不能因为后验表现不好看而静默裁掉参数空间。
- 无论保留还是拒绝，都必须保留完整 ledger 和拒绝原因。

**必备输出**

- `train_thresholds.*`
- `train_quality.*`
- `train_param_ledger.csv`
- `train_rejects.csv`
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**说明**

- `train_thresholds.*` 冻结下游必须复用的阈值与分层尺子。
- `train_quality.*`、`train_param_ledger.csv`、`train_rejects.csv` 负责记录可研究性判断、保留对象和拒绝原因。
- `03_train_freeze` 中所有机器可读产物都必须登记到 `artifact_catalog.md`，并能追到 companion 字段说明。

**晋级标准**

后续 `Test` 能拿着一套已经冻结的尺子去验证，而不是一边验证一边重估。

**明确禁止**

- 根据 `test` 结果回头重算 `train` 阈值。
- 在 `train` 用收益最大化方式选最终策略参数。
- 只保留通过的参数，不保留被淘汰的搜索轨迹。

**失败后的允许动作**

- 允许修训练内的质量门槛或冻结逻辑。
- 如果修复动作需要借用 `test` 或 `backtest` 的信息，视为污染，必须整体回退。

### 4.5 Test Evidence

**核心问题**

冻结后的信号结构，是否在独立样本里仍然成立。

**为什么这一步只验证结构，不负责赚最多的钱**

`Test` 的职责是验证方向和结构，而不是做收益最大化。它应该回答的是“这个机制在新样本里有没有继续存在”，而不是“怎么把这一段样本调到最好看”。

**必做事项**

- 复用 `Train` 冻结尺子。
- 在独立样本上计算统计证据。
- 冻结白名单、`best_h` 或后续候选集。
- 记录 formal gate 与 audit gate。

**说明**

`Test` 只验证结构是否在独立样本中延续。

- 只能复用 `Train` 已冻结的阈值、切点和保留对象，不得在测试窗重估。
- 本阶段要冻结进入 `Backtest` 的白名单、`best_h` 或等价候选集，并把 formal gate 与 audit gate 分开记录。
- 统计证据服务于结构验证，不用于测试窗收益最大化。

**必备输出**

- `report_by_h.parquet`
- `symbol_summary.parquet`
- `admissibility_report.parquet`
- `test_gate_table.csv`
- `crowding_review.md`
- `test_gate_decision.md`
- `selected_symbols_test.*`
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**说明**

- `report_by_h.parquet` 保留最细粒度的测试证据；`symbol_summary.parquet` 和 `admissibility_report.parquet` 汇总可晋级性。
- `test_gate_table.csv` 给出紧凑 gate 总表；`selected_symbols_test.*` 是 `Backtest` 允许消费的正式候选集。
- `crowding_review.md` 负责记录拥挤/风格重叠等解释证据。
- `04_test_evidence` 中所有机器可读产物都必须登记到 `artifact_catalog.md`，并能追到 companion 字段说明。

**晋级标准**

团队能够区分“统计结构成立”和“交易上值得推进”是两层不同结论。

**明确禁止**

- 在 `test` 里重估 `train` 分位阈值。
- 看了 `backtest` 再回写 `test` 白名单，但不做明确 retry 记账。
- 把审计子集和正式白名单混成一回事。

### 4.5.1 条件分层与辅助条件层

辅助条件默认先作为 `Test` 阶段的 `audit evidence`，回答主信号在什么对象、状态或环境下更可信，而不是直接并入主打分。

最小纪律：

- 只能使用上游已冻结的主信号、辅助字段定义和阈值，不得在 `Test` 临时重估后再包装成正式规则。
- 静态跨对象效应与动态时变效应必须分开审计，避免把 `whitelist`、`state gate` 和 `regime gate` 混成同一个动作。
- 只有当某个辅助条件已在更早阶段被正式声明可消费，且机制文档写明它可作为 gate 或 regime 规则时，它才可以升级为 formal rule；否则应作为解释证据，必要时开 `child lineage`。
- 如需保留证据链，可补 `report_by_h_with_conditions.*` 或等价附加产物。

**失败后的允许动作**

- 如果只是实现 bug，可回退到 `Signal` 或 `Train`。
- 如果是机制不成立，应给出 `NO-GO` 或开 `child lineage`，不能在原线悄悄换题。

### 4.5.2 Crowding Distinctiveness 与 Capacity Review

`crowding distinctiveness` 和 `capacity / self-impact` 不应合并成同一个阶段，也不应在同一时间点下结论。

放置原则：

- `Mandate` 只冻结比较基准、流动性代理、参与率边界和容量口径。
- `Test Evidence` 处理 `crowding_review.md`，回答 alpha 与已知拥挤或风格暴露的关系；默认属于审计证据，不直接代替 formal gate。
- `Backtest Ready` 处理 `capacity_review.md`，在正式交易规则、成本模型和双引擎语义下判断 deployable capital 与 self-impact。
- `Shadow Admission` 复核 `Backtest` 的容量结论，并冻结监控阈值、降额动作和回滚条件。

最小纪律：

- 不得因为 `crowding` 发现就在 `Backtest` 阶段回改 `Test` 白名单而不记账。
- 不得把容量问题包装成“alpha 机制不存在”。
- 如果 `crowding review` 中的条件层要升级成正式机制，应按 retry 纪律回退，或开 `child lineage`。

### 4.6 Backtest Ready

**核心问题**

冻结后的交易规则，在独立 OOS 窗口里能否成立。

**为什么必须晚于 Test**

如果在看到回测收益后才决定白名单、`best_h` 或筛选门槛，那么回测就不再是 OOS，而是在替研究流程做隐性调参。先过 `Test`，再做 `Backtest`，是为了保持证据层次清晰。

**必做事项**

- 只使用冻结的候选集、白名单和交易规则。
- 必须完成 `vectorbt`、`backtrader` 两套正式回测，不允许只跑单一回测引擎就宣布 `Backtest Ready`。
- 输出组合和单标的层面的交易结果。
- 回测收益、`Sharpe`、回撤必须基于正式资金记账口径计算，至少要能说明初始资金、仓位/名义本金规则、费用模型和资金曲线更新方式；不允许用 `spread-unit` 或 `Δs_level` 这类非资金单位分数冒充正式回测收益。
- 把费用、换手、持有期、回撤解释清楚，并给出双引擎之间的一致性说明。

**如何理解这一步的策略搜索边界**

- `Backtest` 不是重新发明 alpha，而是把上游已经冻结好的信号和候选集，映射成正式可交易规则。
- 如果 Stage 5 要搜索多套策略组合，搜索空间必须按层拆成有限集合，例如 `execution / sizing / portfolio / risk overlay` 四层，而不是任由研究员临时改脚本参数。
- 最好先定义一个最小可执行 baseline，再围绕 baseline 做小范围 `coarse-to-fine` 搜索；不要一开始就把仓位、风控、开平仓、组合规则一起做暴力全搜索。
- 风控叠层要和 alpha 分开记账。例如 `invalid_sample`、高波动停开仓、交易所异常熔断属于 `risk overlay`，不应被包装成“信号的一部分”。
- 如果交易规则真的需要搜索，必须留下“规则网格 -> 评估结果 -> 保留组合”的因果链，方便后续解释为什么某组规则进入 `Holdout`。

**建议附加输出**

- `execution_grid.yaml`、`portfolio_grid.yaml`、`risk_overlay_grid.yaml` 或等价规则清单
- `strategy_combo_ledger.csv` 或等价的策略组合评估账本
- `selected_strategy_combo.json` 或等价的最终保留组合说明

**默认晋级预算**

- 快速筛选层最多保留 `min(5, ceil(候选总数 * 20%))` 个候选进入正式 bar 级回测。
- 正式 bar 级回测层最多保留 `3` 个候选进入压力测试、`Holdout` 准备或最终 shortlist。
- 最终进入 `Holdout / Shadow` 的主方案默认只能有 `1` 个；如果保留主备双轨，最多 `2` 个，并在 gate 文档里明确 `primary / backup`。

**异常高收益的强制复核**

当 `Backtest` 出现“明显好得不正常”的结果时，团队默认先质疑，再允许晋级；这不是研究员个人的主观习惯，而是 formal gate 的一部分。

只要出现下面任一情况，就必须触发 `abnormal performance sanity check`：

- 回测收益、`Sharpe`、`Calmar`、胜率、盈亏比或资金曲线斜率明显超出该研究机制、该市场微观结构或团队同类策略的常识范围。
- 大部分收益集中在极少数 `symbol`、极少数交易、极少数日期、极少数 regime 或极少数事件窗口上，导致整体结果看起来异常漂亮。
- 双引擎结果虽然方向一致，但收益高得离谱，而当前解释仍停留在“结果很好看”，没有定位到可审计的收益来源。

触发后，至少必须完成下面这些检查：

- 前视、时间标签、未来收益对齐、白名单冻结、`best_h` 冻结、阈值冻结是否被破坏。
- 手续费、滑点、资金费率、杠杆/名义本金、强平或爆仓语义、资金曲线更新口径是否与正式规则一致。
- 坏 bar、缺失、`outlier`、`stale`、极端跳变、成交异常或数据修复逻辑是否放大了收益。
- 收益集中度拆解是否清楚，至少要能按 `symbol`、交易、日期、方向、regime 或事件窗口解释主要收益来源。
- `vectorbt / backtrader` 是否完成逐笔、逐日或逐窗口 spot check，确认高收益来自同一批交易语义，而不是引擎实现偏差。

这项复核是 formal gate，不是建议项。未完成前：

- 不允许写 `PASS`。
- 不允许写 `CONDITIONAL PASS`。
- 不允许进入 `Holdout` 或 `Promotion`。
- 阶段状态只能写 `RETRY`、`PASS FOR RETRY`，或在结论里明确说明仍需调查的 blocking issue。

**Formal gate**

- `PASS`：至少有 `1` 套策略组合通过项目预设的收益、回撤、换手、容量和风险约束；`vectorbt / backtrader` 双引擎均成功且 `semantic_gap = false`；最终保留组合、成本模型、仓位规则和风控规则已经冻结；若触发了 `abnormal performance sanity check`，则复核已经完成且未发现阻断性问题；若存在多套候选，晋级预算和 ledger 记录完整且无保留事项。
- `CONDITIONAL PASS`：至少有 `1` 套策略组合通过 formal gate，且双引擎无语义冲突，但仍存在明确保留事项，例如容量假设仍待补强、压力测试尚未完成、主备双轨暂未收敛为单一主方案；若触发了 `abnormal performance sanity check`，则其阻断性问题已经排除，仅保留非阻断性 reservations；这些保留事项必须写入 `backtest_gate_decision.md`。
- `FAIL`：没有任何策略组合通过正式资金口径下的成本后门槛；或双引擎存在语义冲突；或候选组合没有留下完整 ledger / 冻结规则，导致后续阶段无法照单执行。

**失败分支**

当 `Backtest Ready` 失败时，不允许用同一份 OOS 继续静默调参直到看起来可接受。此时应改用 [`docs/guides/backtest-fail-sop.md`](/Users/mac08/workspace/web3qt/superquant/docs/guides/backtest-fail-sop.md) 进入失败治理流程，先冻结失败包，再分类失败原因，最后回到现有门禁语义下决定通常是 `RETRY`、`PASS FOR RETRY`、`NO-GO` 还是 `CHILD LINEAGE`。

其中：

- `ENG_FAIL` 对应可修复的实现 / 数据 / 撮合问题，正式决策通常是 `RETRY`。
- `EXEC_FAIL` 对应执行语义、成本或容量问题，正式决策通常是 `RETRY`。
- `RESEARCH_FAIL` 对应 `03/04` 证据层问题，正式决策仍是 `RETRY`，但 `rollback_stage` 必须回到 `03_train_freeze` 或 `04_test_evidence`。
- `THESIS_FAIL` 对应机制不成立或经济性不可接受，正式决策应为 `NO-GO`。
- 若研究主问题、机制、Universe 或时间切分发生实质变化，应开 `CHILD LINEAGE`，而不是继续在原线修补。
- `PASS FOR RETRY` 仍保留为正式门禁状态，适用于需要先受控回退再继续的场景，不会因为本 SOP 的失败分类而消失。

**必备输出**

- `engine_compare.csv` 或等价的多引擎对照文档
- `vectorbt/`、`backtrader/` 两个子目录；每个子目录下至少包含：
  - `selected_symbols.*`
  - `trades.parquet`
  - `symbol_metrics.parquet`
  - `portfolio_timeseries.parquet`
  - `portfolio_summary.parquet`
  - `summary.txt`
- `capacity_review.md`
- `backtest_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

其中 `capacity_review.md` 负责把正式资金曲线口径下的容量判断写清楚，至少覆盖流动性代理、参与率假设、自冲击边界、容量瓶颈 symbol、成本吞噬位置以及它是 blocking issue 还是 non-blocking reservation。

**晋级标准**

策略层能说明“为什么通过”或者“为什么失败”，而不是只展示一条净值曲线；并且双引擎的方向、成本归因和主要风险解释不能互相矛盾。

**明确禁止**

- 在 `backtest` 上重新选币。
- 在 `backtest` 里重估 `best_h`。
- 因为回测难看就回头改 `train` 尺子。

**失败后的允许动作**

- 如果失败原因是执行参数过宽、费用吃掉 alpha，可以按记录清楚的规则回退到 `Test` 做一次受控策略冻结。
- 但这次回退不允许动 `Train` 冻结尺子，也不允许伪装成“只是修 bug”。

### 4.7 Holdout Validation

**核心问题**

最终冻结方案在最后一段完全未参与设计的窗口里，是否仍然没有翻向。

**为什么它必须保留到最后**

`Holdout` 的价值就在于它没有参与前面的定义、筛选和冻结。一旦用它来改参数，它就失去了“最终验证”的意义。

**必做事项**

- 复用 `Backtest` 冻结方案。
- 输出单日和合并窗口表现。
- 解释无交易、低触发或低样本是否属于正常现象。

**必备输出**

- `holdout_run_manifest.json`
- `holdout_backtest_compare.csv`
- `holdout_gate_decision.md`
- 每个 holdout 窗口下的 `portfolio_summary.parquet`、`trades.parquet` 等结果
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**晋级标准**

团队能够明确回答“冻结后的方案在最终窗口有没有方向翻转，是否出现明显漂移”。

**明确禁止**

- 用 `holdout` 调任何参数。
- 因为 `holdout` 不好看就改 symbol 白名单。
- 重新定义研究问题来解释 `holdout`。

**失败后的允许动作**

- 给出 `NO-GO`、`RETRY` 或 `child lineage` 判断。
- 不允许把 `holdout` 直接并入前面的 `test` 或 `backtest` 当作更多样本。

### 4.8 Promotion Decision

**核心问题**

组织上是否允许这条研究线进入下一步，而不是研究员个人是否“觉得还能做”。

**为什么要把它和证据阶段分开**

证据阶段回答的是“发生了什么”，而 `Promotion` 回答的是“组织怎么行动”。把这两件事分开，才能防止研究结论和组织治理混在一起。

**必备输出**

- `final_research_conclusion.md`
- `dashboard_index.md`
- `retry record` 或等价 gate 记录
- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

**允许的正式结论**

- `GO`
- `NO-GO`
- `RETRY`
- `CHILD LINEAGE`

**明确禁止**

- 只说“看起来还不错”，不给正式结论。
- 只保留最终通过的版本，不保留失败和回退过程。
- 在 `Backtest` 或 `Holdout` 已经触发异常收益复核的情况下，仍然在没有复核结论前直接给出 `GO`。

**Primary line 与 child lineage 的治理纪律**

正式研究里，`primary line` 和 `child lineage` 不是同义词。

- `primary line` 代表当前组织上默认消费、默认比较、默认汇报的正式基线；
- `child lineage` 代表某个新条件、新规则、新机制的受控试验线。

因此，默认应遵守下面这些纪律：

- 子线在某一个阶段更好，不自动等于可以替换主线；
- 若要替换主线，至少应在与主线相同的阶段口径下完成正式比较，且不能跳过 `holdout`；
- 如果子线只改善了 `backtest`，但 `holdout` 没有延续，则主线保持不动，子线继续作为候选线研究；
- 如果子线的结论更像“方向对，但 gate 太重”，下一步应在子线内部继续弱化、收窄或终止，而不是直接回写主线；
- 任何主线替换都应在 `Promotion Decision` 给出明确书面记录，而不是因为研究员主观偏好就静默切换。

这条纪律的目的不是保守，而是确保团队始终知道：当前正式基线是谁，候选增益来自哪条线，以及哪些仍然只是研究中的分支。

### 4.9 Shadow Admission

**核心问题**

这条研究线在已经完成 `vectorbt`、`backtrader` 双引擎回测验证之后，是否具备进入 `shadow` 的治理条件。

**为什么它不等于投产**

`Shadow` 只是更高一级的准入，不是最终上线批准。它要求研究证据之外，还要补足执行语义、撮合假设、容量、成本、稳定性和监控方案。

**至少应补充的内容**

- 对双引擎结果的一致性复核结论。
- 对 `Backtest` 阶段 `capacity_review.md` 的治理级复核，包括 shadow 期间的容量监控阈值、降额动作与回滚触发条件。
- 监控指标与回滚条件。
- shadow 期间的异常处理规则。

### 4.10 Canary / Production

**核心问题**

在小规模真实环境和最终投产审批下，这条策略是否仍然可接受。

这一阶段已经超出研究本身，属于更高等级的工程与风控治理。研究流程能做的是把策略送到“值得做这一步”的状态，而不是替代投产审批。

### 4.11 阶段最低晋级 Checklist

上面的章节解释了“为什么这样分阶段”，但真正重跑一条研究线时，还需要更硬的最低晋级门槛。

这张表是速查摘要，不替代 `docs/all-sops/workflow_stage_gates.yaml`。如果 checklist 与 YAML 之间出现不一致，默认以 YAML 中对应阶段的 `required_outputs / formal_gate / verdict_rules / rollback_rules` 为准。

下面这张表的作用不是替代专题细节，而是防止执行时出现“感觉差不多可以往下走”的口头晋级。

| 阶段 | 最低晋级 checklist |
| --- | --- |
| `Mandate` | 主问题已冻结；不研究什么已写清；时间窗和切分已冻结；Universe 已冻结；时间标签与无前视约定已冻结；字段分层和字段解释已写清；参数字典已写清；信号机制与表达式模板已冻结；公式的符号说明、研究含义和时间语义已写清；后续 `crowding / capacity review` 的比较口径、流动性代理与参与率边界已写清；`mandate.md / research_scope.md / time_split.json / parameter_grid.yaml` 已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Data Ready` | 基准腿覆盖审计已完成；dense 时间轴已生成；所有目标对象时间轴长度一致；QC 报告已生成；排除项已显式记录；`data_ready` gate 文档已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Signal Ready` | 字段合同已生成；参数身份已显式落地；`timeseries/` 已生成；覆盖摘要已生成；已明确引用上游 `Mandate` 表达式模板并完成实例化；信号 gate 文档已生成；没有越权做白名单或收益结论；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Train Calibration` | 训练阈值已冻结；质量过滤已冻结；参数 ledger 已保存；reject ledger 已保存；`train` gate 文档已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Test Evidence` | 使用的阈值来自 `Train`；正式 gate 与审计 gate 已记录；白名单或候选集已冻结；`crowding_review.md` 或等价证据已生成；`test_gate_decision.md` 已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Backtest Ready` | 输入白名单和交易规则来自上游冻结文件；若搜索了多套策略组合，则 execution / portfolio / risk overlay ledger 已保存；多层晋级预算已遵守或有明确豁免记录；`vectorbt / backtrader` 两套正式回测均已落地；收益与回撤基于正式资金曲线口径；`capacity_review.md` 已生成并说明 deployable capital、自冲击和成本吞噬边界；若出现异常高收益，`abnormal performance sanity check` 已完成且结论已写入 `backtest_gate_decision.md`；多引擎对照结论与 `backtest_gate_decision.md` 已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Holdout Validation` | 使用的交易规则未再修改；单窗口和合并窗口结果已落地；`holdout_gate_decision.md` 已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Promotion Decision` | 已形成正式结论；回退或 retry 理由已记录；正负结果都可追溯；若上游阶段触发过异常收益复核，则复核结论与证据链可追溯；`final_research_conclusion.md` 已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |
| `Shadow Admission` | 双引擎回测一致性已复核；`Backtest` 容量结论已做治理级复核；监控指标和回滚条件已生成；shadow gate 文档已生成；所有机器可读产物已登记到 `artifact_catalog.md`；所有字段都能追到 `field_dictionary.md` 或 `*_fields.md` |

任何阶段如果 checklist 里有一项答不上来，默认不晋级。

### 4.12 Gate 文档模板

为了避免不同研究线把 gate 文档写成完全不同风格，正式阶段 gate 文档至少必须包含下面这些字段。

这张模板表解决的是“gate 文档怎么写”，而 `docs/all-sops/workflow_stage_gates.yaml` 解决的是“每个阶段到底怎么判”。因此，具体 gate 文档中的字段、状态词、回退范围和下一阶段权限，必须能映射回 YAML 中对应阶段的 `verdict_rules / rollback_rules / downstream_permissions`，而不是只写一篇好看的总结。

如果某阶段没有单独 gate 文件，而是由阶段主文档兼任 gate 文档，也必须覆盖同样的信息。

| 字段 | 含义 |
| --- | --- |
| `stage` | 当前阶段名，例如 `signal_ready` |
| `stage_status` | 当前阶段状态，使用统一 gate 词汇表 |
| `decision_date_utc` | 决策时间 |
| `lineage_id` | 当前研究线标识 |
| `input_artifacts` | 本阶段使用的上游关键产物 |
| `output_artifacts` | 本阶段生成的关键产物 |
| `artifact_catalog` | 本阶段产物目录与 companion 字段说明映射文件 |
| `field_documentation` | 本阶段正式字段说明文档集合，例如 `field_dictionary.md` 或 `*_fields.md` |
| `frozen_scope` | 本阶段冻结了什么 |
| `decision_basis` | 为什么通过、失败或需要重试 |
| `rejected_items` | 被淘汰的对象、参数或分支 |
| `residual_risks` | 允许带到下一阶段的保留风险 |
| `sanity_check_triggered` | 是否触发异常结果复核；若未触发，写 `false` 并简述原因 |
| `sanity_check_scope` | 异常结果复核覆盖的检查项，例如前视、成本、异常 bar、收益集中度、多引擎 spot check |
| `sanity_check_conclusion` | 异常结果复核结论；若仍有未解释异常，不得写 `PASS` 或 `CONDITIONAL PASS` |
| `rollback_stage` | 如果失败或重试，应该回退到哪里 |
| `allowed_modifications` | 允许修改的范围 |
| `next_stage` | 允许进入的下一阶段 |

最关键的纪律是：

- gate 文档不能只写一句 `PASS`；
- 必须写清楚“凭什么过、冻结了什么、下一步不能改什么”；
- 必须写清楚本阶段的 `artifact_catalog` 和字段说明文档在哪里；
- 如果结果异常地好，必须写清楚是否触发了 `abnormal performance sanity check`、查了什么、结论是什么；
- 如果阶段结论是 `RETRY` 或 `PASS FOR RETRY`，`rollback_stage` 和 `allowed_modifications` 不能为空。

## 5. Artifact Contract 与目录规范

建议每条正式研究线都使用统一根目录，例如：

```text
outputs/<lineage_name>/
```

根目录下建议采用显式阶段编号：

```text
outputs/<lineage_name>/
├── 00_mandate/
├── 01_data_ready/
├── 02_signal_ready/
├── 03_train_freeze/
├── 04_test_evidence/
├── 05_backtest/
├── 06_holdout/
├── 07_promotion/
├── 08_shadow/
├── 09_canary_prod/
└── 99_run_manifest/
```

### 5.0 目录命名规则

为了保证总规范和专题研究都能共存，目录命名建议遵守下面的规则：

1. **优先使用标准阶段名**

```text
00_mandate/
01_data_ready/
02_signal_ready/
03_train_freeze/
04_test_evidence/
05_backtest/
06_holdout/
07_promotion/
08_shadow/
09_canary_prod/
99_run_manifest/
```

1. **如果需要保留专题语义，允许在标准阶段名前缀后追加后缀**

例如：

```text
01_data_ready_layer0_1s/
02_signal_ready_topic_c_1s/
```

而不建议只写：

```text
01_layer0_1s/
02_custom_signal_pack/
```

原因是后者在脱离上下文后不自解释，新成员很难一眼知道它属于哪个标准阶段。

1. **如果历史原因已经存在专题目录名**

则必须在该阶段 gate 文档中显式写出映射关系，例如：

- `01_layer0_1s` 对应 `Data Ready`
- `02_custom_signal_pack` 对应 `Signal Ready`

这样总规范和历史谱系才能对齐。

每个阶段都至少要有四类文件：

1. 机器可读配置
2. 机器可读结果
3. 人类可读结论
4. gate 决策与运行身份

建议统一的文件类型：

- `*.json` / `*.yaml` / `*.toml`
  用于冻结配置、运行清单、参数身份。
- `*.parquet` / `*.csv`
  用于结果表、ledger、覆盖报告、交易结果。
- `*.md`
  用于阶段结论、解释、gate 决策、回退说明。

### 5.1 参数身份

从 `Signal Ready` 开始，所有结果都应携带稳定、可逆、无歧义的参数身份，例如 `param_id`。

原则只有一个：不允许靠文件名猜，也不允许靠人脑记。

同时建议 `Signal Ready` 额外生成 `param_manifest.csv` 或等价清单，至少写清：

- 当前已经物化的 `param_id` 集合
- 每个 `param_id` 对应的核心参数值
- 本次物化范围是 `baseline`、`search_batch` 还是 `full_frozen_grid`

后续 `Train Calibration`、`Test Evidence`、`Backtest Ready` 只能消费这份清单里已经出现的 `param_id`，不允许在下游阶段再静默扩空间。

### 5.2 参数字典

参数身份解决的是“这是谁”，参数字典解决的是“它是什么”。

正式研究里，这两件事缺一不可：

- 没有参数身份，无法追踪是哪组结果。
- 没有参数字典，新成员无法理解这组结果在控制什么。

因此每条正式研究线至少必须同时具备：

- `parameter_grid.yaml`
  用于冻结候选范围和参数约束。
- `parameter_dictionary.md` 或等价章节
  用于解释参数含义、单位、作用层、默认值和不该在哪个阶段定死。

如果研究体量较小，也可以把参数字典直接并入 `mandate.md`，但不能省略。

同样的逻辑也适用于字段字典与公式解释：

- `field_dictionary.md` 或等价章节
  用于解释字段含义、字段层级、消费阶段和是否允许进入正式 schema。
- `formula_notes.md` 或等价章节
  用于解释公式符号、研究含义、参数映射和时间语义。

如果研究体量较小，也可以把这些解释直接并入 `mandate.md`，但不能省略。

#### Companion Field Documentation

参数字典和字段字典还不够，因为后续阶段会继续产出大量新的机器可读 artifact。

因此正式研究里，每个阶段都必须额外满足下面的 companion 文档制度：

- `artifact_catalog.md`
  - 必须列出本阶段所有关键产物；
  - 对每个产物写清文件名、用途、粒度、主键、消费者、是否机器可读；
  - 对每个机器可读产物，必须指向对应的 `field_dictionary.md` 或 `*_fields.md`。
- `field_dictionary.md` 或 `*_fields.md`
  - 必须解释该产物中的正式字段；
  - 至少包含字段名、类型、含义、单位、是否可空、空值语义、约束、所属层、下游消费阶段。

这条制度适用于所有阶段，不只适用于 `Mandate`。如果阶段较小，可以用一份 `field_dictionary.md` 覆盖全阶段；如果阶段较大，可以按产物拆分成多个 `*_fields.md`。但不允许没有 `artifact_catalog.md` 就直接丢给下游一堆 `csv / parquet / json`。

### 5.3 负结果保留

正式研究必须保留：

- 被拒绝的 symbol。
- 被淘汰的参数组合。
- 失败的 gate 记录。
- 回退和 retry 的原因。

如果团队只保留“最后通过的那个版本”，那就不是研究资产，而只是幸存者偏差的展示。

### 5.4 Run Manifest

`99_run_manifest/` 不是可有可无的归档目录，而是整条研究线的执行账本。

每个阶段至少应生成一个 `run_manifest.json` 或等价文件，最低字段包括：

| 字段 | 含义 |
| --- | --- |
| `stage` | 当前阶段名，例如 `signal_ready` |
| `lineage_id` | 研究线唯一标识 |
| `run_id` | 本次执行唯一标识 |
| `timestamp_utc` | 本次执行时间 |
| `input_dirs` | 上游输入目录 |
| `output_dir` | 当前输出目录 |
| `time_window` | 当前使用的正式时间窗或子窗口 |
| `param_id` | 当前参数身份；无参数阶段可写 `null` |
| `config_files` | 使用的配置文件列表 |
| `command` | 关键执行命令或脚本入口 |
| `git_revision` | 代码版本标识 |
| `upstream_artifacts` | 引用的上游关键产物 |
| `artifact_catalog` | 本阶段产物目录与字段说明映射文件 |
| `field_documentation` | 本阶段字段说明文档集合 |
| `notes` | 本次运行说明 |

如果阶段失败，也应保留 manifest，而不是只保留成功执行。

### 5.5 Frozen Handoff Spec

当某个阶段要把“冻结后的选择结果”交给下一个阶段时，建议额外生成 `frozen_spec.json` 或等价文件，而不是只在 Markdown 里口头描述。

典型场景：

- `Train -> Test`
  交付冻结后的阈值、regime 切点、质量门槛。
- `Test -> Backtest`
  交付冻结后的白名单、`best_h`、统计门槛和候选交易规则。
- `Backtest -> Holdout`
  交付冻结后的交易规则、symbol 集合、成本模型和风控规则。

推荐最低字段：

| 字段 | 含义 |
| --- | --- |
| `stage` | 产生该冻结文件的阶段 |
| `lineage_id` | 当前研究线标识 |
| `time_window` | 产生冻结决策所依据的窗口 |
| `param_id` | 冻结结果对应的参数身份 |
| `selected_symbols` | 冻结后的对象集合 |
| `selected_horizons` | 冻结后的 horizon 或等价验证参数 |
| `thresholds` | 冻结阈值 |
| `regime_rules` | 冻结的 regime 切分规则 |
| `trade_rules` | 冻结的交易规则；若 Stage 5 搜索了多套 execution 规则，这里应指向最终保留的规则身份或规则文件 |
| `fee_model` | 成本模型 |
| `risk_rules` | 风控规则；无则写 `null`，有则应明确哪些属于 `risk overlay`，哪些属于强制退出 |
| `execution_policy_id` | 最终保留的执行规则身份；无则写 `null` |
| `portfolio_policy_id` | 最终保留的组合/仓位规则身份；无则写 `null` |
| `upstream_artifacts` | 生成该冻结文件依赖的关键产物 |
| `artifact_catalog` | 本阶段产物目录与字段说明映射文件 |
| `field_documentation` | 本阶段字段说明文档集合 |

原则：

- 只要下一阶段需要“照单执行”，就不应只靠 Markdown 解释；
- 应同时给人类可读结论和机器可读冻结规范；
- `frozen_spec.json` 是下游阶段的输入合同，不是可有可无的附录。

### 5.6 标准阶段文件名建议

为了让不同研究线的目录尽量可搜索、可比对，建议每个阶段优先采用下面的标准文件名。

| 阶段 | 推荐 gate 文件 | 推荐冻结文件 |
| --- | --- | --- |
| `Mandate` | `mandate.md` 或 `mandate_gate_decision.md` | `time_split.json`、`parameter_grid.yaml` |
| `Data Ready` | `data_ready_gate_decision.md` | `data_contract.md` |
| `Signal Ready` | `signal_gate_decision.md` | `signal_fields_contract.md` |
| `Train Calibration` | `train_gate_decision.md` | `train_thresholds.json` 或 `frozen_spec.json` |
| `Test Evidence` | `test_gate_decision.md` | `frozen_spec.json` |
| `Backtest Ready` | `backtest_gate_decision.md` | `backtest_frozen_config.json` 或 `frozen_spec.json` |
| `Holdout Validation` | `holdout_gate_decision.md` | `holdout_run_manifest.json` |
| `Promotion Decision` | `final_research_conclusion.md` | `retry_record.*` |

如果专题研究需要更具体的文件名，可以在这个标准名基础上追加后缀，但不建议完全脱离标准名。

除此之外，所有阶段还应优先保留下列标准配套文件名：

- `artifact_catalog.md`
- `field_dictionary.md` 或按产物拆分的 `*_fields.md`

## 6. Review Gate 统一检查项

### 6.0 Gate 状态词汇表

为了避免不同研究线各写各的，建议正式 gate 文档统一使用下面这些状态词：

| 状态 | 含义 | 是否允许进入下一阶段 |
| --- | --- | --- |
| `PASS` | 当前阶段目标已满足 | 是 |
| `CONDITIONAL PASS` | 当前阶段主要目标满足，但附带保留事项，允许进入下一阶段 | 是，但必须把保留事项写清楚 |
| `PASS FOR RETRY` | 当前阶段允许受控回退或局部重试后继续 | 否，必须先按 retry 记录执行 |
| `RETRY` | 当前阶段失败，但属于受控可修复问题 | 否 |
| `NO-GO` | 当前阶段结论不支持继续推进 | 否 |
| `GO` | 这是 `Promotion` 或更高治理层的推进结论，不用于早期阶段 gate | 视治理层定义 |
| `CHILD LINEAGE` | 当前问题需要新谱系承接，不应在原线继续修改 | 否 |

约束：

- `PASS`、`CONDITIONAL PASS` 主要用于研究阶段 gate。
- `GO`、`NO-GO`、`CHILD LINEAGE` 更适合 `Promotion` 和更高治理层。
- 不建议自由发明新状态词，除非在文档里补全定义。
- 任何 `CONDITIONAL PASS` 都不能是“裸状态词”；对应 gate 文档必须显式写出 reservations / 保留事项，否则应视为 gate 说明不完整。

每次阶段晋级前，`Reviewer` 至少检查以下问题：

- 这一步的输入是否来自上一阶段冻结产物，而不是临时重算。
- 这一步是否留下了机器可读结果和人类可读结论。
- 是否存在前视、重估、偷改阈值、偷改白名单。
- 如果结果异常地好，是否已经完成 `abnormal performance sanity check`，并解释清楚收益来源、成本口径和多引擎一致性。
- 失败结果是否被保留。
- 这一步的结论到底是统计证据、策略证据还是执行证据。
- 如果要重试，是否写清楚 rollback stage、allowed modifications 和 retry reason。

如果这些问题回答不清楚，默认不晋级。

## 7. 回退、重试与 Child Lineage 规则

### 7.1 什么情况允许 retry

以下问题通常允许在原谱系做 controlled retry：

- 数据抽取 bug。
- 对齐或去重 bug。
- 信号实现 bug。
- 回测执行逻辑 bug。
- 已经明确写在上一阶段允许修改范围内的策略冻结调整。

前提是：

- 写清楚回退到哪个阶段。
- 写清楚允许修改什么。
- 写清楚为什么这不改变研究主问题。

### 7.2 什么情况必须开 child lineage

以下问题不应继续在原线修：

- 研究主问题改变。
- Universe 准入规则改变。
- 时间窗切分改变。
- 信号机制定义改变。
- 允许因子范围改变。
- 由原先的“信号研究”变成另一类策略逻辑。
- 原先只是 `audit evidence` 的辅助条件，被正式升级为 `symbol gate`、`state gate`、`regime gate`、仓位规则或持有期规则。

这类变化会改变原证据的解释边界，因此必须开新谱系。

### 7.3 什么情况应该直接 NO-GO

以下情况更适合明确终止，而不是继续优化：

- 独立 `test` 上结构不成立。
- `backtest` 和 `holdout` 连续翻向。
- alpha 薄到在合理成本假设下根本不可做。
- 数据质量缺陷决定性地破坏研究对象本身。

团队需要学会让失败正式落地，而不是默认继续修。

## 8. 团队执行清单

- 立项前：冻结研究问题、不研究项、Universe、时间窗、时间标签，以及实现栈和例外说明。
- 阶段结束前：确认机器可读配置、机器可读结果、人类可读结论、gate decision、`artifact_catalog.md` 与字段说明齐全，并保留 reject / fail 记录。
- 晋级前：确认当前阶段回答的问题、冻结边界、下一阶段禁止修改项，以及失败时的 `rollback_stage`。
- 进入 `shadow` 前：确认正式研究结论、双引擎一致性复核、容量审计、监控指标与回滚条件齐全。

## 9. 如何使用这份规范

团队使用时，建议一条研究线同时维护两类文档：

1. 通用 workflow 规范。
2. 该研究线自己的样板说明或专题手册。

前者负责统一阶段语言、artifact 契约和 gate 纪律；后者负责解释具体谱系怎样落地。总指南应尽量稳定，专题细节应尽量沉淀到谱系自己的 `outputs/<lineage_name>/` 阶段产物里。

## 10. 执行提示

重开一条研究线时，不必在总指南里再维护一套长模板。直接按本文件的标准顺序推进：

`Mandate -> Data Ready -> Signal Ready -> Train Calibration -> Test Evidence -> Backtest Ready -> Holdout Validation -> Promotion Decision -> Shadow Admission -> Canary / Production`

具体写法、字段定义和专题样板，应沉淀到谱系自己的阶段产物中；总指南只保留阶段 contract、artifact 要求、gate 语言和回退纪律。
