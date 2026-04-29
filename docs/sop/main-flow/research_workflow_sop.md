# 团队研究 Workflow 主规范

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-WORKFLOW-v2.0 |
| 日期 | 2026-03-27 |
| 状态 | Active |

---

## 0. 文档定位与优先级

本文档是**解释层**，不是 gate contract 真值。

| 文档 | 职责 |
|------|------|
| 本文档 | 解释阶段目的、指导思想、常见误区、artifact 治理逻辑 |
| `workflow_stage_gates.yaml` | Gate contract 真值：每阶段必须检查什么、formal gate 条件、verdict 规则 |
| 各阶段 `*_sop_cn.md` | 各阶段的详细操作流程 |

**冲突时以 `workflow_stage_gates.yaml` 为准**。

### Agent / Reviewer 核查顺序

1. 识别正在核查的阶段；
2. 读取 `workflow_stage_gates.yaml` 中该阶段的 contract；
3. 核对 `required_inputs / required_outputs / formal_gate / audit_only / verdict_rules / rollback_rules`；
4. 先判断 formal gate，再记录 audit-only 发现，最后给出统一 verdict。

### Repo 职责边界

QROS 约束的是正式研究流程与 artifact 治理，而不是把本仓库当作具体策略研究代码的承载体。

对于某条实际研究线，agent 应在当前研究仓中生成因子、检验、回测与验证实现；本规范只要求这些实现形成可审查、可复现、可追溯的正式产物，并通过对应 gate。空目录、占位文件或只有语义说明的文档，都不能被当作阶段完成。

从 `01_mandate` 开始，所有可执行阶段还必须在当前研究仓的 `outputs/<lineage_id>/program/` 下保留 lineage-local stage program。这里的 program 由 Codex 在当前 author lane 显式编写或刷新，QROS runtime 负责 freeze/review gate、程序合同校验、调用、产物验证与 provenance 记账，但不再直接把框架仓里的共享 builder 当作阶段完成来源，也不再后台静默生成默认 wrapper。共享代码可以复用到 `program/common/`，但真正的 stage entrypoint 必须留在当前 lineage；thin wrapper、framework builder shim 和 fixture/demo-only helper 都不能冒充真实研究流的阶段完成来源。

---

## 1. 指导思想

| 原则 | 含义 |
|------|------|
| **Hypothesis before results** | 先冻结研究问题，再看结果 |
| **Data contract before evidence** | 先确认数据可研究，再讨论 alpha |
| **Freeze first, verify later** | Train 定尺子 → Test 验证尺子 → Backtest/Holdout 验证可交易性。顺序不可逆 |
| **Separate evidence layers** | 统计证据（Test）、策略证据（Backtest）、执行证据（post-holdout observation）是三件独立的事 |
| **Artifact over memory** | 正式结论必须依赖 artifact，不依赖"谁记得" |
| **Controlled retry** | 允许重试，但必须受控、记账、可审计；实质变化必须开 child lineage |
| **Rust-first & efficient search** | 默认 Rust 实现栈；参数多时优先 coarse-to-fine，不做无计划暴力搜索 |
| **Companion field documentation** | 任何机器可读 artifact 必须同时有 `artifact_catalog.md` + `field_dictionary.md` |
| **Multiple testing awareness** | 参数搜索是多重假设检验，Test Evidence 阶段必须做数据挖掘校正 |
| **Regime stationarity awareness** | 跨窗口验证时须审计 regime 分布偏移，不把 regime 不匹配直接归因为策略失效 |
| **Route before stage contract** | 先冻结 research route，再让 `signal_ready / train / test / backtest` 按 route 分流语义 |

---

## 2. 个人研究职责视角

单人可以兼任所有职责，但**每个正式 gate 前必须显式切换视角**：

| 职责 | 核心责任 | 禁止 |
|------|----------|------|
| Explorer | 提出主问题、冻结边界 | 看到结果后悄悄改主问题 |
| Builder | 在研究仓落地数据、信号、统计、回测，并为当前阶段编写 lineage-local stage program | 用实现便利替代研究纪律 |
| Critic | 检查泄漏、样本污染、artifact 完整性 | 因结果好看就跳过审查 |
| Auditor | 给出 gate verdict，决定晋级/回退/开新谱系 | 把"再调一调"当默认动作 |
| Orchestrator | 维护阶段顺序、lineage、retry 记账，并只负责校验/调用 lineage-local stage program | 跳阶段、静默重试或直接代建阶段产物 |

---

## 3. 标准阶段流转

正式研究必须按顺序推进，**不允许跳阶段**。
在 `01_mandate` 冻结 `research_route` 之后，研究流程按 route 分叉：

