---
name: qros-tss-data-ready-author
description: Use when a QROS time_series_signal lineage is at the tss_data_ready authoring gate.
---

# TSS Data Ready Author

## Purpose

只在 `mandate review` closure 完成且 `research_route = time_series_signal` 之后，把 `01_mandate` 冻结成正式 `02_tss_data_ready` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序，也不是在同一时点把多个资产互相排名。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_data_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Artifact Contract Truth

- `contracts/artifacts/tss_data_ready_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值；本文件只定义执行顺序、确认纪律和 review 边界。
- 必须先读取 artifact contract，再 scaffold / build `02_tss_data_ready/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_data_ready`；validator 不通过不得进入 review。

## Required Inputs

- `01_mandate/author/formal/research_route.yaml`
- `01_mandate/author/formal/time_split.json`
- `01_mandate/author/formal/run_config.toml`
- `01_mandate/review/closure/stage_completion_certificate.yaml`

## Required Outputs

- `time_index_manifest.json`
- `asset_time_index.parquet`
- `quality_flags.parquet`
- `split_sample_adequacy_report.yaml`
- `run_manifest.json`
- `rebuild_tss_data_ready.py`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `time_index_contract`
- `quality_semantics`
- `label_contract`
- `feature_base`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 本阶段只建立单资产时间轴、质量标记、split adequacy 和可复现数据基础层；不得产出信号有效性、收益或白名单结论。
- 必须在当前 research repo 真实物化 machine-readable artifacts，不得把空目录、placeholder 或 contract-only markdown 当成完成。
- 必须先显式生成或刷新 lineage-local stage program，并在 `run_manifest.json` 记录 replay/provenance。
- 必须通过 `data_implementation_contract` 硬门禁后才允许 build/review；该门禁只约束实现纪律，不替代 artifact contract、semantic validation 或 upstream binding validation。
- `data_implementation_contract` 门禁不通过时停在 author lane 修复程序，不得进入 review。
- 主数据引擎必须使用 Polars；大表 parquet 输入默认使用 `pl.scan_parquet` 或等价 lazy scan；time index、quality flags、split adequacy 和 as-of feature base 的聚合、排序、去重、join、窗口和过滤优先 Polars expression / lazy pipeline。
- 不得询问用户技术实现细节来决定是否使用 Polars、parquet-first、lazy scan 或表达式化计算。
- 主路径不得使用 pandas、`.to_pandas()`、`.iterrows()`、`.itertuples()`、`DataFrame.apply(..., axis=1)`、逐行循环、逐 symbol 全量 scan/read/write、重复全量 scan 同一大输入来分别生成多个 formal outputs。
- Python loop 只能用于 manifest、artifact catalog、field dictionary、输出文件枚举和小型 metadata/report 控制流，不能承担时间轴主路径计算。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- 时间主键、bar size、split 边界和 quality semantics 必须继承 mandate，不能静默改写。
- `asset_time_index.parquet` 必须表示单资产或逐资产时间轴，不得表达横截面排名面板。
- `quality_flags.parquet` 必须保留缺失、stale、异常价等语义，不能静默填补或删除。
- `split_sample_adequacy_report.yaml` 必须说明 train/test/backtest/holdout 的样本覆盖是否足以支持 TSS 后续阶段。

## Working Rules

1. 确认 mandate review closure 存在且 route 为 `time_series_signal`。
2. 读取 `contracts/artifacts/tss_data_ready_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_data_ready？` 后，才允许进入正式 build 准备。
5. 在 lineage-local `stage_program.yaml` 声明 `data_implementation_contract`，并在 build/review 前通过该门禁；门禁不通过时停在 author lane 修复程序，不得进入 review。
6. `data_implementation_contract` 门禁通过后才生成正式 `02_tss_data_ready/author/formal` 下的 required outputs。
7. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
8. 运行 `qros-validate-stage --stage tss_data_ready`。
9. validator 通过后停在 `tss_data_ready_review_confirmation_pending`，由用户显式进入 `qros-tss-data-ready-review`。
