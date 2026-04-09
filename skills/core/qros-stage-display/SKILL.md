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

### Recommended Summary Blocks
- `Research Thesis And Route Decision`
- `Scope Boundary`
- `Data / Time Commitments`
- `Execution Constraint Summary`
- `What Downstream Stages Must Reuse`

### Recommended Charts / Tables / Visuals
- route decision summary table
- scope / market / universe boundary table
- time split timeline schematic
- execution constraints checklist

### Interpretation Questions
- 这一阶段到底冻结了哪些研究边界？
- 为什么当前选择的是这个 route，而不是别的 route？
- 下游最不能擅自改动的约束是什么？

### Stage-Specific Do / Don’t Rules
- **Do:** 明确展示 route choice、scope、data/time commitments、execution constraints
- **Do:** 强调哪些边界是给后续 stage 继承的
- **Don't:** 把还没冻结的 signal / train / backtest 结论提前当成 mandate 展示结果
- **Don't:** 用实现细节淹没 thesis 和 scope 这两个一级问题

---

## Stage: `csf_data_ready`

### Recommended Summary Blocks
- `Panel Construction And Universe Definition`
- `Coverage And QC Summary`
- `Eligibility / Shared Base Readiness`
- `Downstream Signal-Ready Dependencies`

### Recommended Charts / Tables / Visuals
- coverage summary table or heatmap
- eligibility funnel table
- panel / universe contract table
- artifact inventory table

### Interpretation Questions
- 这个 panel base 是否足够支撑后续因子工作？
- 最大的 coverage / QC 风险在哪里？
- 哪些共享底座是 downstream 必须直接复用的？

### Stage-Specific Do / Don’t Rules
- **Do:** 展示 panel、coverage、eligibility、shared base 这四类核心 readiness 信息
- **Do:** 明确“哪里可用、哪里缺口最大”
- **Don't:** 把 factor alpha 结论或 signal 表现混进 data-ready 展示
- **Don't:** 只列 artifact 名称，不解释其对 signal-ready 的意义

---

## Stage: `csf_signal_ready`

### Recommended Summary Blocks
- `Factor Identity And Role`
- `Transform / Neutralization / Ranking Logic`
- `Coverage / Stability Sanity Checks`
- `What Train Freeze Will Treat As Fixed`

### Recommended Charts / Tables / Visuals
- factor pipeline summary diagram
- factor distribution chart
- factor coverage summary table
- transform / neutralization / ranking rule matrix

### Interpretation Questions
- 这个 factor 到底在测什么？
- 哪些 transform / neutralization 选择是治理关键？
- train 阶段还能改什么，不能改什么？

### Stage-Specific Do / Don’t Rules
- **Do:** 把 factor identity 和 factor role 讲清楚
- **Do:** 明确哪些处理步骤已经被 signal-ready 固定
- **Don't:** 把 train-governable threshold 问题提前塞进 signal-ready 结论
- **Don't:** 用“效果很好”替代 factor meaning / pipeline explanation

---

## Stage: `csf_train_freeze`

### Recommended Summary Blocks
- `Training Window Policy`
- `Threshold / Preprocess Governance`
- `Parameter Ledger And Rejections`
- `What Test Stage Inherits`

### Recommended Charts / Tables / Visuals
- train window timeline
- threshold summary table
- parameter keep/reject summary table
- preprocess governance table

### Interpretation Questions
- 哪些轴现在仍然是 train-governable 的？
- 这阶段最关键的 reject pattern 是什么？
- test 阶段将继承哪些冻结对象？

### Stage-Specific Do / Don’t Rules
- **Do:** 展示 train window、threshold governance、param ledger 三个核心面
- **Do:** 明确 rejected variants 的主要原因
- **Don't:** 把 test/backtest 的结果反向写成 train freeze 的合理性证明
- **Don't:** 把 signal-ready 已固定的东西伪装成 train still-tunable

---

## Stage: `csf_test_evidence`

### Recommended Summary Blocks
- `Formal Gate Evidence`
- `Admissibility Summary`
- `Audit / Informational Findings`
- `Backtest Entry Readiness`

### Recommended Charts / Tables / Visuals
- formal gate table
- admissibility summary table
- audit observations table
- selected frozen outputs summary table

### Interpretation Questions
- 到底哪些证据足以支持进入 backtest？
- 哪些问题只是 audit 信息，而不是 formal gate blocker？
- downstream backtest 最关键会继承什么？

### Stage-Specific Do / Don’t Rules
- **Do:** 明确 formal gate 与 audit 的区别
- **Do:** 展示 admissibility 的核心结论
- **Don't:** 把 informational audit 发现伪装成 formal blocker
- **Don't:** 直接跳去 backtest policy，而不解释 test evidence 为什么够用

---

## Stage: `csf_backtest_ready`

### Recommended Summary Blocks
- `Execution And Portfolio Policy`
- `Engine / Implementation Contract`
- `Risk / Capacity Framing`
- `What Holdout Must Reuse`

### Recommended Charts / Tables / Visuals
- execution policy table
- portfolio / risk overlay summary table
- engine contract comparison matrix
- capacity / fragility notes table

### Interpretation Questions
- downstream backtest 必须严格遵守哪些交易规则？
- 哪些 assumptions 最脆弱？
- capacity / risk overlay 在这里是如何被冻结的？

### Stage-Specific Do / Don’t Rules
- **Do:** 把 execution / portfolio / risk / engine 作为四个主轴展示
- **Do:** 突出“holdout 将复用什么”
- **Don't:** 把 holdout 结论提前并入 backtest-ready 展示
- **Don't:** 只给一堆策略参数，不解释 policy 层语义

---

## Stage: `csf_holdout_validation`

### Recommended Summary Blocks
- `Holdout Window And Reuse Rules`
- `Drift / Stability Interpretation`
- `Failure Governance`
- `Final Decision-Readiness Summary`

### Recommended Charts / Tables / Visuals
- holdout window / split diagram
- drift audit summary table
- stability comparison table
- failure-governance trigger matrix

### Interpretation Questions
- 什么算 validation，什么算 drift evidence？
- 什么情况会触发 rollback / child lineage？
- 这个阶段的核心结论是“验证通过”，还是“风险被重新界定”？

### Stage-Specific Do / Don’t Rules
- **Do:** 展示 holdout window、reuse contract、drift audit、failure governance
- **Do:** 强调 decision-readiness 而不是只给结果数字
- **Don't:** 把 backtest 与 holdout 混成一个统一展示口径
- **Don't:** 跳过 failure governance 直接下最终乐观结论

---

## Output Guidance

如果用户说“做成展示稿”，默认输出可采用：

1. `标题`
2. `阶段一句话定义`
3. `4~5 个展示块`
4. `每块 2~4 个 bullet`
5. `1 个推荐图表/表格说明`
6. `最后给出 interpretation / risk / next-step`

如果用户说“先给我总结框架”，则只输出：

- block list
- chart/table suggestions
- interpretation questions
- do/don’t rules

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
