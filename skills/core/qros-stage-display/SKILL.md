---
name: qros-stage-display
description: Public, user-triggered display guidance for mandate + CSF stages. Use only when the user explicitly asks to display or summarize a covered stage.
---

# QROS Stage Display Guidance

## Purpose

这是一个**公共展示指导 skill**。

它的目标不是推进 stage，也不是自动出 HTML，而是在用户明确要求时，指导 agent：

- 这一阶段**应该展示什么**
- 应该分成哪些 summary blocks
- 适合用哪些图表 / 表格 / 可视化
- 展示时应该提出哪些 interpretation questions
- 哪些内容不应该混进这一阶段的展示里

## Trigger Boundary

只在用户**明确提出**类似请求时使用：

- “展示一下这一阶段”
- “总结一下 mandate”
- “把 csf_data_ready 做成展示稿”
- “这一阶段应该怎么展示”

## Hard Non-goals

这个 skill：

- **不是** stage orchestration 的一部分
- **不是** mandatory gate
- **不会**自动在 review 结束后触发
- **不会**恢复 `*_display_pending`
- **不会**定义或执行 runtime HTML renderer
- **不会**接管 data acquisition subsystem
- **不会**替代 formal review closure

它是一个**guidance skill**，不是 display runtime。

## Scope (v1)

当前第一版只覆盖：

- `mandate`
- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`

当前第一版**不覆盖** mainline 的：

- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`

## Shared Display Philosophy

展示一个阶段时，默认遵守：

1. 先回答：**这个阶段冻结了什么**
2. 再回答：**这些冻结内容为什么重要**
3. 再回答：**当前最关键的风险或不确定性是什么**
4. 再回答：**下一阶段将继承什么边界**

默认输出结构建议：

1. `Stage Intent And Contract Boundary`
2. `What Was Frozen`
3. `Key Evidence / Diagnostics`
4. `Risks / Caveats`
5. `Downstream Implications`

如果用户只要简版，则压缩成：

- `What this stage locked in`
- `What evidence matters most`
- `What the next stage inherits`

## Rendering / Style Defaults

### Default Output Medium
- 默认直接输出 `HTML`

### Page Positioning
- 默认页面定位是：`dashboard + 报告页结合`
- 不是纯 dashboard
- 也不是纯长文报告

### Visual Style
- 默认风格：`极简投研风`
- 白底 / 浅底
- 高信息密度
- 少装饰，靠标题层级、留白、强调色和信息结构区分重点

### Layout
- 默认布局：`顺序阅读式`
- 从上到下按 section 展开
- 图表穿插在各 section 中
- 不采用“KPI 卡片先堆在最上面”的 dashboard-first 结构

### Text / Chart Ratio
- 默认图表与文字 roughly `1:1`
- 不是“只有图表，文字只是脚注”
- 也不是“长文报告里偶尔插一张图”

### Default Chart Strategy
- 默认允许正式图表库
- 图表是主角之一，而不是只做静态附图
- 默认图表库：`Plotly + 自定义极简主题`
- Plotly 负责交互图表，主题层负责去掉默认工具面板感

### Shared HTML Shell
- 所有阶段共用同一套 `极简投研风 HTML shell`
- 统一：
  - 页面宽度
  - section 标题层级
  - 表格风格
  - 图表卡片风格
  - 风险 / warning / caveat 提示样式
- 每个阶段只替换：
  - block 内容
  - 字段
  - 图表类型

### When To Downshift
- 如果当前阶段证据更多是 contract / rule / boundary，而不是数值序列，优先：
  - table
  - matrix
  - checklist
  - schematic
- 不要为了“像 dashboard”硬塞无意义图表

## Common Evidence Hints

v1 的重点是“展示什么”，不是“完整取数系统”。

如果需要取证据，优先查看该 stage 目录下：

- `artifact_catalog.md`
- `field_dictionary.md`
- `*_gate_decision.md`
- `stage_completion_certificate.yaml`
- stage-specific machine artifacts

但不要把这个 skill写成“必须从哪些文件精确提取哪些字段”的数据访问合同。

---

