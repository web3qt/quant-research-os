---
name: qros-csf-train-freeze-author
description: Use when reviewed csf_signal_ready outputs must be frozen into formal csf_train_freeze artifacts through grouped interactive confirmation.
---

# CSF Train Freeze Author

## Purpose

只在 `csf_signal_ready review` closure 完成之后，把 `03_csf_signal_ready` 冻结成正式 `04_csf_train_freeze` 产物。

这里的 `csf_train_freeze` 不是给因子重新发明规则，而是把 cross-sectional factor 路线后续必须复用的预处理尺子、中性化尺子和分组尺子正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `04_csf_train_freeze` 需要交付的阈值、质量证据和参数台账，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_train_freeze 完成。

## Required Inputs

- `03_csf_signal_ready/factor_manifest.yaml`
- `03_csf_signal_ready/factor_panel.parquet`
- `03_csf_signal_ready/factor_coverage.parquet`
- `03_csf_signal_ready/factor_contract.md`
- `03_csf_signal_ready/stage_completion_certificate.yaml`

## Required Outputs

- `csf_train_freeze.yaml`
- `train_quality.parquet`
- `train_variant_ledger.csv`
- `train_rejects.csv`
- `train_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `preprocess_contract`
- `neutralization_contract`
- `ranking_bucket_contract`
- `rebalance_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_signal_ready 产物
- 当前阶段只冻结 train 尺子，不替因子宣布赢家
- 必须在当前 research repo 里真实生成训练窗估计得到的预处理、中性化和分组尺子
- 不得产出任何时序主线措辞、best_h、预测 horizon 或单资产命中率语义
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_train_freeze？`
- 不得借用 test/backtest 结果回写 train 尺子

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Gate Discipline

### 严禁用下游结果回写 train 尺子
以下任何行为都必须触发 **CHILD LINEAGE**：
- 用 test/backtest 结果反推阈值
- 用下游表现选择分组切点
- 基于后续表现调整中性化条件

### 参数台账必须完整
`train_variant_ledger.csv` 中的所有候选组合都必须有可追溯身份，拒绝项也必须保留原因。

### 阈值语义分离
`csf_train_freeze.yaml` 必须明确区分：
- `preprocess_rules`
- `neutralization_rules`
- `ranking_bucket_rules`
- `rebalance_rules`
- `auxiliary_conditions`

## Working Rules

1. 确认 `03_csf_signal_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `preprocess_contract`
3. 再收敛并确认 `neutralization_contract`
4. 再收敛并确认 `ranking_bucket_contract`
5. 再收敛并确认 `rebalance_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 train 尺子、quality 证据、param ledger 和 reject ledger
8. 输出一份 grouped csf_train_freeze summary
9. 只有用户最终批准后，才生成正式 `04_csf_train_freeze` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_train_freeze 完成
