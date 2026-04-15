# QROS Multi-Stage Validation Findings Report

**Lineage**: btc-leads-alt-30m
**Date**: 2026-03-30
**Method**: Intentionally defective artifacts reviewed by stage-specific review skills
**Total Blocking Findings**: 55 across 6 stages (all NO-GO)

---

## Pattern 1: 全样本统计量泄漏 (Full-Sample Leakage)

**Incidence**: 18 blocking findings across 4 stages

This is the most common and most dangerous pattern. It appears at data_ready (BF-001, BF-002, BF-005) and propagates through signal_ready (BF-002), train_freeze (BF-001, BF-002, BF-003, BF-004, BF-005), test_evidence (RF-003), and holdout (RF-003).

**Mechanism**: Full-sample (train+test+holdout) statistics are used for normalization, quantile thresholds, and outlier boundaries. This means test-period information is embedded in objects that downstream stages treat as "frozen" from train-only data.

**Why it's hard to catch**: Full-sample statistics often produce "better" metrics (higher R², tighter confidence intervals, more stable thresholds). The improvement is real — it genuinely reduces variance — but it comes at the cost of independence. The improvement is seductive because it makes results look cleaner.

**Propagation chain**:
```
data_ready: full-sample z-score, full-sample outlier boundaries
  → signal_ready: full-sample signal_zscore normalization, full-sample quantile thresholds
    → train_freeze: full-sample threshold estimation, test-based quality calibration
      → test_evidence: test-window threshold re-estimation
        → holdout: contaminated thresholds in frozen config
```

**Detection rule**: Any mention of "全样本", "full-sample", or normalization statistics without explicit "train window" or "expanding window" qualifier should trigger LEAKAGE_FAIL.

---

## Pattern 2: 上游 Gate Bypass (Upstream Gate Bypass)

**Incidence**: 6 blocking findings (one per downstream stage)

Every downstream stage (signal_ready BF-009, train_freeze BF-009, test_evidence BF-012, backtest BF-008, holdout BF-008) entered despite upstream receiving NO-GO verdicts.

**Mechanism**: The author skill requires confirming upstream `stage_completion_certificate.yaml` exists, but this check is only in the author workflow — not in the review checklist. The review skill has no blocking item to verify upstream gate status. This means a reviewer cannot catch the bypass; it must be caught by the author or an orchestrator.

**Why it's hard to catch**: The author skill's working rules say "确认上游证书已存在" but the review skill's formal gate has no corresponding blocking checklist item. The review focuses on the current stage's artifacts, not upstream governance. Only the test_evidence review has 7 statistical diagnostic items — none check upstream gate status.

**Fix applied**: Added blocking checklist item to all 6 review SKILLs: "上游 stage_completion_certificate.yaml 存在且 verdict 非 NO-GO / CHILD LINEAGE".

**Detection rule**: Before reviewing any stage artifacts, verify upstream stage_completion_certificate.yaml exists and contains a PASS, CONDITIONAL PASS, or GO verdict.

---

## Pattern 3: Required Artifacts Missing (Missing Standalone Artifacts)

**Incidence**: 7 blocking findings (one per stage)

Every stage lists required machine-readable outputs (parquet, csv, json) in its delivery_contract, but only a narrative YAML file exists. No standalone artifacts were generated.

**Mechanism**: The author skill explicitly states "placeholder parquet/csv/json/md、空目录或只有说明文档都不能算正式完成", but this discipline is not enforced. The stage_completion_certificate should only be generated after all required artifacts exist, but in practice the certificate is never generated because the pipeline never reaches formal completion.

**Why it's hard to catch**: The review skill's formal gate includes "required_outputs 全部存在", but when the reviewer only sees the narrative YAML, the "required outputs" section appears to describe the contract — not the actual artifacts. Without listing the directory contents and cross-referencing, the gap is invisible.

