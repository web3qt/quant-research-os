# Data Ready Orchestration Design

## Goal

把 `data_ready` 接入 `qros-research-session`，使其在 `mandate review` 之后继续以交互式冻结方式推进到 `data_ready review`，而不是停在 mandate 阶段。

## Product Semantics

`mandate` 冻结“研究什么”；`data_ready` 冻结“后续研究共同依赖的数据研究底座”。

`data_ready` 可以冻结：

- 统一时间栅格与主时间键
- universe admissibility 与 exclusion 结果
- missing / stale / bad price / outlier 的质量语义
- 共享基础层，如 `aligned_bars/` 与 `rolling_stats/`
- 共享派生层，如 `pair_stats/`、`benchmark_residual`、`topic_basket_state`

`data_ready` 不可以冻结：

- thesis-specific 信号定义
- `param_id` 级信号实例化
- 收益结论、白名单结论或 alpha verdict

一句话边界：

`data_ready` 产出“研究共享特征层”，不能产出“策略结论层”。

## Stage Flow

统一会话主流程扩展为：

`idea_intake -> mandate_confirmation_pending -> mandate -> mandate review -> data_ready_confirmation_pending -> data_ready -> data_ready review`

对应的 runtime 状态：

- `idea_intake`
- `mandate_confirmation_pending`
- `mandate_author`
- `mandate_review`
- `data_ready_confirmation_pending`
- `data_ready_author`
- `data_ready_review`
- `data_ready_review_complete`

当 `01_mandate/stage_completion_certificate.yaml` 存在时，会话不再停止，而是进入 `data_ready_confirmation_pending`。

## Freeze Groups

`data_ready` 按 5 组交互冻结：

1. `extraction_contract`
2. `quality_semantics`
3. `universe_admission`
4. `shared_derived_layer`
5. `delivery_contract`

每组在 draft 中都包含：

- `confirmed`
- `draft`
- `missing_items`

交互节奏统一为：

1. agent 从 `01_mandate` 推出默认草案
2. 只问该组最关键的分歧点
3. 将用户回答压成 freeze draft
4. 回显这一组将被冻结的内容
5. 等待该组确认

五组都完成后，再输出 `Data Ready Summary` 并明确问：

`是否按以上内容冻结 data_ready？`

只有明确肯定后，才允许生成正式 `02_data_ready/*`。

## Disk State

正式阶段目录直接使用：

- `02_data_ready/`

在正式产物写出前，先在该目录保存草案与批准状态：

- `02_data_ready/data_ready_freeze_draft.yaml`
- `02_data_ready/data_ready_transition_approval.yaml`

这样既保留阶段号，也避免把 `data_ready` 的中间状态塞回 `01_mandate/`。

## Required Outputs

第一版 `data_ready` 至少 formalize 这些产物：

- `aligned_bars/`
- `rolling_stats/`
- `pair_stats/`
- `benchmark_residual/`
- `topic_basket_state/`
- `qc_report.parquet`
- `dataset_manifest.json`
- `validation_report.md`
- `data_contract.md`
- `dedupe_rule.md`
- `universe_summary.md`
- `universe_exclusions.csv`
- `universe_exclusions.md`
- `artifact_catalog.md`
- `field_dictionary.md`

第一版不需要真的完成大规模数据计算，但必须把阶段 skeleton、数据合同、交付清单和 review 可消费的 formal outputs 稳定落盘。

## Runtime Strategy

新增 `tools/data_ready_runtime.py`，职责类似 `tools/idea_runtime.py`：

- scaffold `02_data_ready/`
- 提供 blank freeze draft
- 校验 5 组均已确认
- 从 freeze draft 生成 formal outputs

`tools/research_session.py` 负责：

- 在 mandate review complete 后进入 `data_ready_confirmation_pending`
- 报告当前还缺哪一组
- 只有在最终批准且 5 组都 confirmed 时进入 `data_ready_author`
- `data_ready` outputs 完整后进入 `data_ready_review`
- `data_ready` closure artifacts 完整后进入 `data_ready_review_complete`

## Skills And Docs

需要新增 `qros-data-ready-author` skill，并更新：

- `qros-research-session`
- `README.md`
- `docs/experience/qros-research-session-usage.md`
- `docs/experience/quickstart-codex.md`

文档要同步说明：

- first-wave 已扩展到 `data_ready`
- `data_ready` 是交互式冻结，不是静默生成
- review 仍由现有 `qros-data-ready-review` 与 stage review engine 完成

## Guardrails

- 不允许在 `data_ready` 中改 mandate 冻结的时间边界
- 不允许在 `data_ready` 中改 mandate 冻结的 universe 口径
- 一旦需要改上面两项，必须回退到 `mandate` 或开新 lineage
- 不允许在 `data_ready` 中产出 thesis-specific signal
- 不允许静默吞缺失或静默 forward-fill

## Testing Strategy

优先补以下测试：

- session stage detection 能识别 `data_ready_confirmation_pending`
- mandate review complete 后默认继续进入 data_ready，而不是停止
- 五组未确认时，next action 会指出当前 data_ready freeze group
- 明确批准后才生成 `02_data_ready/*`
- `02_data_ready` 完整但未 closure 时进入 `data_ready_review`
- `02_data_ready/stage_completion_certificate.yaml` 存在时进入 `data_ready_review_complete`
- skill/docs 反映新的 first-wave 边界
