from __future__ import annotations

from pathlib import Path

from tests.helpers.skill_test_utils import skill_text


SUPPORTED_CSF_STAGES = [
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
]


def test_factor_diagnostics_skill_declares_read_only_boundaries() -> None:
    content = skill_text("qros-factor-diagnostics")

    assert "./.qros/bin/qros-factor-diagnostics" in content
    assert "只读" in content
    assert "不替代 `qros-review`" in content
    assert "不写 `review/closure`" in content
    assert "不修改任何 `*_gate_decision.md`" in content
    assert "不写 `stage_completion_certificate.yaml`" in content
    assert "不推进 stage" in content
    assert "PASS / FAIL" in content


def test_factor_diagnostics_docs_position_command_as_optional_diagnostics() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    codex = Path("docs/README.codex.md").read_text(encoding="utf-8")
    usage = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/qros-factor-diagnostics.md").read_text(encoding="utf-8")
    combined = "\n".join([readme, codex, usage, guide])

    assert "$qros-factor-diagnostics" in combined
    assert "./.qros/bin/qros-factor-diagnostics" in combined
    assert "可选 diagnostics" in combined
    assert "不是 review" in combined
    assert "不是 gate" in combined
    assert "不写 review closure" in combined


def test_factor_diagnostics_docs_show_codex_prompt_examples_before_shell_debugging() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    codex = Path("docs/README.codex.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/qros-factor-diagnostics.md").read_text(encoding="utf-8")
    usage = Path("docs/guides/qros-research-session-usage.md").read_text(encoding="utf-8")
    skill = skill_text("qros-factor-diagnostics")

    for content in (readme, codex, guide, usage, skill):
        assert "$qros-factor-diagnostics 看下当前 lineage 的因子诊断" in content
        assert "$qros-factor-diagnostics 看下 csf_test_evidence 阶段" in content
        assert "$qros-factor-diagnostics 看下 csf_backtest_ready 阶段" in content
        assert "$qros-factor-diagnostics 看下 csf_holdout_validation 阶段" in content

    assert "普通用户不需要手动执行 `./.qros/bin/qros-factor-diagnostics`" in guide
    assert "不要要求用户手动执行 shell wrapper" in skill
    assert guide.index("在 Codex 里直接问") < guide.index("维护者 / 调试入口")


def test_factor_diagnostics_guide_lists_supported_csf_stages() -> None:
    guide = Path("docs/guides/qros-factor-diagnostics.md").read_text(encoding="utf-8")

    for stage in SUPPORTED_CSF_STAGES:
        assert stage in guide
