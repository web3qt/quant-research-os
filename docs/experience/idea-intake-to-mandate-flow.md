# Idea Intake To Mandate Flow

## Goal

这条前置流程负责回答一个问题：

一个原始想法，是否值得正式投入研究预算，并冻结成 mandate。

它不直接研究收益，也不直接进入 `data_ready`。

## Flow

第一版流程固定为：

`Idea -> Observation -> Hypothesis -> Qualification -> Mandate`

落盘阶段为：

- `00_idea_intake`
- `01_mandate`

## `00_idea_intake` Required Artifacts

- `idea_brief.md`
- `observation_hypothesis_map.md`
- `research_question_set.md`
- `scope_canvas.yaml`
- `qualification_scorecard.yaml`
- `idea_gate_decision.yaml`
- `artifact_catalog.md`

可以先用下面的命令生成这套模板：

```bash
python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
```

## Qualification Rules

qualification 至少评估以下 6 项：

- `observability`
- `mechanism_plausibility`
- `tradeability`
- `data_feasibility`
- `scoping_clarity`
- `distinctiveness`

强制要求：

- 必须写 `counter_hypothesis`
- 必须写 kill criteria
- 必须写 machine-readable gate decision

## Gate Verdicts

- `GO_TO_MANDATE`
- `NEEDS_REFRAME`
- `DROP`

只有 `GO_TO_MANDATE` 允许进入 `01_mandate`。

## `01_mandate` Handoff

`mandate-author` 只消费这些 intake outputs：

- `qualification_scorecard.yaml`
- `research_question_set.md`
- `scope_canvas.yaml`
- `idea_gate_decision.yaml`

然后生成：

- `mandate.md`
- `research_scope.md`
- `time_split.json`
- `parameter_grid.yaml`
- `run_config.toml`

当 `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` 时，可以运行：

```bash
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
```

## Example

以 BTC 领动 ALT 为例：

- `Observation`
  BTC 显著冲击后，部分高流动性 ALT 在未来 15m-60m 可能存在跟随反应
- `Primary Hypothesis`
  BTC 承担价格发现，ALT 存在信息吸收迟滞
- `Counter Hypothesis`
  这只是共同 beta 暴露，不存在可交易滞后
- `Qualification`
  先判断变量是否可观测、范围是否可收窄、成本后是否有潜在空间
- `Mandate`
  只有通过 intake gate 后，才冻结正式研究边界
