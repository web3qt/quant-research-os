# 从 Idea Intake 到 Mandate 的流程

## 目标

这条前置流程负责回答一个问题：

一个原始想法，是否值得正式投入研究预算，并冻结成 mandate。

它不直接研究收益，也不直接进入 `data_ready`。

如果你还没安装运行时和 skill，先看：

- `README.md`
- `docs/guides/installation.md`
- `docs/guides/quickstart-codex.md`
- `docs/guides/stage-freeze-group-field-guide.md`

## 流程

第一版流程固定为：

`Idea -> Observation -> Hypothesis -> Qualification -> Mandate`

落盘阶段为：

- `00_idea_intake`
- `01_mandate`

## `00_idea_intake` 必备产物

- `idea_brief.md`
- `intake_interview.md`
- `observation_hypothesis_map.md`
- `research_question_set.md`
- `artifact_catalog.md`
- `scope_canvas.yaml`
- `qualification_scorecard.yaml`
- `idea_gate_decision.yaml`
- `mandate_freeze_draft.yaml`

`00_idea_intake` 的 artifact shape 真值层是
`contracts/artifacts/idea_intake_artifacts.yaml`。字段一致必须由
contract、runtime scaffold 和 validator 保证；内容一致不应该强求，
自然语言内容只要求结构、枚举、必填项和默认值形状稳定。skill 是执行引导，
负责访谈顺序和禁止跳步，不负责重新定义字段。

正常用户不需要手动生成这套模板。直接从 active research repo 运行：

```text
qros-research-session 帮我研究这个想法：<your idea>
```

runtime 会在缺少 `00_idea_intake/` 时自动 scaffold intake artifacts。
如果需要手动确认磁盘 shape，运行：

```bash
qros-validate-stage --stage idea_intake --lineage-id <lineage_id>
```

对于一个全新的 raw idea，正确行为不是直接从一句话推断完整 intake 结论。应先进行 intake 访谈，至少确认：

- `observation`
- `primary hypothesis`
- `counter-hypothesis`
- `market` / `universe` / `target_task`
- `data_source` / `bar_size`
- `kill criteria` 或 `reframe` 条件

只有这些信息收齐后，才应该正式填写 `qualification_scorecard.yaml` 和 `idea_gate_decision.yaml`。

## Qualification 规则

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

## Gate Verdicts / 门禁结论

- `GO_TO_MANDATE`
- `NEEDS_REFRAME`
- `DROP`

只有 `GO_TO_MANDATE` 才允许申请进入 `01_mandate`。

但 `GO_TO_MANDATE` 不等于立即生成 mandate。

系统会先停在 `mandate_confirmation_pending`，等待显式确认。

## `01_mandate` Handoff / 交接

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

进入 `mandate` 前，必须先通过询问确认：

- `research_intent`
- `scope_contract`
- `data_contract`
- `execution_contract`

如果只记得组名，不确定字段该怎么理解，直接查：

- `docs/guides/stage-freeze-group-field-guide.md`

必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups。批量确认只完成 group confirmations，不等于最终确认进入 mandate。

四组都确认后，才允许最终冻结到 mandate 文档。

当 `idea_gate_decision.yaml.verdict == GO_TO_MANDATE` 时，先显式确认：

```bash
python runtime/.qros/bin/qros-session --outputs-root outputs --lineage-id <lineage_id> --confirm-mandate
```

确认后才允许生成：

```bash
python runtime/scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
```

`01_mandate/author/formal` 的正式 artifact shape 由 `contracts/artifacts/mandate_artifacts.yaml` 定义。`qros-mandate-author` 不再维护字段真值，只维护 freeze 顺序、确认规则和 validator 调用纪律。

构建 mandate 后必须运行：

```bash
qros-validate-stage --stage mandate --lineage-id <lineage_id>
```

如果 validator 失败，不得进入 mandate review。

完成 mandate 产物后，继续运行：

```bash
python runtime/scripts/run_stage_review.py
```

## 示例

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