## Stage: `mandate`

### Core Review Purpose
- 治理复核
- 快速理解
- 判断是否值得进入下一阶段

### 60-Second Understanding Goal
- 研究对象到底是什么
- 冻结了哪些边界不能改
- 数据 / 时间口径是什么

### Core Blocks
1. `Research Object / Problem Statement`
2. `Frozen Boundaries`
3. `Data / Time Contract`

### Optional Block
- `Why This Mandate Matters For Downstream`

### Display Form Recommendation
- `Research Object / Problem Statement`：一句话定义 + 5 行摘要表
- `Frozen Boundaries`：boundary table + do/don't checklist
- `Data / Time Contract`：contract table + time split schematic

### Block: `Research Object / Problem Statement`
#### Must-show fields
- `research_question`
- `primary_hypothesis`
- `market / universe`
- `research_route`
- `target_task`

#### Recommended charts / tables / visuals
- one-sentence stage definition
- 5-row summary table
- optional route note card

#### Interpretation questions
- 这条 mandate 到底要研究什么？
- 它研究的是哪个市场 / universe / task？
- 为什么它值得被单独立项？

#### Stage-Specific Do / Don’t Rules
- **Do:** 先让人 30 秒内看懂“研究对象是什么”
- **Do:** 把 `research_route` 直接露出来，不要埋在长文里
- **Don't:** 用大段叙述替代核心字段表
- **Don't:** 提前混入 signal / train / backtest 结论

### Block: `Frozen Boundaries`
#### Must-show fields
- `excluded_routes`
- `scope_contract`
- `execution_constraints`
- `must_reuse_constraints`
- `change_requires_relineage`

#### Recommended charts / tables / visuals
- frozen-boundary table
- do/don't checklist
- change-trigger warning box

#### Interpretation questions
- 下游最不能乱改的边界是什么？
- 哪些改动一旦发生就不再是同一条线？
- 现在有哪些东西是“明确不做”的？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把不可改边界和可回退边界分开写
- **Do:** 明确 `change_requires_relineage`
- **Don't:** 把 scope 和 execution 约束混成一句笼统描述
- **Don't:** 省略 `excluded_routes`

### Block: `Data / Time Contract`
#### Must-show fields
- `data_source`
- `bar_size`
- `time_split`
- `timestamp_semantics`
- `holding_horizons / evaluation horizons`

#### Recommended charts / tables / visuals
- data/time contract table
- split timeline schematic
- horizon summary strip

#### Interpretation questions
- 这条线的数据口径到底是什么？
- 时间切分是否已经冻结清楚？
- 下游会继承哪些时间语义？

#### Stage-Specific Do / Don’t Rules
- **Do:** 让人一眼看到 `data_source + bar_size + time_split`
- **Do:** 把时间语义和 horizon 关系写清楚
- **Don't:** 只写“按 mandate 冻结”而不把字段展开
- **Don't:** 把数据口径做成纯文字埋点

---

## Stage: `csf_data_ready`

### Core Review Purpose
- 看清 panel base 是否真的搭好
- 判断 coverage / eligibility / taxonomy 是否可信
- 决定这套底座是否足够支撑进入 `csf_signal_ready`

### 60-Second Understanding Goal
- panel base 到底长什么样
- coverage / eligibility / taxonomy 是否可信
- shared feature base 是否已 ready（附加）

### Core Blocks
1. `Panel Base Shape`
2. `Coverage / Eligibility / Taxonomy Trust`

### Optional Block
- `Shared Feature Base Ready For Signal`

### Display Form Recommendation
- `Panel Base Shape`：schema-style contract table + compact panel summary card
- `Coverage / Eligibility / Taxonomy Trust`：coverage table/heatmap + eligibility/taxonomy trust matrix

### Block: `Panel Base Shape`
#### Must-show fields
- `panel_primary_key`
- `asset_universe_definition`
- `panel_frequency`
- `cross_section_time_key`
- `coverage_rule`
- `panel_manifest_summary`

#### Recommended charts / tables / visuals
- panel contract table
- universe summary table
- panel manifest summary card

