# QROS 文档

## 快速开始

* [概述](README.md)
* [安装指南](guides/installation.md)
* [QROS 工作原理](guides/how-qros-works.md)
* [Codex 快速开始](guides/quickstart-codex.md)

## 研究流程

* [研究工作流 SOP](sop/main-flow/research_workflow_sop.md)
* [Mandate Admission 到 Mandate](guides/mandate-admission-flow.md)
* [研究 Session 使用](guides/qros-research-session-usage.md)
* [Closure Artifact Writer](guides/closure-artifact-writer-usage.md)

## Mandate SOP

* [Mandate](sop/main-flow/01_mandate_sop_cn.md)

## TSS 时序信号研究 SOP

* [TSS Data Ready](sop/main-flow/02_tss_data_ready_sop_cn.md)
* [TSS Signal Ready](sop/main-flow/03_tss_signal_ready_sop_cn.md)
* [TSS Train Freeze](sop/main-flow/04_tss_train_freeze_sop_cn.md)
* [TSS Test Evidence](sop/main-flow/05_tss_test_evidence_sop_cn.md)
* [TSS Backtest Ready](sop/main-flow/06_tss_backtest_ready_sop_cn.md)
* [TSS Holdout Validation](sop/main-flow/07_tss_holdout_validation_sop_cn.md)

## CSF 因子研究 SOP

* [CSF Data Ready](sop/main-flow/02_csf_data_ready_sop_cn.md)
* [CSF Signal Ready](sop/main-flow/03_csf_signal_ready_sop_cn.md)
* [CSF Train Freeze](sop/main-flow/04_csf_train_freeze_sop_cn.md)
* [CSF Test Evidence](sop/main-flow/05_csf_test_evidence_sop_cn.md)
* [CSF Backtest Ready](sop/main-flow/06_csf_backtest_ready_sop_cn.md)
* [CSF Holdout Validation](sop/main-flow/07_csf_holdout_validation_sop_cn.md)

## Review 与诊断

* [Stage Freeze Group Field Guide](guides/stage-freeze-group-field-guide.md)
* [Codex Stage Review Skill](guides/codex-stage-review-skill-usage.md)
* [Review 共享协议](guides/qros-review-shared-protocol.md)
* [Review 约束 Map](guides/qros-review-constraint-map.md)
* [阶段完成标准](sop/review/stage_completion_standard_cn.md)
* [阶段完成证书模板](sop/review/stage_completion_certificate_template_cn.md)
* [严格回测 Review 清单](sop/review/strict_backtest_review_checklist_cn.md)

## 诊断与验证

* [因子诊断](guides/qros-factor-diagnostics.md)
* [信号诊断](guides/qros-signal-diagnostics.md)
* [验证层级](guides/qros-verification-tiers.md)
* [Agent 行为评估](guides/qros-agent-behavior-eval.md)

## 失败处置

* [Lineage 变更控制 SOP](sop/failures/lineage_change_control_sop_cn.md)

## Legacy compatibility 文档

以下无前缀文档只保留给旧 lineage / 历史兼容引用。新 `time_series_signal` 研究线应使用上面的 TSS SOP；新 `cross_sectional_factor` 研究线应使用 CSF SOP。

* [Legacy Data Ready](sop/main-flow/02_data_ready_sop_cn.md)
* [Legacy Signal Ready](sop/main-flow/03_signal_ready_sop_cn.md)
* [Legacy Train Freeze](sop/main-flow/04_train_freeze_sop_cn.md)
* [Legacy Test Evidence](sop/main-flow/05_test_evidence_sop_cn.md)
* [Legacy Backtest Ready](sop/main-flow/06_backtest_ready_sop_cn.md)
* [Legacy Holdout Validation](sop/main-flow/07_holdout_validation_sop_cn.md)
* [Legacy Data Ready 失败 SOP](sop/failures/02_data_ready_failure_sop_cn.md)
* [Legacy Signal Ready 失败 SOP](sop/failures/03_signal_ready_failure_sop_cn.md)
* [Legacy Train Freeze 失败 SOP](sop/failures/04_train_freeze_failure_sop_cn.md)
* [Legacy Test Evidence 失败 SOP](sop/failures/05_test_evidence_failure_sop_cn.md)
* [Legacy Backtest 失败 SOP](sop/failures/06_backtest_failure_sop_cn.md)
* [Legacy Holdout 失败 SOP](sop/failures/07_holdout_failure_sop_cn.md)

## 治理与规则

* [Authoring 语言规范](guides/qros-authoring-language-discipline.md)
* [Anti-Drift 基线提升协议](anti_drift_baseline_promotion_protocol.md)
* [Drift Coverage Matrix](drift_coverage_matrix.md)
