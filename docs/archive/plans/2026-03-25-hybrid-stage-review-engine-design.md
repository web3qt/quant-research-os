# Hybrid Stage Review Engine Design

**Date:** 2026-03-25  
**Status:** Approved for implementation  
**Scope:** `Codex-only`, `first-wave stages = mandate / data_ready / signal_ready`

## Goal

把当前已有的 stage review skills、schema loaders 和 closure writer 接成一个真正可执行的 review 闭环：

- 自动识别当前 `lineage / stage / stage_dir`
- 自动加载 gate contract 与 review checklist
- 自动完成硬约束检查
- 消费单文件 `review_findings.yaml`
- 汇总成统一 verdict
- 自动写出 closure artifacts

## Non-Goals

- 不做自然语言语义理解型审查
- 不自动解析 markdown review notes
- 不覆盖 `train/test/backtest/holdout/shadow`
- 不实现完整研究运行时 CLI

## Input Model

第一版输入由三部分组成。

### 1. Rule Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`

### 2. Evidence Inputs

从当前 `stage_dir` 自动检查：

- `required_outputs`
- `artifact_catalog.md`
- `field_dictionary.md` 或 `*_fields.md`
- `run_manifest.json` 或 `repro_manifest.json`
- stage 推荐 gate doc
- checklist evidence 中可自动判定的文件/目录模式

### 3. Reviewer Input

固定单文件：

- `<stage_dir>/review_findings.yaml`

建议结构：

```yaml
reviewer_identity: codex
recommended_verdict: PASS
blocking_findings: []
reservation_findings: []
info_findings: []
residual_risks: []
rollback_stage:
allowed_modifications: []
downstream_permissions: []
```

## Automated Checks

engine 只自动处理“硬项”。

### Blocking By Default

- 上下文推断失败
- `required_outputs` 缺失
- `artifact_catalog.md` 缺失
- `field_dictionary.md` / `*_fields.md` 缺失
- `run_manifest.json` / `repro_manifest.json` 缺失
- 推荐 gate doc 缺失
- checklist evidence 中无歧义的文件/目录项全部缺失

### Reservation / Info

第一版不自动做保守 reservation 推断。  
这类问题统一由 reviewer 在 `review_findings.yaml` 中填写。

## Verdict Policy

### Default Resolution

- 若存在 blocking findings，默认 verdict = `RETRY`
- 若无 blocking 但存在 reservations，默认 verdict = `CONDITIONAL PASS`
- 若无 blocking 且无 reservations，默认 verdict = `PASS`

### Reviewer Override Rules

若 `review_findings.yaml` 提供 `recommended_verdict`：

- 可以更严格
- 不允许用 `PASS / CONDITIONAL PASS` 覆盖自动 blocking findings
- `PASS FOR RETRY` / `RETRY` 必须提供 `rollback_stage` 与 `allowed_modifications`
- `CHILD LINEAGE` / `NO-GO` 允许直接采用

## Output Model

engine 生成标准 payload 后，直接调用现有：

- `write_closure_artifacts(payload, cwd=None, explicit_context=None)`

正式输出：

- `<stage_dir>/latest_review_pack.yaml`
- `<stage_dir>/stage_gate_review.yaml`
- `<stage_dir>/stage_completion_certificate.yaml`
- `<lineage_root>/latest_review_pack.yaml`

## Repository Additions

```text
tools/review_skillgen/
  review_findings.py
  review_engine.py

scripts/
  run_stage_review.py
```

## Skill Integration

第一版不要求 skill 内部自动 shell-out 执行脚本。  
但生成的 skill 文本必须更新为：

1. reviewer 先补 `review_findings.yaml`
2. 然后运行 `python scripts/run_stage_review.py`

这样 skill、engine、closure writer 才形成完整链路。

## Success Criteria

若第一版完成，应满足：

- 在 `outputs/<lineage>/<stage>/` 目录内可直接运行 `python scripts/run_stage_review.py`
- engine 能加载当前 stage contract/checklist
- engine 能校验 `review_findings.yaml`
- engine 能自动发现硬缺口并生成 verdict
- engine 能写出 closure artifacts
- 生成后的 skills 明确指向这条执行路径
