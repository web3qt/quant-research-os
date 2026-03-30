#!/usr/bin/env python3
"""Baseline classification evaluation for QROS data_ready failure classes."""

import yaml
import os
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "labeled_data" / "data_ready"
SKILLS_DIR = Path(__file__).parent.parent / "skills"

FAILURE_CLASSES = [
    "DATA_MISSING",
    "DATA_MISALIGNMENT",
    "LEAKAGE_FAIL",
    "QUALITY_FAIL",
    "SCHEMA_FAIL",
    "REPRO_FAIL",
    "SCOPE_FAIL",
]

def load_skill_rules():
    """Load the data_ready failure handler skill rules."""
    review_path = SKILLS_DIR / "qros-data-ready-review" / "SKILL.md"
    failure_path = SKILLS_DIR / "qros-data-ready-failure" / "SKILL.md"
    review = review_path.read_text() if review_path.exists() else ""
    failure = failure_path.read_text() if failure_path.exists() else ""
    return review, failure

def load_samples(split="train"):
    """Load all samples from a split directory."""
    samples = []
    split_dir = DATA_DIR / split
    if not split_dir.exists():
        return samples
    for sample_dir in sorted(split_dir.iterdir()):
        if not sample_dir.is_dir():
            continue
        input_path = sample_dir / "input.yaml"
        output_path = sample_dir / "output.yaml"
        if input_path.exists() and output_path.exists():
            with open(input_path) as f:
                inp = yaml.safe_load(f)
            with open(output_path) as f:
                out = yaml.safe_load(f)
            samples.append({
                "id": sample_dir.name,
                "input": inp,
                "ground_truth": out["correct_class"],
                "severity": out.get("severity", "UNKNOWN"),
                "rationale": out.get("classification_rationale", ""),
            })
    return samples

def build_classification_prompt(sample, review_rules, failure_rules):
    """Build a prompt for classification."""
    return f"""你是一个 QROS data_ready 阶段的审查专家。根据以下 SKILL 规则，判断这个数据规格中的问题属于哪个 failure class。

## 可选的 7 个 Failure Class:

1. DATA_MISSING — 数据源或字段缺失，导致无法满足最小研究合同
2. DATA_MISALIGNMENT — 时间对齐、采样频率、session 边界、收益归属窗口不正确
3. LEAKAGE_FAIL — 未来函数、标签泄漏、样本外信息混入研究窗口
4. QUALITY_FAIL — 缺失、stale、outlier、停牌、异常成交等质量问题超出门槛
5. SCHEMA_FAIL — 字段名、类型、单位、语义不符合合同
6. REPRO_FAIL — 同一版本配置下无法稳定复现同一底表或统计摘要
7. SCOPE_FAIL — 数据准备已经偏离 mandate 声明的研究范围

## Data Ready Review 规则摘要:
{review_rules[:2000]}

## Data Ready Failure Handler 规则摘要:
{failure_rules[:3000]}

## 待分类样本:

研究想法: {sample['input'].get('research_idea', 'N/A')}

Mandate 摘要:
{yaml.dump(sample['input'].get('mandate_snapshot', {}), default_flow_style=False)}

数据规格尝试:
{sample['input'].get('data_spec_attempt', 'N/A')}

Lineage 上下文:
{yaml.dump(sample['input'].get('lineage_context', {}), default_flow_style=False)}

请输出 JSON 格式:
{{"predicted_class": "<CLASS_NAME>", "severity": "FAIL-HARD|FAIL-SOFT|PASS_WITH_RESTRICTIONS", "rationale": "<简短理由>"}}"""

def main():
    review_rules, failure_rules = load_skill_rules()

    for split in ["train", "test"]:
        samples = load_samples(split)
        if not samples:
            print(f"\n=== {split.upper()} === No samples found")
            continue

        print(f"\n=== {split.upper()} ({len(samples)} samples) ===\n")

        for i, sample in enumerate(samples):
            prompt = build_classification_prompt(sample, review_rules, failure_rules)
            print(f"--- Sample {i+1}: {sample['id']} ---")
            print(f"Ground Truth: {sample['ground_truth']} ({sample['severity']})")
            print(f"PROMPT_START")
            print(prompt)
            print(f"PROMPT_END")
            print()

if __name__ == "__main__":
    main()
