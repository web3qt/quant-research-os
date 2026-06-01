---
name: qros-paper-to-spec
description: Read a paper source and produce a first-stage crypto perpetual paper_data_spec.yaml with reading coverage, data requirements, and strict blocking questions.
---

# qros-paper-to-spec

## Purpose

`qros-paper-to-spec` 现在是 paper data-spec-first 入口。它的第一版职责是把论文、PDF、URL 或粘贴摘要整理成 crypto perpetual research fast-lane 的 `paper_data_spec.yaml`。

这个入口独立于 `qros-research-session`，不进入 mandate / freeze / review / failure handling 的 heavy governance flow。

## Current output

第一版只产 data spec：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

当前不直接生成完整 strategy spec，不直接生成回测代码，也不进入 signal / train-freeze / test-evidence / backtest spec。

旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

## Contract

生成 `paper_data_spec.yaml` 时必须遵守：

```text
contracts/paper_to_spec/paper_data_spec_contract.yaml
```

该 contract 是第一版 machine-readable 真值层，包含：

- required top-level fields
- core required data fields
- strict blocking fields
- requirement status / source enums
- crypto perpetual optional field blocks
- exchange profile defaults
- blocking question groups

## Execution protocol

收到 `$qros-paper-to-spec <pdf|url|summary>` 后，按以下顺序执行：

1. `source`：识别 `source_kind`、原始 locator、title、paper_slug。
2. `read source itself`：Codex 必须自己读取 PDF / URL / pasted summary，不能把读取责任推给 runtime wrapper。
3. `reading_coverage`：记录 PDF 总页数、成功提取页、覆盖章节、未提取页、低置信表格/公式和 data-relevant evidence。
4. `target_market`：默认面向 `crypto_perpetual`，使用 `generic_crypto_perp` 或研究员明确指定的 exchange profile。
5. `core_data_requirements`：逐项填写 `universe`、`price_bars`、`price_type`、`funding`、`fees_and_slippage`、`label_or_return_target`、`timestamp_alignment`、`data_availability`。
6. `triggered_optional_blocks`：只在论文或 data reasoning 触发时展开 derivatives positioning、liquidity microstructure、cross-exchange、external/onchain、sentiment/news。
7. `strict blocking`：任何 strict blocking field 为 `unknown`，或关键 evidence 不足，必须停止并问研究员。
8. `materialize`：在 active research repo 的 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml` 写入当前阶段产物。
9. `validate`：使用 deterministic validator 校验 `paper_data_spec.yaml`，若失败则修正 artifact 或把阻断问题返回研究员。

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

## Strict blocking fields

以下字段不清楚时必须停止，不得继续 signal / train / test / backtest：

- `universe`
- `price_bars`
- `price_type`
- `funding`
- `fees_and_slippage`
- `label_or_return_target`
- `timestamp_alignment`
- `data_availability`

阻断问题最多聚合成 3 个问题，并按 contract 中的 `blocking_question_groups` 归类：

- `market_scope`
- `bar_and_price`
- `return_accounting`
- `source_coverage`

## Boundaries

- 不直接生成完整 strategy spec。
- 不直接生成回测代码。
- 不把 validator failure 包装成 review verdict；这不是 `qros-research-session` review。
- 不把 crypto perpetual 迁移假设伪装成论文原文。
- 不为所有 optional blocks 机械展开字段；只展开被 PDF 或 data reasoning 触发的块。
- 不保留与 `paper_data_spec_contract.yaml` 冲突的字段名或枚举。