#### Interpretation questions
- 这个面板到底是按什么主键组织的？
- cross-section 是在什么时间点被定义的？
- downstream signal 看到的基础面板到底长什么样？

#### Stage-Specific Do / Don’t Rules
- **Do:** 先把主键 / frequency / universe 讲清楚
- **Do:** 明确 `coverage_rule`
- **Don't:** 把 panel 讲成泛泛的数据集概念
- **Don't:** 只列文件名不解释结构

### Block: `Coverage / Eligibility / Taxonomy Trust`
#### Must-show fields
- `coverage_summary`
- `coverage_gaps / weak slices`
- `eligibility_base_rule`
- `eligibility_exclusion_summary`
- `taxonomy_reference / version`
- `group_neutral_readiness`

#### Recommended charts / tables / visuals
- coverage summary table or heatmap
- eligibility funnel table
- taxonomy/version trust table

#### Interpretation questions
- 这套底座哪里最可信，哪里最脆弱？
- eligibility 到底筛掉了什么？
- taxonomy / group-neutral 准备程度是否足够？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把 coverage gap 和 exclusion 分开写
- **Do:** 显式露出 taxonomy version
- **Don't:** 把 taxonomy 准备程度说成默认理所当然
- **Don't:** 隐藏 weak slices

---

## Stage: `csf_signal_ready`

### Core Review Purpose
- 让人看懂这个 factor / signal 到底在表达什么
- 让人看懂哪些处理步骤已经冻结
- 让人判断 train 是否只应该沿着允许的轴继续走

### 60-Second Understanding Goal
- factor identity / factor role 是什么
- transform / neutralization / ranking 逻辑是什么
- 哪些东西在 signal_ready 已经固定，train 不能回写

### Core Blocks
1. `Factor Identity / Role`
2. `Transform / Neutralization / Ranking Logic`

### Optional Block
- `What Is Frozen For Train`

### Display Form Recommendation
- `Factor Identity / Role`：identity card + short rationale table
- `Transform / Neutralization / Ranking Logic`：pipeline diagram + rule matrix
- `What Is Frozen For Train`：governable vs non-governable split table

### Block: `Factor Identity / Role`
#### Must-show fields
- `factor_id`
- `factor_name / short label`
- `factor_role`
- `economic intuition / mechanism`
- `target cross-section`
- `expected directional meaning`

#### Recommended charts / tables / visuals
- factor identity card
- mechanism summary table
- directionality note card

#### Interpretation questions
- 这个 factor 到底在测什么？
- 它在研究线上扮演什么角色？
- 它应该怎样被解释，而不是被误读？

#### Stage-Specific Do / Don’t Rules
- **Do:** 让人先看懂 factor identity，再看算法细节
- **Do:** 明确 `expected directional meaning`
- **Don't:** 只写数学变换，不写 economic intuition
- **Don't:** 把 factor role 写成含混标签

### Block: `Transform / Neutralization / Ranking Logic`
#### Must-show fields
- `raw_factor_inputs`
- `transform_pipeline`
- `neutralization_policy`
- `ranking_method / bucket_rule`
- `score_combination_formula`
- `output_signal_definition`

#### Recommended charts / tables / visuals
- factor pipeline diagram
- transform / neutralization / ranking rule matrix
- output signal definition table

#### Interpretation questions
- raw inputs 如何变成最终 signal？
- 哪些处理中性化 / 排序规则是治理关键？
- 最终输出给下游的 signal 语义到底是什么？

#### Stage-Specific Do / Don’t Rules
- **Do:** 用 pipeline 形式展示加工路径
- **Do:** 把 neutralization 与 ranking 逻辑拆开写
- **Don't:** 把多个步骤压成一句“标准化处理”
- **Don't:** 省略最终 output signal definition

### Block: `What Is Frozen For Train`
#### Must-show fields
- `frozen_signal_contract_reference`
- `non_governable_axes_after_signal`
- `train_governable_axes`
- `forbidden_train_changes`
- `downstream_train_input_manifest`

#### Recommended charts / tables / visuals
- governable vs non-governable split table
- downstream train input checklist

