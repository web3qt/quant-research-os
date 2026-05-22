---
name: qros-data-ready-author
description: Use when a reviewed mandate must be frozen into formal data_ready artifacts through grouped interactive confirmation.
---

# Data Ready Author

## Purpose

只在 `mandate review` closure 完成之后，把 `01_mandate` 冻结成正式 `02_data_ready` 产物。

这里的 `data_ready` 不是静默跑数据，而是交互式冻结“后续研究共同依赖的数据研究底座”。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `02_data_ready` 需要交付的共享数据层，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 data_ready 完成。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage data_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Required Inputs

- `01_mandate/mandate.md`
- `01_mandate/research_scope.md`
- `01_mandate/time_split.json`
- `01_mandate/run_config.toml`
- `01_mandate/stage_completion_certificate.yaml`

## Required Outputs

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
- `data_ready_gate_decision.md`
- `run_manifest.json`
- `rebuild_data_ready.py` or equivalent program snapshot
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `extraction_contract`
- `quality_semantics`
- `universe_admission`
- `shared_derived_layer`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 mandate 产物
- 可以冻结共享研究底座与共享派生层
- 不得产出 thesis-specific signal 或收益结论
- 必须在当前研究仓真实生成可供下游消费的 `aligned_bars/`、共享缓存和相关证据
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- 必须把 `data_viability_contract`、`time_coverage_contract`、`provenance_viability_contract` 作为进入 reviewer 之前的 preflight 事实先锁定；reviewer 不是第一次发现“这批数据是否真实可用、覆盖到哪、来自哪里”的地方
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 必须把本阶段真实使用的数据处理程序保存到 stage 目录，并登记到 `run_manifest.json`
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups
- 五组全部确认后，才允许最终 `是否按以上内容冻结 data_ready？`
- 不得静默修改 mandate 冻结的时间边界和 universe 口径

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 排除项声明（即使为空也必须显式记录）
`universe_exclusions.csv` 和 `universe_exclusions.md` 必须存在：
- 有排除项时：列出每条排除原因
- **无排除项时**：必须显式声明 `no_exclusions: true`，不允许用空文件或省略代替"没有排除"

### 质量语义：保留标记，不静默填补
`aligned_bars/` 中的缺失值、stale 价、outlier 必须用**显式质量标记**保留，不允许：
- 静默 forward-fill
- 静默删除有问题的 bar

`quality_semantics` 冻结时，必须明确列出每种异常情况的处理方式（标记/删除/保留），并在 `data_contract.md` 中写清语义。

### 覆盖异常必须有解释
`validation_report.md` 中出现的任何覆盖率异常（如基准腿覆盖低、某 symbol 时间段大量缺失）必须有明确解释。无法解释的覆盖异常**不得**通过 formal gate。

## Working Rules

1. 确认 `01_mandate/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `extraction_contract`，先把 `time_coverage_contract` 锁定，确保 `time_boundary` 与真实数据覆盖一致
3. 再收敛并确认 `quality_semantics`；明确每种异常的处理语义（标记/保留，不静默填）
4. 再收敛并确认 `universe_admission`；确认排除项已显式记录（即使为空）
5. 再收敛并确认 `shared_derived_layer`
6. 最后确认 `delivery_contract`，并把 `data_viability_contract` 锁定，确保 formal machine artifacts 不是 placeholder
7. 明确当前 research repo 中由谁负责真实生成 `aligned_bars/`、rolling 缓存、coverage/QC 证据和 shared derived outputs
8. 输出一份 grouped data_ready summary
9. 只有用户最终批准后，才生成正式 `02_data_ready` artifacts
10. 验证 `validation_report.md` 中所有覆盖异常已有解释
11. 生成 `run_manifest.json`，写清 runtime 版本、program_artifacts、replay_command 和输入根目录，并把 `provenance_viability_contract` 锁定
12. 保存 `rebuild_data_ready.py` 或等价 stage-local 程序快照；若使用自定义程序，不得只引用 notebook 名称
13. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
14. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 data_ready 完成
