# Signal Ready Orchestration Design

## Goal

把 `signal_ready` 接入 `qros-research-session`，使统一主流程在 `data_ready review` 之后继续以交互式冻结方式推进到 `signal_ready review`。

## Product Semantics

`signal_ready` 第一版只冻结“正式 baseline signal 合同”，不做 `small search batch`，也不做 `full frozen grid`。

`signal_ready` 冻结：

- baseline signal expression
- baseline `param_id`
- 正式时间语义
- 正式 signal schema
- 下游可消费的正式 signal artifacts

`signal_ready` 不冻结：

- search batch
- full frozen grid
- train / test 结论
- 收益结论
- 白名单结论

一句话边界：

`signal_ready` 回答“后续研究到底在用哪个 baseline signal”，不回答“哪组参数最好”。

## Stage Flow

统一会话主流程扩展为：

`idea_intake -> mandate_confirmation_pending -> mandate -> mandate review -> data_ready_confirmation_pending -> data_ready -> data_ready review -> signal_ready_confirmation_pending -> signal_ready -> signal_ready review`

对应的 runtime 状态新增：

- `signal_ready_confirmation_pending`
- `signal_ready_author`
- `signal_ready_review`
- `signal_ready_review_complete`

当 `02_data_ready/stage_completion_certificate.yaml` 存在时，会话不再停止，而是进入 `signal_ready_confirmation_pending`。

## Freeze Groups

`signal_ready` 按 5 组交互冻结：

1. `signal_expression`
2. `param_identity`
3. `time_semantics`
4. `signal_schema`
5. `delivery_contract`

每组在 draft 中都包含：

- `confirmed`
- `draft`
- `missing_items`

交互节奏统一为：

1. agent 从 `01_mandate` 与 `02_data_ready` 推出 baseline signal 默认草案
2. 只问该组最关键的分歧点
3. 将用户回答压成 freeze draft
4. 回显这一组将被冻结的内容
5. 等待该组确认

五组都完成后，再输出 `Signal Ready Summary` 并明确问：

`是否按以上内容冻结 signal_ready？`

只有明确肯定后，才允许生成正式 `03_signal_ready/*`。

## Disk State

正式阶段目录直接使用：

- `03_signal_ready/`

在正式产物写出前，先在该目录保存草案与批准状态：

- `03_signal_ready/signal_ready_freeze_draft.yaml`
- `03_signal_ready/signal_ready_transition_approval.yaml`

## Required Outputs

第一版 `signal_ready` 至少 formalize 这些产物：

- `param_manifest.csv`
- `params/`
- `signal_coverage.csv`
- `signal_coverage.md`
- `signal_coverage_summary.md`
- `signal_contract.md`
- `signal_fields_contract.md`
- `signal_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

第一版不需要真的完成全量真实信号计算，但必须把 baseline `param_id`、timeseries schema、时间语义和 formal delivery 合同稳定落盘。

## Runtime Strategy

新增 `tools/signal_ready_runtime.py`，职责类似 `tools/data_ready_runtime.py`：

- scaffold `03_signal_ready/`
- 提供 blank freeze draft
- 校验 5 组均已确认
- 从 freeze draft 生成 formal outputs

`tools/research_session.py` 负责：

- 在 data_ready review complete 后进入 `signal_ready_confirmation_pending`
- 报告当前还缺哪一组
- 只有在最终批准且 5 组都 confirmed 时进入 `signal_ready_author`
- `signal_ready` outputs 完整后进入 `signal_ready_review`
- `signal_ready` closure artifacts 完整后进入 `signal_ready_review_complete`

## Skills And Docs

需要新增 `qros-signal-ready-author` skill，并更新：

- `qros-research-session`
- `README.md`
- `README_EN.md`
- `docs/experience/qros-research-session-usage.md`
- `docs/experience/quickstart-codex.md`

文档要同步说明：

- first-wave 已扩展到 `signal_ready`
- `signal_ready` 是交互式冻结 baseline signal，不是静默生成
- review 仍由现有 `qros-signal-ready-review` 与 stage review engine 完成

## Guardrails

- 不允许在 `signal_ready` 中改 mandate 冻结的核心机制边界
- 不允许在 `signal_ready` 中引入 mandate 未允许的参数维度
- 不允许在 `signal_ready` 中做 search batch 或 full grid
- 不允许在 `signal_ready` 中输出收益结论或 whitelist 结论
- Train 阶段不得新增本阶段未物化过的 `param_id`

## Testing Strategy

优先补以下测试：

- session stage detection 能识别 `signal_ready_confirmation_pending`
- data_ready review complete 后默认继续进入 signal_ready，而不是停止
- 五组未确认时，next action 会指出当前 signal_ready freeze group
- 明确批准后才生成 `03_signal_ready/*`
- `03_signal_ready` 完整但未 closure 时进入 `signal_ready_review`
- `03_signal_ready/stage_completion_certificate.yaml` 存在时进入 `signal_ready_review_complete`
- skill/docs 反映新的 first-wave 边界
