---
name: qros-train-freeze-author
description: Use when reviewed signal_ready outputs must be frozen into formal train-freeze artifacts through grouped interactive confirmation.
---

# Train Freeze Author

## Purpose

只在 `signal_ready review` closure 完成之后，把 `03_signal_ready` 冻结成正式 `04_train_freeze` 产物。

这里的 `train_freeze` 不是在 QROS 框架仓里写一份训练合同示意，而是要在当前 research repo 中把后续 `test_evidence` 必须复用的 train 冻结结果正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `04_train_freeze` 需要交付的 thresholds、quality 证据和参数台账，而不是把 placeholder 文件或只有合同语义的说明文档当作 train_freeze 完成。

## Required Inputs

- `03_signal_ready/param_manifest.csv`
- `03_signal_ready/params/`
- `03_signal_ready/signal_coverage.csv`
- `03_signal_ready/signal_fields_contract.md`
- `03_signal_ready/stage_completion_certificate.yaml`
- `01_mandate/time_split.json`

## Required Outputs

- `train_thresholds.json`
- `train_quality.parquet`
- `train_param_ledger.csv`
- `train_rejects.csv`
- `train_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `threshold_contract`
- `quality_filters`
- `param_governance`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 signal_ready 产物
- 当前阶段只冻结 train 合同，不替策略宣布“赢家”
- 参数 ledger 必须完整保留，reject ledger 必须单独落盘
- 必须在当前研究仓真实生成训练窗估计得到的 thresholds、quality 证据、kept or rejected ledger
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 train_freeze？`
- 不得借用 test/backtest 结果回写 train 尺子

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Gate Discipline

### 严禁用 Test/Backtest 结果回写 Train 尺子
这是最严重的信息泄露。以下任何行为都必须触发 **CHILD LINEAGE**：
- 用已知 test 窗结果反推阈值
- 用回测 Sharpe 选择分位切点
- 基于下游表现调整质量过滤条件

如果用户提到"根据 test 结果调一下阈值"，必须明确拒绝并说明原因。

### Reject Ledger 必须有原因
`train_rejects.csv` 中每条拒绝记录必须包含非空的 `reject_reason` 字段。参数粗筛的理由只能是：
- 超出 mandate 参数边界
- 信号计算失败
- 覆盖率低于质量阈值

不允许以"收益不好"为由拒绝参数。

### 阈值语义分离
`train_thresholds.json` 必须明确区分以下四类，不允许混用在同一层级下：
- `quantile_thresholds`：信号分位切点
- `regime_cuts`：市场状态切点（训练窗分布特征需单独记录）
- `quality_filters`：质量过滤条件
- `auxiliary_conditions`：辅助条件切点

### 搜索过程统计
必须产出 `search_statistics.json`，包含：total_params / passed / rejected / median_metric / best_metric / z_score（或等价统计量）。缺少搜索过程统计不得宣布 train 完成。

## Working Rules

1. 确认 `03_signal_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `threshold_contract`；核查阈值语义分离（见上）
4. 再收敛并确认 `quality_filters`；确认质量过滤与阈值语义隔离
5. 再收敛并确认 `param_governance`；确认 reject_reason 字段必须非空
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 thresholds、quality 证据、param ledger 和 reject ledger
8. 输出一份 grouped train_freeze summary
9. 只有用户最终批准后，才生成正式 `04_train_freeze` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 train_freeze 完成
