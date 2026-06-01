from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/core/qros-paper-to-spec/SKILL.md"
QROS_BIN = "./.qros/bin/"


def test_paper_to_spec_skill_exists() -> None:
    assert SKILL_PATH.exists(), f"missing skill: {SKILL_PATH}"


def test_paper_to_spec_skill_documents_first_paper_data_spec_version() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "paper_signal_spec.yaml",
        "paper_train_freeze_spec.yaml",
        "paper_test_evidence_spec.yaml",
        "contracts/paper_to_spec/paper_data_spec_contract.yaml",
        "contracts/paper_to_spec/paper_signal_spec_contract.yaml",
        "contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml",
        "contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml",
        "runtime/scripts/validate_paper_data_spec.py",
        "runtime/scripts/validate_paper_signal_spec.py",
        "runtime/scripts/validate_paper_train_freeze_spec.py",
        "deterministic validator",
        "Execution protocol",
        "reading_coverage",
        "target_market",
        "core_data_requirements",
        "triggered_optional_blocks",
        "strict blocking",
        "strict blocking field",
        "Requirement entry shape",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
        "exchange_profile_default",
        "universe",
        "price_bars",
        "funding",
        "fees_and_slippage",
        "label_or_return_target",
        "timestamp_alignment",
        "data_availability",
        "blocking_question_groups",
        "market_scope",
        "bar_and_price",
        "return_accounting",
        "source_coverage",
        "data_spec_reference",
        "core_signal_requirements",
        "signal_family",
        "prediction_target",
        "feature_inputs",
        "signal_definition",
        "signal_timing",
        "lookahead_controls",
        "train_test_policy",
        "not_required_rule_based",
        "required_parameter_fit",
        "required_ml_model",
        "portfolio_mapping",
        "diagnostics",
        "data_spec_inherited",
        "signal_identity",
        "prediction_and_inputs",
        "leakage_and_training",
        "portfolio_and_diagnostics",
        "signal_spec_reference",
        "inherited train/test policy consistency",
        "core_train_freeze_requirements",
        "train_test_mode",
        "frozen_signal_definition",
        "parameter_freeze",
        "train_window",
        "test_window",
        "split_policy",
        "selection_policy",
        "model_training",
        "refit_policy",
        "artifact_identity",
        "signal_spec_inherited",
        "freeze_identity",
        "split_and_selection",
        "fit_and_refit",
        "train_freeze_spec_reference",
        "core_test_evidence_requirements",
        "test_window",
        "frozen_artifact_binding",
        "signal_diagnostics",
        "performance_diagnostics",
        "rule_based_evidence",
        "parameter_fit_evidence",
        "ml_model_evidence",
        "no_retune_attestation",
        "test_result_usage_policy",
        "provenance",
        "evidence_identity",
        "train_freeze_spec_inherited",
        "evidence_scope",
        "no_retune",
        "provenance_identity",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不直接生成回测代码",
        "不把 validator failure 包装成 review verdict",
        "不把 train/test 是否需要留到 backtest 阶段才判断",
        "不把参数选择、模型训练、split policy 或 artifact identity 留到 backtest 阶段才定义",
        "不把 test evidence 用作 holdout 前调参入口",
        "独立于 `qros-research-session`",
        "heavy governance flow",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        QROS_BIN + "qros-paper-to-spec",
        QROS_BIN + "qros-paper-to-spec" + "-baseline",
        "--spec" + "-file",
        "--auto" + "-implement",
        "auto" + "_implement",
        "source -> spec -> materialize -> stop",
        "默认只产出 `" + "strategy_" + "spec.yaml`",
        "report where the baseline files were written",
    ]

    for needle in forbidden_strings:
        assert needle not in content

    assert "--paper-url" not in content
    assert "--paper-slug" not in content
    assert "source_manifest.json" not in content
    assert "source_inventory.md" not in content
    assert "ambiguities.md" not in content
    assert "implementation_notes.md" not in content