#### Interpretation questions
- 哪些东西 train 还能调？
- 哪些东西 train 再碰就越界了？
- downstream train 真实会拿到什么？

#### Stage-Specific Do / Don’t Rules
- **Do:** 清楚分出 governable / non-governable
- **Do:** 把 forbidden changes 写得醒目
- **Don't:** 用模糊措辞掩盖冻结边界
- **Don't:** 让 train scope 看起来比 signal-ready 更宽

---

## Stage: `csf_train_freeze`

### Core Review Purpose
- 看清 train 阶段到底冻结了哪些治理轴
- 看清哪些 threshold / preprocess / quality 还可动，哪些不能动
- 看清 `csf_test_evidence` 会继承什么

### 60-Second Understanding Goal
- train window / training regime 是怎么定的
- threshold / preprocess / quality filter 的治理边界是什么
- 哪些参数被保留、哪些被拒绝，以及为什么（附加）

### Core Blocks
1. `Train Window / Regime Policy`
2. `Threshold / Preprocess / Quality Governance`

### Optional Block
- `Parameter Keep / Reject Ledger`

### Display Form Recommendation
- `Train Window / Regime Policy`：timeline + regime policy table
- `Threshold / Preprocess / Quality Governance`：governance table + threshold summary strip
- `Parameter Keep / Reject Ledger`：keep/reject summary ledger

### Block: `Train Window / Regime Policy`
#### Must-show fields
- `train_window_definition`
- `window_split_logic`
- `regime_definition`
- `regime_segmentation_rule`
- `sampling / rebalance cadence`
- `train_period_rationale`

#### Recommended charts / tables / visuals
- train window timeline
- regime policy table
- cadence summary strip

#### Interpretation questions
- train 到底在什么窗口上估计？
- regime 是怎么切分的？
- 为什么这个 train period 合理？

#### Stage-Specific Do / Don’t Rules
- **Do:** 用 timeline 明确窗口边界
- **Do:** 把 regime segmentation rule 说清楚
- **Don't:** 把 train window 描述成模糊时期
- **Don't:** 隐藏 sampling / rebalance cadence

### Block: `Threshold / Preprocess / Quality Governance`
#### Must-show fields
- `threshold_contract_summary`
- `preprocess_rules`
- `quality_filters`
- `governable_axes`
- `non_governable_axes`
- `threshold_change_guardrail`

#### Recommended charts / tables / visuals
- threshold governance table
- preprocess / quality filter summary table
- governable vs non-governable matrix

#### Interpretation questions
- 这个阶段哪些治理尺子已经冻住？
- 哪些东西还能调，哪些不能再动？
- quality filter 与 threshold 的关系是什么？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把 threshold / preprocess / quality 分层写
- **Do:** 明确 `threshold_change_guardrail`
- **Don't:** 把 governable axes 说成全开放
- **Don't:** 混淆 preprocess 与 quality governance

---

## Stage: `csf_test_evidence`

### Core Review Purpose
- 判断 formal gate 证据是否足够进入 `csf_backtest_ready`
- 判断 admissibility 与 audit 是否被混淆
- 看清 downstream backtest 会继承哪些冻结对象

### 60-Second Understanding Goal
- formal gate 到底凭什么 PASS
- 哪些结果是 admissibility，哪些只是 audit 信息
- backtest 阶段会真正拿走什么冻结对象

### Core Blocks
1. `Formal Gate Evidence`
2. `Admissibility vs Audit Boundary`

### Optional Block
- `Frozen Outputs For Backtest`

### Display Form Recommendation
- `Formal Gate Evidence`：formal gate table + metric strip by horizon
- `Admissibility vs Audit Boundary`：two-column boundary table + selected output summary

### Block: `Formal Gate Evidence`
#### Must-show fields
- `formal_gate_summary`
- `core_test_metrics`
- `pass_thresholds / gate_rules`
- `evidence_by_horizon`
- `winning / accepted configurations`
- `residual_uncertainty_note`

#### Recommended charts / tables / visuals
- formal gate table
- evidence-by-horizon metric strip
- accepted configuration summary table