**Incidence by stage**:
| Stage | Required Artifacts Missing |
|-------|------------------------|
| data_ready | 13 (aligned_bars/, rolling_stats/, qc_report, etc.) |
| signal_ready | 8 (param_manifest.csv, params/*.parquet, etc.) |
| train_freeze | 7 (train_thresholds.json, etc.) |
| test_evidence | 11 (report_by_h.parquet, etc.) |
| backtest | 8 (engine_compare.csv, vectorbt/, etc.) |
| holdout | 6 (holdout_run_manifest.json, etc.) |

**Detection rule**: Review checklist should include a hard check: "ls <stage_dir> contents cross-referenced against delivery_contract required_outputs list. Any missing file is FAIL-HARD."

---

## Pattern 4: 事后调参 (Post-Hoc Parameter Tuning)

**Incidence**: 13 blocking findings across 4 stages

This pattern appears when downstream stages use results to modify upstream frozen objects, either explicitly or implicitly.

**Mechanism**: Each stage's formal gate explicitly forbids using downstream information to modify upstream frozen objects, but the discipline is enforced through author skill working rules, not through hard automated checks. The temptation is strong because adjusting parameters based on results "improves" the immediate metrics.

**Variants by stage**:

| Stage | Instance | What was modified | Based on |
|-------|---------|------------------|------------|
| train_freeze | BF-003 | min_response_bars 15→20 | test window performance |
| train_freeze | BF-004 | signal_quality_score calibration | test-window Sharpe |
| train_freeze | BF-005 | param selection (top 50% by Sharpe) | in-sample performance |
| test_evidence | BF-001 | quantile thresholds re-estimated | test window distribution |
| test_evidence | BF-002 | backtest results viewed | backtest Sharpe before frozen_spec |
| test_evidence | BF-003 | symbol selection (3/18 kept) | test-period p-values |
| test_evidence | BF-009 | regime filter promoted to formal gate | test-period regime analysis |
| backtest | BF-002 | ETH added to whitelist | backtest Sharpe comparison |
| backtest | BF-003 | LINK→DOT substitution | backtest Sharpe comparison |
| holdout | BF-001 | vol_regime threshold adjusted | holdout event trigger rate |
| holdout | BF-002 | min_response_bars reduced | holdout LINK coverage |
| holdout | BF-005 | holdout+backtest results merged | combined Sharpe improvement |
| holdout | BF-006 | time boundary expanded | holdout sample size |

**Why it's hard to catch**: Each individual instance looks reasonable in isolation ("test results suggest adjusting this parameter"). The pattern only becomes visible when you track all parameter modifications across stages and cross-reference against freeze timestamps. No single stage review can see the full picture.

**Detection rule**: Every freeze decision must be timestamped. Any modification to a frozen object after its freeze timestamp requires CHILD LINEAGE, regardless of the rationale.

---

## Cross-Pattern Statistics

| Pattern | Blocking Findings | Stages Affected | Avg. Severity |
|---------|-----------------|----------------|-------------|
| Full-sample leakage | 18 | data_ready → holdout | FAIL-HARD |
| Upstream gate bypass | 6 | all downstream | FAIL-HARD |
| Missing artifacts | 7 | all stages | FAIL-HARD |
| Post-hoc tuning | 13 | train_freeze → holdout | FAIL-HARD (5) / SCOPE (3) |

## Most Contagious Failure Classes

| Failure Class | Avg. Contamination Depth | Most Common Stage |
|--------------|----------------------|-----------------|
| LEAKAGE_FAIL / LEAKED_FREEZE_FAIL | 5 stages | data_ready (origin) |
| REPRO_FAIL | 4-5 stages | any stage |
| SCOPE_FAIL | 3-4 stages | any stage |
| SELECTION_BIAS_FAIL | 3 stages | test_evidence (origin) |

## Key Insight

The most impactful single fix is preventing Pattern 1 (full-sample leakage) at the earliest possible stage (data_ready). Because leakage propagates through normalization chains and threshold estimation, fixing it later requires re-running all downstream stages. Pattern 2 (gate bypass) is now addressed by the review checklist addition. Pattern 3 (missing artifacts) requires enforcement in the stage completion workflow. Pattern 4 (post-hoc tuning) requires timestamp-based freeze auditing.

Patterns 1 and 4 are the hardest to detect automatically because they produce "better" results that don't look like errors. Pattern 2 is the easiest to prevent structurally. Pattern 3 is the most straightforward to detect but the most tedious to enforce.