```
00_idea_intake → 01_mandate
├─ time_series_signal → 02_tss_data_ready → 03_tss_signal_ready → 04_tss_train_freeze
│                    → 05_tss_test_evidence → 06_tss_backtest_ready → 07_tss_holdout_validation
└─ cross_sectional_factor → 02_csf_data_ready → 03_csf_signal_ready → 04_csf_train_freeze
                         → 05_csf_test_evidence → 06_csf_backtest_ready → 07_csf_holdout_validation
```

`time_series_signal` 的 TSS 主线含义是：**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不以 Rank IC / Top-Bottom / bucket monotonicity 作为主证据；这些指标属于 CSF 或审计上下文，不能替代 TSS 的单资产时间路径证据。

**注意**：`00_idea_intake` 是前置资格评估阶段，不属于正式研究管线。只有 `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` 且通过交互式确认后，才允许进入 `01_mandate`。

### 3.1 Executable-stage hard gate

从 `01_mandate` 开始，所有可执行阶段都遵守同一个不变量：

`freeze approval -> lineage-local program -> artifact build -> review closure`

Canonical program tree：

- route-neutral mandate：`outputs/<lineage_id>/program/mandate/`
- TSS 时序主线：`outputs/<lineage_id>/program/time_series_signal/<stage>/`
- CSF 主线：`outputs/<lineage_id>/program/cross_sectional_factor/<stage>/`
- 可复用共享代码：`outputs/<lineage_id>/program/common/`

每个 stage program 目录至少包含 `stage_program.yaml`、`README.md` 和 manifest 指向的 entrypoint。runtime 成功调用后，必须在对应阶段产物目录写出 `program_execution_manifest.json`，其中 `program_hash` 记录的是整个 `program_dir` 的 hash，而不是单个 `run_stage.py` 文件。共享 helper 只能作为库被 lineage-local entrypoint 调用，不能继续充当 framework-side completion fallback。

阶段产物目录的 canonical layout：

- `outputs/<lineage_id>/<stage>/author/draft/`
- `outputs/<lineage_id>/<stage>/author/formal/`
- `outputs/<lineage_id>/<stage>/review/request/`
- `outputs/<lineage_id>/<stage>/review/result/`
- `outputs/<lineage_id>/<stage>/review/closure/`

约束：

- downstream stage 只允许消费 `author/formal/`
- `artifact_catalog.md` 与 `field_dictionary.md` 归 `author/formal/`
- `stage_completion_certificate.yaml` 只允许位于 `review/closure/`

各阶段的详细操作规范见对应的 `*_sop_cn.md`。

---

## 4. 各阶段速览

### 4.0 Idea Intake（前置阶段）

**核心问题**：这个想法是否成熟到值得开始冻结研究边界？

**必须完成**：intake 访谈（observation / primary hypothesis / counter hypothesis / kill criteria）；6 维度 qualification 评分（observability / mechanism_plausibility / tradeability / data_feasibility / scoping_clarity / distinctiveness）；route assessment；scope canvas；gate decision。

**禁止**：访谈期间查看任何真实数据结果；counter_hypothesis 只是 primary hypothesis 的弱化版；GO_TO_MANDATE 后不经交互式确认直接生成 mandate。

**Gate Verdict**：`GO_TO_MANDATE` / `NEEDS_REFRAME` / `DROP`

**必备输出**：`idea_brief.md`, `observation_hypothesis_map.md`, `research_question_set.md`, `scope_canvas.yaml`, `qualification_scorecard.yaml`, `idea_gate_decision.yaml`, `artifact_catalog.md`

---

### 4.1 Mandate（00）

**核心问题**：这条研究线研究什么，不研究什么。

**必须冻结**：主问题、研究路线、时间窗切分、Universe 口径、允许字段族（含层级和消费阶段说明）、信号机制与表达式模板（含符号说明、时间语义、无前视约定）、参数边界与字典、容量/拥挤审计口径、实现栈。

**路线分叉**：`time_series_signal` 进入独立 `02_tss_data_ready -> 07_tss_holdout_validation` 主线；`cross_sectional_factor` 进入独立 `02_csf_data_ready -> 07_csf_holdout_validation` 流程。新 TSS lineage 不再把无前缀 `02_data_ready`、`03_signal_ready`、`04_train_freeze`、`05_test_evidence`、`06_backtest`、`07_holdout` 当作 canonical post-mandate 目录。

**禁止**：一边抽数据一边改 Universe；先扫结果再回写研究边界；未冻结 time_split 就看 test/backtest。

