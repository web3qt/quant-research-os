from pathlib import Path


def test_stage_failure_handler_skill_exists_and_covers_failure_flow() -> None:
    skill_path = Path("skills/qros-stage-failure-handler/SKILL.md")
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    assert "data_ready" in content
    assert "signal_ready" in content
    assert "train_freeze" in content
    assert "test_evidence" in content
    assert "backtest_ready" in content
    assert "holdout_validation" in content
    assert "shadow" in content
    assert "PASS FOR RETRY" in content
    assert "RETRY" in content
    assert "NO-GO" in content
    assert "CHILD LINEAGE" in content
    assert "stop normal stage progression" in content.lower() or "停止正常推进" in content
    assert "failure_disposition.yaml" in content


def test_stage_failure_handler_bootstrap_expectation_is_present() -> None:
    bootstrap_path = Path("tests/test_project_bootstrap.py")
    content = bootstrap_path.read_text(encoding="utf-8")

    assert "skills/qros-stage-failure-handler/SKILL.md" in content
