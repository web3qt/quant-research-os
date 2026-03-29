from pathlib import Path


def test_research_session_skill_exists_and_covers_first_wave_flow() -> None:
    skill_path = Path(".agents/skills/qros-research-session/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "idea_intake" in content
    assert "idea_intake_confirmation_pending" in content
    assert "mandate" in content
    assert "mandate review" in content.lower()
    assert "mandate_confirmation_pending" in content
    assert "CONFIRM_MANDATE" in content
    assert "是否确认进入 mandate" in content
    assert "observation" in content
    assert "counter-hypothesis" in content or "counter_hypothesis" in content
    assert "kill criteria" in content
    assert "CONFIRM_IDEA_INTAKE" in content
    assert "data source" in content.lower() or "数据来源" in content
    assert "bar_size" in content or "1m" in content
    assert "research_intent" in content
    assert "scope_contract" in content
    assert "data_contract" in content
    assert "execution_contract" in content
    assert "data_ready_confirmation_pending" in content
    assert "extraction_contract" in content
    assert "shared_derived_layer" in content
    assert "是否按以上内容冻结 data_ready" in content
    assert "signal_ready_confirmation_pending" in content
    assert "signal_expression" in content
    assert "param_identity" in content
    assert "是否按以上内容冻结 signal_ready" in content
    assert "train_freeze_confirmation_pending" in content
    assert "window_contract" in content
    assert "threshold_contract" in content
    assert "quality_filters" in content
    assert "param_governance" in content
    assert "是否按以上内容冻结 train_freeze" in content
    assert "test_evidence_confirmation_pending" in content
    assert "formal_gate_contract" in content
    assert "admissibility_contract" in content
    assert "audit_contract" in content
    assert "是否按以上内容冻结 test_evidence" in content
    assert "backtest_ready_confirmation_pending" in content
    assert "execution_policy" in content
    assert "portfolio_policy" in content
    assert "risk_overlay" in content
    assert "engine_contract" in content
    assert "是否按以上内容冻结 backtest_ready" in content
    assert "holdout_validation_confirmation_pending" in content
    assert "reuse_contract" in content
    assert "drift_audit" in content
    assert "failure_governance" in content
    assert "是否按以上内容冻结 holdout_validation" in content
    assert "~/.qros/bin/qros-session" in content


def test_research_session_usage_doc_mentions_single_entry_flow() -> None:
    usage_path = Path("docs/experience/qros-research-session-usage.md")
    content = usage_path.read_text(encoding="utf-8")

    assert usage_path.exists()
    assert "~/.qros/bin/qros-session" in content
    assert "qros-research-session" in content
    assert "data_ready" in content
    assert "mandate_confirmation_pending" in content
    assert "idea_intake_confirmation_pending" in content
    assert "用户不需要记住内部命令" in content
    assert "intake" in content.lower()
    assert "kill criteria" in content
    assert "--confirm-intake" in content
    assert "是否确认进入 mandate" in content
    assert "数据来源" in content
    assert "1m" in content or "5m" in content or "15m" in content
    assert "research_intent" in content
    assert "scope_contract" in content
    assert "data_ready_confirmation_pending" in content
    assert "shared_derived_layer" in content
    assert "是否按以上内容冻结 data_ready" in content
    assert "signal_ready_confirmation_pending" in content
    assert "signal_expression" in content
    assert "是否按以上内容冻结 signal_ready" in content
    assert "train_freeze_confirmation_pending" in content
    assert "window_contract" in content
    assert "是否按以上内容冻结 train_freeze" in content
    assert "test_evidence_confirmation_pending" in content
    assert "formal_gate_contract" in content
    assert "是否按以上内容冻结 test_evidence" in content
    assert "backtest_ready_confirmation_pending" in content
    assert "execution_policy" in content
    assert "是否按以上内容冻结 backtest_ready" in content
    assert "holdout_validation_confirmation_pending" in content
    assert "reuse_contract" in content
    assert "是否按以上内容冻结 holdout_validation" in content


def test_data_ready_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-data-ready-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "data_ready" in content.lower()
    assert "extraction_contract" in content
    assert "quality_semantics" in content
    assert "universe_admission" in content
    assert "shared_derived_layer" in content
    assert "delivery_contract" in content


def test_idea_intake_author_skill_requires_interview() -> None:
    skill_path = Path(".agents/skills/qros-idea-intake-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "intake" in content.lower()
    assert "observation" in content
    assert "counter-hypothesis" in content or "counter_hypothesis" in content
    assert "kill criteria" in content
    assert "不能只根据用户一句原始 idea" in content


def test_signal_ready_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-signal-ready-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "signal_ready" in content.lower()
    assert "signal_expression" in content
    assert "param_identity" in content
    assert "time_semantics" in content
    assert "signal_schema" in content
    assert "delivery_contract" in content


def test_train_freeze_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-train-freeze-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "train_freeze" in content.lower()
    assert "window_contract" in content
    assert "threshold_contract" in content
    assert "quality_filters" in content
    assert "param_governance" in content
    assert "delivery_contract" in content


def test_test_evidence_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-test-evidence-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "test_evidence" in content.lower()
    assert "window_contract" in content
    assert "formal_gate_contract" in content
    assert "admissibility_contract" in content
    assert "audit_contract" in content
    assert "delivery_contract" in content


def test_backtest_ready_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-backtest-ready-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "backtest_ready" in content.lower()
    assert "execution_policy" in content
    assert "portfolio_policy" in content
    assert "risk_overlay" in content
    assert "engine_contract" in content
    assert "delivery_contract" in content


def test_holdout_validation_author_skill_exists() -> None:
    skill_path = Path(".agents/skills/qros-holdout-validation-author/SKILL.md")
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "holdout_validation" in content.lower()
    assert "window_contract" in content
    assert "reuse_contract" in content
    assert "drift_audit" in content
    assert "failure_governance" in content
    assert "delivery_contract" in content