**必备输出**：`mandate.md`, `research_scope.md`, `time_split.json`, `parameter_grid.yaml`, `run_config.toml`, `artifact_catalog.md`, `field_dictionary.md`

**晋级标准**：研究问题、边界、禁止事项都写清楚。

---

### 4.2 TSS Data Ready（02）

**核心问题**：原始数据能否转换为单资产时间序列研究可用、可审计、可复用的数据基础层。

**必须完成**：冻结 `research_route = time_series_signal`；按单资产历史路径建立 time index；保留缺失与脏数据语义（不得静默填值）；生成 quality flags；审计 train/test/backtest/holdout 的样本充分性；输出 TSS 后续阶段可复用的数据基础层。

**禁止**：在原始层静默 forward-fill；混用 open_time/close_time 作主键；静默删样本不留质量标记；把横截面排序面板当作 TSS data ready。

**必备输出**：`time_index_manifest.json`, `asset_time_index.parquet`, `quality_flags.parquet`, `split_sample_adequacy_report.yaml`, `run_manifest.json`, `rebuild_tss_data_ready.py`, `artifact_catalog.md`, `field_dictionary.md`

**晋级标准**：能明确回答"这份数据为什么能研究"。

---

### 4.3 TSS Signal Ready（03）

**核心问题**：单资产时间序列研究对象是否被定义成统一、可复现、可比较的信号 / 事件字段合同。

**与 Mandate 的边界**：把 Mandate 已冻结的表达式模板正式实例化，不重新发明信号机制。如需改变核心主信号定义，必须回退到 Mandate 或开新谱系。

**必须完成**：固定信号字段定义、事件锚点、未来 horizon、方向语义和 `param_id` 集合；物化 `signal_panel.parquet` 与 `signal_event_panel.parquet`；生成 route inheritance 与覆盖证据；为 Train/Test 提供统一字段合同。

**Formal gate 状态**：

- `PASS`：必备 artifact 齐全，failed/skipped params = 0
- `CONDITIONAL PASS`：有 skipped params 或退化 symbol-param 覆盖
- `FAIL`：baseline 物化失败或关键 gate artifact 缺失

**禁止**：在 Train 里边算边改信号定义；在 Train 阶段扩充未在 TSS Signal Ready 物化过的 param_id；把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

**必备输出**：`signal_manifest.yaml`, `param_manifest.csv`, `signal_panel.parquet`, `signal_event_panel.parquet`, `route_inheritance_contract.yaml`, `run_manifest.json`, `artifact_catalog.md`, `field_dictionary.md`

---

### 4.4 TSS Train Freeze（04）

**核心问题**：如何在不接触未来窗口的前提下把尺子定下来。

**Train 只负责定尺子，不宣布胜利。**

**必须完成**：冻结分位阈值和 regime 切点（含样本特征记录）；信号可研究性过滤；参数粗筛（只排除荒谬区间，不选赢家）；完整 param_ledger 和 reject_ledger；搜索过程统计（total/passed/rejected/median/best/z-score）。

**禁止**：根据 test 结果回写 train 阈值；在 train 用收益最大化选最终参数；只保留通过参数不保留搜索轨迹。

**必备输出**：`tss_train_freeze.yaml`, `train_threshold_ledger.csv`, `train_variant_ledger.csv`, `train_variant_rejects.csv`, `run_manifest.json`, `artifact_catalog.md`, `field_dictionary.md`

详见：`04_tss_train_freeze_sop_cn.md`

---

### 4.5 TSS Test Evidence（05）

**核心问题**：冻结后的信号结构是否在独立样本里仍然成立。

**Test 只验证结构，不做收益最大化。**

**必须完成**：复用 train 冻结阈值（不重估）；在测试窗计算统计证据；冻结白名单/best_h；记录 formal gate 与 audit gate；完成多重检验校正（搜索 ≥ 20 时必须生成 `data_mining_adjustment.json`）；若 formal gate 直接引用 `t` 值、`p` 值、回归显著性或残差型证据，必须记录稳健推断口径或免做理由；若 formal gate 进一步依赖残差近似独立、原始 `OLS` 误差设定或“未见明显 serial correlation”这类判断，必须记录自相关诊断 protocol 或免做理由；若 formal gate 进一步依赖多变量回归中单个系数的符号、显著性或增量解释，必须记录多重共线性诊断 protocol 或免做理由；若 formal gate 进一步声称关系连续性、回归系数稳定性、lead-lag 结构或 threshold 机制在窗口间稳定延续，必须记录结构突变检验 protocol 或免做理由；若 formal gate 进一步依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，必须记录防虚假回归 protocol 或免做理由。

