#!/usr/bin/env python3
"""Build a single evaluation prompt file with all training samples."""

import yaml
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "labeled_data" / "data_ready"
SKILLS_DIR = Path(__file__).parent.parent / "skills"

def main():
    review_rules = (SKILLS_DIR / "qros-data-ready-review" / "SKILL.md").read_text()
    failure_rules = (SKILLS_DIR / "qros-data-ready-failure" / "SKILL.md").read_text()

    samples = []
    train_dir = DATA_DIR / "train"
    for d in sorted(train_dir.iterdir()):
        if not d.is_dir():
            continue
        inp = yaml.safe_load((d / "input.yaml").read_text())
        out = yaml.safe_load((d / "output.yaml").read_text())
        samples.append({"id": d.name, **inp, "gt_class": out["correct_class"], "gt_severity": out.get("severity", "")})

    # Build the prompt
    prompt = f"""# QROS data_ready Failure Classification — Baseline Evaluation

You are a QROS data_ready stage review expert. For each sample below, classify the failure into one of 7 classes based on the SKILL rules.

## SKILL RULES

### qros-data-ready-review (Full):
```
{review_rules}
```

### qros-data-ready-failure (Full):
```
{failure_rules}
```

## FAILURE CLASSES

1. DATA_MISSING — 数据源或字段缺失，导致无法满足最小研究合同
2. DATA_MISALIGNMENT — 时间对齐、采样频率、session 边界、收益归属窗口不正确
3. LEAKAGE_FAIL — 未来函数、标签泄漏、样本外信息混入研究窗口
4. QUALITY_FAIL — 缺失、stale、outlier、停牌、异常成交等质量问题超出门槛
5. SCHEMA_FAIL — 字段名、类型、单位、语义不符合合同
6. REPRO_FAIL — 同一版本配置下无法稳定复现同一底表或统计摘要
7. SCOPE_FAIL — 数据准备已经偏离 mandate 声明的研究范围

## SEVERITY LEVELS

- FAIL-HARD: 存在时间错位/未来函数/关键字段缺失/schema错误到足以改变结论
- FAIL-SOFT: 问题集中于部分 symbol 或部分时间段，可通过收缩 Universe 或限制时间范围处理

## INSTRUCTIONS

For each sample, output EXACTLY this format (one line per sample):
SAMPLE_ID | PREDICTED_CLASS | SEVERITY | ONE_SENTENCE_RATIONALE

Do NOT look at the sample ID to guess the class. Classify based solely on the data spec content and SKILL rules.

---

## SAMPLES

"""

    for i, s in enumerate(samples):
        mandate = s.get("mandate_snapshot", {})
        lineage = s.get("lineage_context", {})
        prompt += f"""### Sample {i+1}: {s['id']}

**Research Idea**: {s.get('research_idea', 'N/A')}

**Mandate Snapshot**:
{yaml.dump(mandate, default_flow_style=False)}

**Data Spec Attempt**:
{s.get('data_spec_attempt', 'N/A')}

**Lineage Context**:
{yaml.dump(lineage, default_flow_style=False)}

---

"""

    out_path = DATA_DIR / "baseline_eval_prompt.md"
    out_path.write_text(prompt)
    print(f"Wrote evaluation prompt to {out_path} ({len(prompt)} chars, {len(samples)} samples)")

if __name__ == "__main__":
    main()