#### Interpretation questions
- 为什么 formal gate 可以 PASS？
- 哪些核心指标真正决定了通过？
- 哪些不确定性仍然存在？

#### Stage-Specific Do / Don’t Rules
- **Do:** 先讲清 formal gate 逻辑，再讲具体配置
- **Do:** 把 horizon 维度露出来
- **Don't:** 只报一堆指标，不解释通过规则
- **Don't:** 把 accepted configurations 当成默认理所当然

### Block: `Admissibility vs Audit Boundary`
#### Must-show fields
- `admissibility_summary`
- `selected_symbols / selected slices`
- `audit_findings_summary`
- `non_blocking_observations`
- `formal_vs_informational_boundary_note`
- `backtest_entry_implication`

#### Recommended charts / tables / visuals
- admissibility summary table
- audit findings table
- formal vs informational boundary callout

#### Interpretation questions
- 哪些东西是真正 gating 的？
- 哪些只是补充审计信息？
- backtest 到底会继承什么？

#### Stage-Specific Do / Don’t Rules
- **Do:** 显式区分 formal 与 informational
- **Do:** 把 selected symbols / slices 放在 admissibility 语境下展示
- **Don't:** 把 audit 发现写成 formal blocker
- **Don't:** 模糊 `backtest_entry_implication`

---

## Stage: `csf_backtest_ready`

### Core Review Purpose
- 确认 downstream backtest 要遵守哪些 execution / portfolio / risk 规则
- 确认 engine contract 与实现边界是否冻结清楚
- 确认 holdout 前最脆弱的假设是什么（附加）

### 60-Second Understanding Goal
- 交易规则 / 组合规则 / 风险叠加到底是什么
- engine contract 到底固定了什么
- 进入 holdout 前最关键的风险假设是什么

### Core Blocks
1. `Execution / Portfolio / Risk Policy`
2. `Engine Contract`

### Optional Block
- `Fragility / Capacity / Holdout Watchpoints`

### Display Form Recommendation
- `Execution / Portfolio / Risk Policy`：policy matrix + guardrail summary
- `Engine Contract`：engine comparison matrix + assumption table
- `Fragility / Capacity / Holdout Watchpoints`：watchlist card

### Block: `Execution / Portfolio / Risk Policy`
#### Must-show fields
- `execution_policy_summary`
- `portfolio_policy_summary`
- `risk_overlay_summary`
- `rebalance / turnover constraints`
- `positioning / neutrality rule`
- `policy_guardrails`

#### Recommended charts / tables / visuals
- execution / portfolio / risk policy matrix
- turnover / neutrality summary table
- guardrail callout box

#### Interpretation questions
- backtest 执行到底按什么规则跑？
- 组合与风险层面有哪些明确 guardrails？
- 哪些规则属于不能碰的 execution contract？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把 execution / portfolio / risk 三者拆开写
- **Do:** 明确 neutrality / positioning 规则
- **Don't:** 把风控写成附带说明
- **Don't:** 让 policy guardrails 埋没在长文里

### Block: `Engine Contract`
#### Must-show fields
- `engine_contract_summary`
- `engine_compare_scope`
- `fill / slippage / fee assumptions`
- `simulation boundary assumptions`
- `engine_consistency_rule`
- `reproducibility_reference`

#### Recommended charts / tables / visuals
- engine contract matrix
- fee / slippage assumption table
- reproducibility reference block

#### Interpretation questions
- engine 层到底冻结了哪些假设？
- engine compare 的 scope 到哪里为止？
- 这套回测 contract 如何被复现？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把 fee/slippage/fill assumptions 明确露出
- **Do:** 说明 engine consistency rule
- **Don't:** 把 engine contract 简化成“两个引擎都跑了”
- **Don't:** 漏掉 reproducibility reference

---

## Stage: `csf_holdout_validation`

### Core Review Purpose
- 判断 holdout 究竟在验证什么，而不是重复 backtest
- 判断 drift / stability 信号说明了什么
- 判断 failure governance / rollback / child-lineage 条件是什么（附加）

