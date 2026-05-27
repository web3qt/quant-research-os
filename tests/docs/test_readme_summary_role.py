from pathlib import Path


def test_readme_foregrounds_summary_role_priorities() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    combined = readme

    assert "mandate_admission -> mandate_freeze_confirmation_pending -> 01_mandate" in combined
    assert "02_tss_data_ready" in combined
    assert "07_tss_holdout_validation" in combined
    assert "cross_sectional_factor" in combined
    assert "框架仓" in readme
    assert "qros-research-session" in combined
    assert "qros-progress" in combined
    assert "qros-factor-diagnostics" in combined
    assert "qros-signal-diagnostics" in combined
    assert "只读" in combined
    assert "1191 条 pytest collected tests" in combined
    assert "codex-cli 0.134.0" in combined
    assert "2.1.152 (Claude Code)" in combined
    assert "55 个 public skill bundles" in combined
    assert "19 stage-program keys" in combined
    assert "docs/guides/qros-factor-diagnostics.md" in combined
    assert "docs/guides/qros-signal-diagnostics.md" in combined
    assert "-> 02_data_ready" not in combined
    assert "-> 06_backtest" not in combined
    assert "-> 07_holdout" not in combined
