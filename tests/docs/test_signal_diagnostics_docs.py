from __future__ import annotations

from pathlib import Path

from tests.helpers.skill_test_utils import skill_text


SUPPORTED_TSS_STAGES = [
    "tss_data_ready",
    "tss_signal_ready",
    "tss_train_freeze",
    "tss_test_evidence",
    "tss_backtest_ready",
    "tss_holdout_validation",
]


def test_signal_diagnostics_skill_declares_read_only_boundaries() -> None:
    content = skill_text("qros-signal-diagnostics")

    assert "./.qros/bin/qros-signal-diagnostics" in content
    assert "只读" in content
    assert "不替代 `qros-review`" in content
    assert "不写 `review/closure`" in content
    assert "不修改任何 `*_gate_decision.md`" in content
    assert "不写 `stage_completion_certificate.yaml`" in content
    assert "不推进 stage" in content
    assert "PASS / FAIL" in content


def test_signal_diagnostics_docs_show_codex_prompt_examples_before_shell_debugging() -> None:
    guide = Path("docs/guides/qros-signal-diagnostics.md").read_text(encoding="utf-8")
    skill = skill_text("qros-signal-diagnostics")
    readme = Path("README.md").read_text(encoding="utf-8")
    codex = Path("docs/README.codex.md").read_text(encoding="utf-8")

    for content in (guide, skill, readme, codex):
        assert "$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断" in content
        assert "$qros-signal-diagnostics 看下 tss_backtest_ready 阶段的成本后收益、回撤和换手" in content
        assert "$qros-signal-diagnostics 看下 tss_holdout_validation 阶段有没有样本外退化" in content

    assert "$qros-signal-diagnostics 帮我解释这条 TSS 研究线的 test evidence" in guide
    assert "$qros-signal-diagnostics 帮我解释这条 TSS 研究线的 test evidence" in skill
    assert "普通用户不需要手动执行 `./.qros/bin/qros-signal-diagnostics`" in guide
    assert "不要要求用户手动执行 shell wrapper" in skill
    assert guide.index("在 Codex 里直接问") < guide.index("维护者 / 调试入口")


def test_signal_diagnostics_docs_require_chinese_interpretation_not_metric_dump() -> None:
    guide = Path("docs/guides/qros-signal-diagnostics.md").read_text(encoding="utf-8")
    skill = skill_text("qros-signal-diagnostics")
    combined = "\n".join([guide, skill])

    assert "$qros-signal-diagnostics mean_rank_ic 小于 0 说明什么，按高信号做多会不会站错方向" in combined
    assert "$qros-signal-diagnostics 不要只给数字，用中文解释这些指标说明什么" in combined
    assert "不要只输出指标数字" in skill
    assert "必须用中文解释核心指标含义" in skill
    assert "跟当前策略的关系" in skill
    assert "mean_rank_ic < 0" in skill
    assert "信号方向可能反了" in skill
    assert "高信号做多" in skill
    assert "系统性站错方向" in skill
    assert "forward return" in skill
    assert "事件数量" in skill


def test_signal_diagnostics_guide_lists_supported_tss_stages() -> None:
    guide = Path("docs/guides/qros-signal-diagnostics.md").read_text(encoding="utf-8")

    for stage in SUPPORTED_TSS_STAGES:
        assert stage in guide