### 60-Second Understanding Goal
- holdout window / reuse rule 到底是什么
- 结果更像 validation 成功，还是 drift 信号增强
- 什么条件下必须 rollback / child lineage

### Core Blocks
1. `Holdout Window / Reuse Contract`
2. `Drift / Stability Interpretation`

### Optional Block
- `Failure Governance`

### Display Form Recommendation
- `Holdout Window / Reuse Contract`：window schematic + reuse contract table
- `Drift / Stability Interpretation`：consistency summary + drift judgement card
- `Failure Governance`：trigger matrix

### Block: `Holdout Window / Reuse Contract`
#### Must-show fields
- `holdout_window_definition`
- `window_isolation_rule`
- `reuse_contract_summary`
- `frozen_inputs_reused`
- `forbidden_changes_in_holdout`
- `validation_scope_note`

#### Recommended charts / tables / visuals
- holdout window schematic
- reuse contract table
- forbidden changes warning box

#### Interpretation questions
- holdout 到底验证的是哪一段窗口？
- 哪些 frozen inputs 被直接复用？
- holdout 明确不允许改什么？

#### Stage-Specific Do / Don’t Rules
- **Do:** 先把 holdout window 与 reuse boundary 讲清楚
- **Do:** 明确 `forbidden_changes_in_holdout`
- **Don't:** 把 holdout 描述成 backtest 的延长段
- **Don't:** 模糊 window isolation rule

### Block: `Drift / Stability Interpretation`
#### Must-show fields
- `holdout_vs_backtest_consistency_summary`
- `drift_signal_summary`
- `stability_score / stability_judgement`
- `direction_flip / regime_shift_note`
- `key_failure_or_warning_patterns`
- `decision_readiness_summary`

#### Recommended charts / tables / visuals
- consistency summary table
- drift judgement card
- warning pattern summary table

#### Interpretation questions
- 当前结果更像 validation 成功还是 drift 增强？
- 最大的不稳定性信号是什么？
- 这条线现在是否具备 decision-readiness？

#### Stage-Specific Do / Don’t Rules
- **Do:** 把 validation 与 drift 两种解释并列展示
- **Do:** 让 stability judgement 可被快速读取
- **Don't:** 只给结果数字不解释 drift meaning
- **Don't:** 把 rollback/child-lineage 风险隐到脚注里

---

## Output Guidance

如果用户说“做成展示稿”，默认输出可采用：

1. `标题`
2. `阶段一句话定义`
3. `2~3 个主干块`
4. `每块 2~4 个 bullet`
5. `每块 1 组推荐字段`
6. `每块 1 个推荐图表/表格形式`
7. `最后给出 interpretation / risk / next-step`

如果用户说“先给我总结框架”，则只输出：

- block list
- must-show fields
- chart/table suggestions
- interpretation questions
- do/don’t rules

## HTML Save Contract

当用户明确要求“展示 / 总结某个覆盖阶段”且你实际生成 HTML 时，默认保存合同是：

```text
outputs/<lineage_id>/<stage_dir>/display/stage_display.html
```

### Save Behavior
- 不同阶段天然落在不同 `stage_dir` 下，因此不同阶段会有不同 HTML 文件
- 同一阶段重复生成时，**覆盖同一个** `stage_display.html`
- 当前不要求保留 HTML 历史版本

### Chat Response Behavior
- 不要把整段 HTML 直接输出到聊天里
- 聊天里只返回：
  - 一个简短摘要
  - 保存路径
- 如果用户明确要求看源码或 HTML 片段，再按需引用局部内容

### Save Discipline
- 只有当用户明确要求展示时才生成并落盘
- 不要把保存 HTML 重新变成 stage gate
- 不要把这个保存动作伪装成 review closure 或 machine-readable governance proof

## Final Reminder

当用户主动要求展示时，先判断：

- 他要的是简报式总结
- 还是分析式展示框架
- 还是图表导向的展示建议

然后按本 skill 的对应 stage guidance 生成内容。

不要把这个 skill 当成：

- orchestration step
- automatic review follow-up
- runtime renderer
- mandatory workflow gate
