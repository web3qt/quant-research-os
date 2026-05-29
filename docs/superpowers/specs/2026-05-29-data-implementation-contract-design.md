# Data Implementation Contract Design

## Goal

为 active data-ready 路线新增一个 runtime-facing 硬门禁：`data_implementation_contract`。

该门禁只覆盖当前真实分流后的两个 data-ready 阶段：

- `csf_data_ready`
- `tss_data_ready`

目标是把数据底座实现纪律固定到 QROS runtime / preflight 层，避免 agent 在每条 lineage 里重复走低效 pandas、逐行循环、逐 symbol 串行全量处理，再临时调研向量化方案。

## Non-goals

- 不新增公开 workflow stage。
- 不把 legacy `data_ready` 纳入本次能力范围。
- 不引入性能 benchmark 作为 v1 gate。
- 不要求用户额外确认技术实现细节。
- 不禁止 Python loop 用于 manifest、字段字典、输出文件枚举等小型控制流。

## Product Decision

采用方案 2：新增 `data_implementation_contract` gate。

它是 `csf_data_ready` / `tss_data_ready` author lane 内部必须通过的硬门禁，而不是 `data_implement` 这种公开阶段。公开流程仍保持：

```text
mandate -> csf_data_ready / tss_data_ready -> signal_ready ...
```

author lane 的内部顺序应变为：

```text
freeze groups confirmed
-> lineage-local stage program exists
-> data_implementation_contract passes
-> build formal artifacts
-> artifact contract validation
-> semantic validation
-> review-entry preflight
```

## Contract Shape

新增机器真值层：

```text
contracts/stages/data_implementation_contract.yaml
```

该 contract 声明：

- `applicable_stages`: `csf_data_ready`, `tss_data_ready`
- `legacy_stages_excluded`: `data_ready`
- `required_engine`: `polars`
- `preferred_io`: parquet-first
- `preferred_execution`: lazy scan / expression / projection / predicate pushdown
- `forbidden_patterns`: pandas 主路径、row-wise loop、逐 symbol 串行全量处理、重复全量 scan
- `allowed_exceptions`: metadata/report 小表、manifest 写入、字段字典、测试夹具、docs、archive/migration

## Stage Program Declaration

`stage_program.yaml` 允许并要求在适用 stage 中声明：

```yaml
data_implementation_contract:
  engine: polars
  input_strategy: parquet_lazy_scan
  compute_strategy: expression_vectorized
  output_strategy: parquet_columnar
  disallowed_main_path:
    - pandas
    - row_wise_loop
    - per_symbol_full_scan_loop
    - repeated_full_scan_without_shared_intermediate
```

声明缺失、声明与 contract 不一致、或声明与代码扫描结果冲突，都必须 fail。

## Runtime Validator

新增 runtime helper：

```text
runtime/tools/data_implementation_contract_runtime.py
```

核心 API：

```text
validate_data_implementation_contract(lineage_root, stage_id, route)
```

validator 读取 lineage-local stage program 目录，并检查：

- `stage_program.yaml` 的 `data_implementation_contract` 声明
- `run_stage.py` 和 helper `.py` 的 imports / calls / AST pattern
- 适用 stage 是否为 `csf_data_ready` 或 `tss_data_ready`

返回 machine-readable result，至少包含：

- `stage_id`
- `program_dir`
- `status`
- `findings`
- `reason_codes`

## Hard Fail Rules

以下模式在 `csf_data_ready` / `tss_data_ready` stage program 主路径中直接 fail：

- `import pandas` 或 `from pandas ...`
- `.to_pandas()`
- `.iterrows()`
- `.itertuples()`
- `DataFrame.apply(..., axis=1)`
- 对 parquet/csv 文件列表逐个 Python loop 读入并 append/concat 作为主数据路径
- 对 asset/symbol 循环逐个全量读写，而不是用分组、分区或 lazy expression
- Python row dict/list accumulation 后一次性写大 parquet 作为正式面板主路径
- 重复读取同一大输入来生成多个 formal outputs，且没有 shared lazy/cached intermediate

## Allowed Exceptions

以下场景不应被误杀：

- tests、docs、fixtures、archive、migration 中的 pandas 示例或历史材料
- 小型 metadata/report 转换
- manifest、artifact catalog、field dictionary 写入
- 枚举输出文件、检查路径、组装 structured manifest 的普通 Python 控制流
- `pl.read_parquet` 读取已知小型 summary artifact

大表默认要求 `pl.scan_parquet` 或等价 lazy scan。`pl.read_parquet` 用于大表时，stage program 需要明确声明原因；v1 可先以 warning 或 explicit exception field 表达，不能静默通过。

## Integration Points

### Author Skills

更新：

- `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- `skills/tss_data_ready/qros-tss-data-ready-author/SKILL.md`

要求：

- 明确 `data_implementation_contract` 是 build/review 前硬门禁
- 写明 Polars/parquet/lazy/expression/vectorized 默认纪律
- 写明 pandas 和 row-wise 主路径禁止项
- 保持“不询问用户技术实现细节”的口径

### Runtime / CLI

接入位置：

- `qros-validate-stage --stage csf_data_ready`
- `qros-validate-stage --stage tss_data_ready`
- review-entry deterministic preflight

不接入 legacy `data_ready`，避免扩大历史兼容范围。

### Review Preflight

reviewer lane 进入前必须执行该 gate。失败时不得进入 reviewer lane，错误应留在 author lane 修复 stage program。

建议 reason codes：

- `DATA_IMPL_DECLARATION_MISSING`
- `DATA_IMPL_ENGINE_FORBIDDEN_PANDAS`
- `DATA_IMPL_ENGINE_NOT_POLARS`
- `DATA_IMPL_TO_PANDAS_FORBIDDEN`
- `DATA_IMPL_ROW_LOOP_FORBIDDEN`
- `DATA_IMPL_APPLY_AXIS1_FORBIDDEN`
- `DATA_IMPL_PER_ASSET_FULL_SCAN_FORBIDDEN`
- `DATA_IMPL_REPEATED_FULL_SCAN_FORBIDDEN`
- `DATA_IMPL_CONTRACT_STAGE_NOT_APPLICABLE`

## Testing Strategy

Focused tests:

- contract test: `contracts/stages/data_implementation_contract.yaml` exists and applies only to `csf_data_ready` / `tss_data_ready`
- runtime validator pass: Polars lazy parquet pipeline with vectorized expressions passes
- runtime validator fail: pandas import fails
- runtime validator fail: `.to_pandas()` fails
- runtime validator fail: `.iterrows()` / `.itertuples()` / `apply(axis=1)` fails
- runtime validator fail: missing `data_implementation_contract` declaration fails
- runtime validator fail: per-symbol full-scan loop pattern fails
- preflight test: invalid `csf_data_ready` program cannot enter review
- preflight test: invalid `tss_data_ready` program cannot enter review
- skill/doc test: both author skills mention the gate and forbidden patterns

Verification after implementation:

```text
python -m pytest <focused tests>
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

`full-smoke` is required because this changes stage gate semantics and review-entry preflight behavior for active data-ready stages.

## Migration

Existing fixture/demo programs may need explicit test-only exceptions or updates to Polars-style examples. Real research flow should fail closed when an active data-ready stage program lacks the declaration or uses forbidden main-path patterns.

The implementation should keep diffs small:

1. Add contract and validator.
2. Add focused tests.
3. Wire into `csf_data_ready` / `tss_data_ready` validation and preflight.
4. Update active author skills and user docs.
5. Run focused tests, smoke, and full-smoke.