**禁止**：在 test 里重估 train 分位阈值；看了 backtest 再回写 test 白名单不做 retry 记账；临时新增 Mandate 中未声明的正式规则。

**必备输出**：`event_forward_return.parquet`, `signal_performance_summary.json`, `tss_test_gate_table.csv`, `tss_selected_variants_test.csv`, `split_threshold_attestation.yaml`, `selected_variant_membership_proof.csv`, `upstream_binding_digest_ledger.yaml`, `run_manifest.json`, `artifact_catalog.md`, `field_dictionary.md`

详见：`05_tss_test_evidence_sop_cn.md`

---

### 4.6 TSS Backtest Ready（06）

**核心问题**：冻结后的交易规则在独立 OOS 窗口里能否成立。

**必须完成 vectorbt + backtrader 双引擎，不允许只跑单一引擎。**

**必须完成**：只使用冻结候选集和白名单；正式资金曲线口径（不用 spread-unit）；双引擎对照（`semantic_gap` 记录）；异常高收益强制复核（前视/成本/数据质量/收益集中度/多引擎 spot check）；晋级预算控制；容量定量化分析（市场冲击模型、AUM-Sharpe 衰减曲线、参与率分析）。

**异常收益复核未完成前，不允许 PASS 或 CONDITIONAL PASS，不允许进入 Holdout。**

**禁止**：在 backtest 重新选币；重估 best_h；因回测难看就回头改 train 尺子。

**必备输出**：`strategy_contract.yaml`, `engine_compare.csv`, `position_timeseries.parquet`, `trade_ledger.csv`, `tss_backtest_gate_table.csv`, `run_manifest.json`, `artifact_catalog.md`, `field_dictionary.md`

详见：`06_tss_backtest_ready_sop_cn.md`

---

### 4.7 TSS Holdout Validation（07）

**核心问题**：最终冻结方案在最后一段完全未参与设计的窗口里，是否仍然没有翻向。

**Holdout 的价值就在于它没有参与前面的任何定义、筛选和冻结。**

**必须完成**：复用 backtest 冻结方案（照单执行）；滚动 OOS 一致性检查（3-5 个子窗口，≥60% 方向一致）；regime 平稳性审计；跨阶段性能退化追踪；若 verdict 依赖“结构仍连续”或“结果退化只是 regime 不匹配而非机制断裂”的判断，必须记录结构突变检验 protocol 或免做理由。

**禁止**：用 holdout 调任何参数；因 holdout 不好看就改 symbol 白名单；重新定义研究问题；把 holdout 并入 test/backtest。

**必备输出**：`tss_holdout_run_manifest.json`, `holdout_signal_diagnostics.parquet`, `holdout_event_compare.parquet`, `holdout_backtest_compare.parquet`, `artifact_catalog.md`, `field_dictionary.md`

详见：`07_tss_holdout_validation_sop_cn.md`

---

## 5. 最低晋级 Checklist（速查）

> 详细 checklist 在各阶段 SOP 文档中。以下为速查摘要，与 `workflow_stage_gates.yaml` 出现不一致时以 YAML 为准。

| 阶段 | 最低晋级要点 |
|------|-------------|
| Idea Intake | observation/primary hypothesis/counter hypothesis/kill criteria 已写明；6 维度 scorecard 已完成（每维度有 evidence + kill_reason）；idea_gate_decision.yaml 已生成；verdict == GO_TO_MANDATE 时 approved_scope 非空；访谈期间未查看真实数据结果 |
| Mandate | 主问题/时间窗/Universe/字段分层/参数字典/信号表达式模板已冻结；artifact_catalog + field_dictionary 已生成 |
| TSS Data Ready | 单资产 time index / quality flags / split adequacy 已完成；artifact_catalog + field_dictionary 已生成 |
| TSS Signal Ready | signal/event schema、param_id、route inheritance 已冻结；未越权做统计显著性或收益结论 |
| TSS Train Freeze | 阈值、quality filters、variant ledger、reject ledger 已冻结；未接触 test/backtest/holdout |
| TSS Test Evidence | 阈值来自 Train；event forward return、performance summary、selected variants 已冻结；未回写上游 |
| TSS Backtest Ready | 策略合同来自上游冻结；engine_compare、position_timeseries、trade_ledger 已生成；异常收益复核已完成 |
| TSS Holdout Validation | 冻结方案照单执行；holdout signal/event/backtest comparison 已生成；失败处置规则已记录 |
## 6. Gate 状态词汇表

