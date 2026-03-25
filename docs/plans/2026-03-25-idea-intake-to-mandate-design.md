# Idea Intake To Mandate Design

**Date:** 2026-03-25  
**Status:** Draft approved for direction  
**Scope:** `Codex-only`, `pre-mandate flow`, first wave covers `idea_intake -> mandate`

## Goal

把“一个想法如何升格为正式 mandate”从自由讨论，变成可重复执行、可写盘、可 gate 的研究前置流程。

第一版只解决一件事：

- 把原始想法压成标准观察、机制假设、研究问题和 qualification 结论
- 只有通过 qualification 的 idea 才允许进入 `mandate`

## Core Principle

参考 `gstack`，这里的关键不是“让 agent 更会头脑风暴”，而是：

- 显式入口
- 固定产物
- 固定 gate
- 固定 verdict
- 固定冻结边界

所以这一段不是：

`idea -> prompt -> mandate`

而是：

`idea -> intake artifacts -> qualification gate -> mandate artifacts`

## Recommended Flow

第一版前置流程拆成 4 步：

1. `Observation Capture`
   把原始想法写成标准观察，不允许直接写收益结论
2. `Hypothesis Qualification`
   写 primary hypothesis 和 counter-hypothesis
3. `Research Question Scoping`
   收窄为明确市场、标的、时间尺度、任务定义
4. `Mandate Admission`
   只有 qualification 通过，才允许进入 `mandate`

流程链路：

`Idea -> Observation -> Hypothesis -> Qualification -> Mandate`

## Stage Boundary

建议将当前研究流程向前扩一层：

- `00_idea_intake`
- `01_mandate`
- `02_data_ready`
- `03_signal_ready`

也就是说，现有 `mandate` 之前增加一个正式的 `idea_intake` 阶段。

## Repository Layout

建议第一版目录结构：

```text
outputs/<lineage>/
  00_idea_intake/
    idea_brief.md
    observation_hypothesis_map.md
    research_question_set.md
    scope_canvas.yaml
    qualification_scorecard.yaml
    idea_gate_decision.yaml
    artifact_catalog.md
  01_mandate/
    mandate.md
    research_scope.md
    time_split.json
    parameter_grid.yaml
    run_config.toml
    artifact_catalog.md
    field_dictionary.md
```

## Intake Artifacts

### `idea_brief.md`

记录：

- 原始想法
- 来源
- 观察到的现象
- 初始怀疑点
- 为什么值得进入 intake

### `observation_hypothesis_map.md`

记录：

- `observation`
- `primary_hypothesis`
- `counter_hypothesis`
- 可能机制链条
- 不在当前研究范围内的内容

### `research_question_set.md`

记录：

- 主研究问题
- 子问题
- 最小验证顺序
- 成功后才值得继续问的问题
- 失败即停止的问题

### `scope_canvas.yaml`

记录：

- `market`
- `instrument_type`
- `universe`
- `bar_size`
- `holding_horizons`
- `target_task`
- `excluded_scope`
- `budget_days`
- `max_iterations`

### `qualification_scorecard.yaml`

记录 6 维资格化评分：

- `observability`
- `mechanism_plausibility`
- `tradeability`
- `data_feasibility`
- `scoping_clarity`
- `distinctiveness`

每一项必须包含：

- `score`
- `evidence`
- `uncertainty`
- `kill_reason`

### `idea_gate_decision.yaml`

正式 gate 结论文件。

允许值：

- `GO_TO_MANDATE`
- `NEEDS_REFRAME`
- `DROP`

并记录：

- `why`
- `approved_scope`
- `required_reframe_actions`
- `rollback_target`

## Qualification Gate

### Minimum Dimensions

第一版强制审这 6 项：

1. `Observability`
   是否能明确写出可观测变量与目标对象
2. `Mechanism Plausibility`
   是否有 plausible mechanism，而不是后验故事
3. `Tradeability`
   即使成立，是否存在覆盖成本的可能
4. `Data Feasibility`
   数据和 artifacts 是否可稳定获取与落盘
5. `Scoping Clarity`
   是否能收窄到明确市场、标的、周期与任务
6. `Distinctiveness`
   是否只是常见因子换壳

### Mandatory Rules

第一版应强制：

- 没有 `counter_hypothesis`，不能过 gate
- 没有 `kill_criteria`，不能过 gate
- 没有 `approved_scope`，不能进入 mandate

### Verdict Rules

- 若存在关键维度明显不成立，`DROP`
- 若方向可研究，但边界不清或预算不值得，`NEEDS_REFRAME`
- 若 6 项全部达到最低门槛，`GO_TO_MANDATE`

## Mandate Admission Rule

`mandate-author` 不直接消费一句口头想法。

它的冻结输入应改成：

- `qualification_scorecard.yaml`
- `research_question_set.md`
- `scope_canvas.yaml`
- `idea_gate_decision.yaml`

只有当 `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` 时，才允许生成：

- `mandate.md`
- `research_scope.md`
- `time_split.json`
- `parameter_grid.yaml`
- `run_config.toml`

## First-Wave Skills

第一版建议先做两个 author-facing skills。

### `qros-idea-intake-author`

职责：

- 从原始 idea 生成 `00_idea_intake` artifacts
- 强制写出 observation / hypothesis / counter-hypothesis
- 强制写出 qualification scorecard
- 输出 `idea_gate_decision.yaml`

不负责：

- 冻结正式 mandate
- 直接宣布进入训练或回测

### `qros-mandate-author`

职责：

- 仅在 `GO_TO_MANDATE` 条件下工作
- 将 intake artifacts 压缩成 `mandate` artifacts
- 明确研究边界、时间切分、参数字典、实现栈和研究预算

不负责：

- 修改未通过 qualification 的 idea
- 根据后验结果静默重写题目

## Example: BTC-led ALT Transmission

以“BTC 领动 ALT”为例：

- `Observation`
  BTC 显著冲击后，部分高流动性 ALT 在未来 15m-60m 可能存在跟随反应
- `Primary Hypothesis`
  BTC 承担价格发现，ALT 存在信息吸收迟滞
- `Counter Hypothesis`
  这只是共同 beta 暴露，并不存在可交易滞后
- `Research Question`
  BTC shock 后 ALT 的 future relative return / event probability 是否显著变化
- `Scope`
  Binance perp / top liquid alts / 5m / 15m-60m / event study first
- `Qualification Verdict`
  只有通过后才可进入 `mandate`

## Integration With Existing Review Stack

这段前置流程完成后，完整闭环会变成：

`idea-intake-author -> idea gate -> mandate-author -> mandate-review`

它和现有 review engine 的关系是：

- `idea_intake` 负责前置过滤与问题资格化
- `mandate` 负责正式冻结研究边界
- `mandate-review` 继续作为独立 gate

## Success Criteria

如果第一版设计成功，应满足：

- 一个原始想法能被压成标准 intake artifacts
- qualification 结论不是自由文本，而是 machine-readable gate
- `mandate-author` 只消费通过 qualification 的 idea
- 现有 `mandate-review` 可直接接住新生成的 mandate artifacts
