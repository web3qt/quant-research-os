# QROS paper-to-spec 使用说明

## 当前状态

`qros-paper-to-spec` 是 paper data-spec-first 入口。旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

当前不要再把它当作“PDF 直接生成完整 strategy spec”或“PDF 直接生成回测代码”的入口。旧版 `paper -> strategy_spec -> baseline` fast-lane 已经下线。

第一版只产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

这个入口不是 `qros-research-session` 的阶段入口，不进入 mandate / freeze / review / failure handling 的 heavy governance flow。

## Contract

`paper_data_spec.yaml` 必须遵守：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
```

第一版 contract 锁定以下内容：

- required top-level fields
- core data requirements
- strict blocking fields
- requirement status / source enums
- crypto perpetual optional blocks
- exchange profile defaults
- blocking question groups

## 执行流程

收到 `$qros-paper-to-spec <pdf|url|summary>` 后，Codex 应按这个顺序处理：

1. 识别 `source`：title、locator、source_kind、paper_slug。
2. 自己读取 PDF / URL / pasted summary，并记录 `reading_coverage`。
3. 确认 `target_market`，默认面向 `crypto_perpetual`，使用 `generic_crypto_perp` 或研究员指定的 exchange profile。
4. 填写 `core_data_requirements`：`universe`、`price_bars`、`price_type`、`funding`、`fees_and_slippage`、`label_or_return_target`、`timestamp_alignment`、`data_availability`。
5. 只在论文或 data reasoning 触发时填写 `triggered_optional_blocks`，包括 derivatives positioning、liquidity microstructure、cross-exchange、external/onchain、sentiment/news。
6. 如任何 strict blocking field 为 `unknown`，或 PDF 读取覆盖不足以支撑 data 结论，必须停止并问研究员。
7. 没有阻断项时，写入 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml`。
8. 使用 deterministic validator 校验 `paper_data_spec.yaml`。

Validator 入口：

```text
python runtime/scripts/validate_paper_data_spec.py --spec-path outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

该 validator 只检查 contract shape、枚举、required fields、reading coverage 和 strict blocking unknown，不判断策略是否有效。

## Requirement entry shape

每个 data requirement 使用同一结构：

```yaml
status: required | optional | not_needed | unknown
source: paper_stated | agent_inferred | researcher_required | exchange_profile_default
value: {}
evidence: []
blocking_if_unknown: true
question_if_unknown: ""
```

`paper_stated` 只能用于论文明确写出的 data 事实。crypto perpetual 迁移假设必须标为 `agent_inferred`，研究员确认项必须标为 `researcher_required`，profile 制度默认值必须标为 `exchange_profile_default`。

## Strict blocking

以下字段不清楚时必须停止，不得继续 signal / train / test / backtest：

- `universe`
- `price_bars`
- `price_type`
- `funding`
- `fees_and_slippage`
- `label_or_return_target`
- `timestamp_alignment`
- `data_availability`

阻断问题最多聚合成 3 个问题，并按 `blocking_question_groups` 归类：

- `market_scope`
- `bar_and_price`
- `return_accounting`
- `source_coverage`

## 边界

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不把 validator failure 包装成 review verdict；这不是 `qros-research-session` review。
- 不把 crypto perpetual 迁移假设伪装成论文原文。
- 不为所有 optional blocks 机械展开字段；只展开被论文或 data reasoning 触发的块。
- 不保留与 `paper_data_spec_contract.yaml` 冲突的字段名或枚举。

## 后续

`paper_data_spec.yaml` 稳定后，再继续设计 paper signal spec、train-freeze spec、test-evidence spec 和 backtest spec。