| 状态 | 含义 | 是否进入下一阶段 |
|------|------|-----------------|
| `PASS` | 当前阶段目标已满足 | 是 |
| `CONDITIONAL PASS` | 主要目标满足，有保留事项（必须写清） | 是 |
| `PASS FOR RETRY` | 允许受控回退后继续 | 否（先按 retry 记录执行） |
| `RETRY` | 失败，但属于受控可修复问题 | 否 |
| `NO-GO` | 结论不支持继续推进 | 否 |
| `CHILD LINEAGE` | 需要新谱系承接，不应在原线继续修改 | 否 |

**CONDITIONAL PASS 必须显式写出保留事项**，不能是裸状态词。

---

## 7. Artifact Contract

### 7.1 每阶段必须有四类文件

1. 机器可读配置（`*.json / *.yaml / *.toml`）
2. 机器可读结果（`*.parquet / *.csv`）
3. 人类可读结论（`*.md`）
4. Gate 决策与运行身份（gate_decision.md + run_manifest.json）

### 7.2 Companion Field Documentation 制度

每个阶段都必须同时生成：

- `artifact_catalog.md`：列出所有产物，每个机器可读产物必须指向对应字段说明；
- `field_dictionary.md`（或按产物拆分的 `*_fields.md`）：逐项解释机器产物中的字段（字段名、类型、含义、单位、是否可空、约束、消费阶段）。

**缺少以上任一，默认不能 PASS 或 CONDITIONAL PASS。**

### 7.3 参数身份

从 Signal Ready 开始，所有结果须携带稳定、可逆、无歧义的 `param_id`。不允许靠文件名猜，不允许靠人脑记。

### 7.4 目录结构建议

```
outputs/<lineage_name>/
├── 01_mandate/
├── 02_tss_data_ready/
├── 03_tss_signal_ready/
├── 04_tss_train_freeze/
├── 05_tss_test_evidence/
├── 06_tss_backtest_ready/
├── 07_tss_holdout_validation/
└── 99_run_manifest/
```

目录命名优先使用标准阶段名，如需专题后缀则追加（例如 `02_tss_data_ready_layer0_1s/`），不建议完全脱离标准名。

### 7.5 负结果保留

必须保留：被拒绝的 symbol、被淘汰的参数组合、失败的 gate 记录、回退和 retry 的原因。只保留"最后通过的版本"不是研究资产，是幸存者偏差的展示。

---

## 8. 回退、重试与 Child Lineage

| 情况 | 处置方式 |
|------|----------|
| 数据 bug、实现 bug、执行逻辑 bug | 允许 controlled retry，须写清 rollback_stage、allowed_modifications、不改变研究主问题的理由 |
| 研究主问题、Universe、时间窗、信号机制、允许字段族实质变化 | 必须开 child lineage |
| 独立 test 结构不成立、backtest/holdout 连续翻向、成本假设下根本不可做 | 应给出 NO-GO |
| Audit evidence 中的辅助条件要升级为正式 gate 规则 | 必须开 child lineage |

---

## 9. Gate 文档最低字段

| 字段 | 含义 |
|------|------|
| `stage` | 当前阶段名 |
| `stage_status` | 使用统一 gate 词汇表 |
| `decision_date_utc` | 决策时间 |
| `lineage_id` | 研究线标识 |
| `input_artifacts` | 上游关键产物 |
| `output_artifacts` | 本阶段生成的关键产物 |
| `artifact_catalog` | 产物目录与字段说明映射文件 |
| `field_documentation` | 字段说明文档集合 |
| `frozen_scope` | 本阶段冻结了什么 |
| `decision_basis` | 通过/失败/重试的理由 |
| `rejected_items` | 被淘汰的对象、参数或分支 |
| `residual_risks` | 允许带到下一阶段的保留风险 |
| `sanity_check_triggered` | 是否触发异常结果复核（未触发写 false + 简述原因） |
| `sanity_check_conclusion` | 复核结论（仍有未解释异常时不得写 PASS） |
| `rollback_stage` | 失败时回退到哪里 |
| `allowed_modifications` | 允许修改的范围 |
| `next_stage` | 允许进入的下一阶段 |

**Gate 文档不能只写一句 PASS**。必须写清楚：凭什么过、冻结了什么、下一步不能改什么、artifact_catalog 和字段说明在哪里。

---

## 10. 执行提示

重开一条研究线时，直接按标准阶段顺序推进，具体写法和字段定义沉淀到谱系自己的产物中。

总指南只保留阶段 contract、artifact 要求、gate 语言和回退纪律；细节由各阶段 SOP（`*_sop_cn.md`）和谱系自己的阶段产物承接。
