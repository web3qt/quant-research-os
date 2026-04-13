---
name: qros-test-evidence-author
description: Use when reviewed train_freeze outputs must be frozen into formal test_evidence artifacts through grouped interactive confirmation.
---

# Test Evidence Author

## Purpose

只在 `train_freeze review` closure 完成之后，把 `04_train_freeze` 冻结成正式 `05_test_evidence` 产物。

这里的 `test_evidence` 不是在 QROS 框架仓里写一份 test 合同示意，而是要在当前 research repo 中把后续 `backtest_ready` 必须复用的 test 统计证据正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `05_test_evidence` 需要交付的 test 统计结果、admissibility 结果和冻结对象，而不是把 placeholder 文件或只有合同语义的说明文档当作 test_evidence 完成。

## Required Inputs

- `04_train_freeze/train_thresholds.json`
- `04_train_freeze/train_param_ledger.csv`
- `03_signal_ready/param_manifest.csv`
- `02_data_ready/aligned_bars/`
- `01_mandate/time_split.json`
- `04_train_freeze/stage_completion_certificate.yaml`

## Required Outputs

- `report_by_h.parquet`
- `symbol_summary.parquet`
- `admissibility_report.parquet`
- `test_gate_table.csv`
- `crowding_review.md`
- `selected_symbols_test.csv`
- `selected_symbols_test.parquet`
- `frozen_spec.json`
- `test_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `formal_gate_contract`
- `admissibility_contract`
- `audit_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 train_freeze 产物
- 当前阶段只冻结 test 合同，不替策略宣布交易层胜利
- formal gate 与 audit gate 必须显式分开
- 必须在当前研究仓真实生成独立测试窗上的统计证据、admissibility 结果和冻结 whitelist/best_h
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 test_evidence？`
- 不得在 test 窗里重估 train thresholds、whitelist 或 best_h

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 对 machine-readable 字段名、文件名、枚举值、命令、schema key 和上下游契约引用，保持英文或既有约定，不得为了中文化破坏契约。
- 对 hypothesis、counter-hypothesis、why、risk、evidence、uncertainty、kill reason、summary、rationale 等解释性内容，默认先判断是否适合中文；适合则优先用中文表达。
- 只有在英文表达更精确、需要与固定术语或上下游契约严格对齐、或用户明确要求英文时，才保留英文。

## Gate Discipline

### frozen_spec.json 完整性要求
`frozen_spec.json` 必须同时包含以下两个字段，缺一不可：
- `selected_symbols`：通过 admissibility 的 symbol 白名单
- `best_h`：冻结的预测 horizon

若任一字段缺失，不得宣布 test_evidence 完成。下游 backtest 阶段只允许消费已在本阶段显式冻结的 `selected_symbols` 和 `best_h`，不得自行增删。

### 拥挤审计必须仅属于 audit_contract 组
`crowding_review.md` 的结论只能影响 `audit_contract` 组（信息性 crowding 披露），**不得**作为 `formal_gate_contract` 的阻断条件：
- 允许：crowding 审计结论写入 `audit_contract`，供后续阶段参考
- 禁止：用 crowding 发现（如拥挤度高、排名靠后）直接阻止 formal gate 通过
- crowding 的处置边界必须在 `audit_contract` 冻结时明确写清，不允许在 formal_gate_contract 里静默夹带

### 严禁 Backtest 结果污染 Test Whitelist
在 `selected_symbols` 和 `best_h` 未完成冻结之前，**任何形式**的 backtest 结果（包括初探回测、粗糙回测）都不得被查看或引用：
- 若用户在冻结 frozen_spec 之前提及了任何 backtest 结果，必须明确触发 **CHILD LINEAGE**
- 只有 `frozen_spec.json` 已冻结，下游 backtest 阶段才能开始
- 不得用"test 窗 Sharpe 好看所以选这批 symbol"等逻辑倒推白名单

### 严禁在 Test 窗重估 Train 尺子
- 不得在 test 窗重新计算或调整 `train_thresholds.json` 中的任何阈值
- 不得以 test 窗表现为由修改 `best_h` 或 `selected_symbols`
- 以上任何行为必须触发 **CHILD LINEAGE**

## Working Rules

1. 确认 `04_train_freeze/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `formal_gate_contract`；确认 crowding 发现不得出现在此组作为阻断条件
4. 再收敛并确认 `admissibility_contract`
5. 再收敛并确认 `audit_contract`；确认 crowding_review 结论仅在此组记录
6. 最后确认 `delivery_contract`；核查 frozen_spec.json 同时包含 selected_symbols 和 best_h
7. 明确当前 research repo 中由谁负责真实生成 test 统计证据、admissibility 结果、selected symbols 和 frozen spec
8. 输出一份 grouped test_evidence summary
9. 只有用户最终批准后，才生成正式 `05_test_evidence` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 test_evidence 完成
