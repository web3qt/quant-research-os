from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/guides/qros-paper-to-spec-usage.md"
README_PATH = ROOT / "docs/README.codex.md"
QROS_BIN = "./.qros/bin/"


def test_paper_to_spec_usage_guide_exists() -> None:
    assert GUIDE_PATH.exists(), f"missing guide: {GUIDE_PATH}"


def test_paper_to_spec_usage_guide_documents_first_paper_data_spec_version() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "paper_signal_spec.yaml",
        "paper_train_freeze_spec.yaml",
        "paper_test_evidence_spec.yaml",
        "paper_backtest_spec.yaml",
        "paper_backtest_implementation_spec.yaml",
        "paper_auto_implementation_handoff.yaml",
        "contracts/paper_to_spec/paper_data_spec_contract.yaml",
        "contracts/paper_to_spec/paper_signal_spec_contract.yaml",
        "contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml",
        "contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml",
        "contracts/paper_to_spec/paper_backtest_spec_contract.yaml",
        "contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml",
        "contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml",
        "contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml",
        "contracts/paper_to_spec/field_guides/paper_auto_implementation_handoff.fields.xml",
        "runtime/scripts/validate_paper_data_spec.py",
        "runtime/scripts/validate_paper_signal_spec.py",
        "runtime/scripts/validate_paper_train_freeze_spec.py",
        "runtime/scripts/validate_paper_test_evidence_spec.py",
        "runtime/scripts/validate_paper_backtest_spec.py",
        "runtime/scripts/validate_paper_backtest_implementation_spec.py",
        "runtime/scripts/validate_paper_auto_implementation_handoff.py",
        "XML field guide",
        "只读取当前阶段",
        "不是正式 artifact",
        "不是 validator",
        "YAML contract remains canonical",
        "正式 artifact 仍然是 `paper_*_spec.yaml`",
        "deterministic validator",
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
        "required_parameter_calibration",
        "portfolio_mapping",
        "diagnostics",
        "data_spec_inherited",
        "signal_identity",
        "prediction_and_inputs",
        "leakage_and_calibration",
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
        "calibration_state",
        "recalibration_policy",
        "artifact_identity",
        "signal_spec_inherited",
        "freeze_identity",
        "split_and_selection",
        "calibration_and_recalibration",
        "train_freeze_spec_reference",
        "core_test_evidence_requirements",
        "test_window",
        "frozen_artifact_binding",
        "signal_diagnostics",
        "performance_diagnostics",
        "rule_based_evidence",
        "parameter_calibration_evidence",
        "no_retune_attestation",
        "test_result_usage_policy",
        "provenance",
        "evidence_identity",
        "train_freeze_spec_inherited",
        "evidence_scope",
        "no_retune",
        "provenance_identity",
        "test_evidence_spec_reference",
        "core_backtest_requirements",
        "backtest_scope",
        "market_assumptions",
        "portfolio_construction",
        "position_sizing",
        "execution_assumptions",
        "fees_slippage_funding",
        "risk_controls",
        "required_metrics",
        "pass_fail_gate",
        "reproducibility",
        "implementation_handoff_plan",
        "test_evidence_spec_inherited",
        "scope_and_binding",
        "portfolio_and_execution",
        "accounting_and_risk",
        "evidence_and_reproducibility",
        "backtest_spec_reference",
        "core_implementation_requirements",
        "active_research_repo_boundary",
        "target_stage_program",
        "backtest_entrypoint",
        "input_artifacts",
        "frozen_config_binding",
        "data_access_plan",
        "output_artifacts",
        "execution_manifest",
        "no_retune_controls",
        "reproducibility_controls",
        "backtest_spec_inherited",
        "repo_policy_required",
        "repo_boundary",
        "execution_inputs",
        "outputs_and_validation",
        "controls",
        "post-spec implementation handoff",
        "implementation_decision",
        "data_readiness_brief",
        "researcher_data_response",
        "agent_acquisition_plan",
        "acquisition_provenance",
        "allowed_next_action",
        "generate_active_repo_paperspec_chain_scaffold",
        "program/data",
        "program/signal",
        "program/train_freeze",
        "program/test_evidence",
        "program/backtest",
        "implementation_consent",
        "data_readiness",
        "agent_acquisition",
        "active repo boundary",
        "agent acquisition plan",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不在缺少 post-spec implementation opt-in 时生成回测代码",
        "不在列出 data readiness brief 和询问研究员能否供数之前执行 agent data acquisition",
        "不在 agent acquisition plan 未获批准时下载",
        "不把 validator failure 包装成 review verdict",
        "不把 train/test 是否需要留到 backtest 阶段才判断",
        "不把参数选择、定尺状态、split policy 或 artifact identity 留到 backtest 阶段才定义",
        "不把 test evidence 用作 holdout 前调参入口",
        "不把 backtest 结果用作调参入口",
        "真实实现属于 active research repo",
        "不是 `qros-research-session` 的阶段入口",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        QROS_BIN + "qros-paper-to-spec",
        QROS_BIN + "qros-paper-to-spec" + "-baseline",
        "--spec" + "-file",
        "--auto" + "-implement",
        "source -> spec -> materialize -> stop",
        "默认停在 `" + "strategy_" + "spec.yaml`",
    ]

    for needle in forbidden_strings:
        assert needle not in content


def test_paper_to_spec_usage_guide_locks_post_spec_handoff_gates() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")
    section = _section(content, "Post-Spec Implementation Handoff 执行流程")

    assert "只有 requested PaperSpec chain 全部通过 deterministic validator 后" in section
    assert "任一 validation_status 不是 `valid` 时不得继续实现" in section
    assert "未回答或回答 declined 时，停止在 specs 之后" in section
    assert "先产出 `data_readiness_brief`" in section
    assert "询问 `researcher_data_response`：研究员能否提供 required datasets" in section
    assert "只有研究员明确 `cannot_provide` required datasets 时" in section
    assert "未获批准不得下载、物化或声称数据可用" in section
    assert "`allowed_next_action` 必须使用 `generate_active_repo_paperspec_chain_scaffold`" in section
    assert "data、signal、train_freeze、test_evidence、backtest 五段轻量实现程序" in section


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = content.find(marker)
    assert start != -1, f"missing section: {heading}"
    body_start = start + len(marker)
    next_section = content.find("\n## ", body_start)
    if next_section == -1:
        return content[body_start:]
    return content[body_start:next_section]


@pytest.mark.parametrize(
    (
        "heading",
        "xml_guide",
        "yaml_contract",
        "output_artifact",
        "validator",
    ),
    [
        (
            "Data 执行流程",
            "paper_data_spec.fields.xml",
            "paper_data_spec_contract.yaml",
            "paper_data_spec.yaml",
            "validate_paper_data_spec.py",
        ),
        (
            "Signal 执行流程",
            "paper_signal_spec.fields.xml",
            "paper_signal_spec_contract.yaml",
            "paper_signal_spec.yaml",
            "validate_paper_signal_spec.py",
        ),
        (
            "Train-Freeze 执行流程",
            "paper_train_freeze_spec.fields.xml",
            "paper_train_freeze_spec_contract.yaml",
            "paper_train_freeze_spec.yaml",
            "validate_paper_train_freeze_spec.py",
        ),
        (
            "Test-Evidence 执行流程",
            "paper_test_evidence_spec.fields.xml",
            "paper_test_evidence_spec_contract.yaml",
            "paper_test_evidence_spec.yaml",
            "validate_paper_test_evidence_spec.py",
        ),
        (
            "Backtest 执行流程",
            "paper_backtest_spec.fields.xml",
            "paper_backtest_spec_contract.yaml",
            "paper_backtest_spec.yaml",
            "validate_paper_backtest_spec.py",
        ),
        (
            "Backtest Implementation 执行流程",
            "paper_backtest_implementation_spec.fields.xml",
            "paper_backtest_implementation_spec_contract.yaml",
            "paper_backtest_implementation_spec.yaml",
            "validate_paper_backtest_implementation_spec.py",
        ),
    ],
)
def test_paper_to_spec_usage_guide_pairs_stage_specific_assets(
    heading: str,
    xml_guide: str,
    yaml_contract: str,
    output_artifact: str,
    validator: str,
) -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")
    section = _section(content, heading)

    assert f"contracts/paper_to_spec/field_guides/{xml_guide}" in section
    assert f"contracts/paper_to_spec/{yaml_contract}" in section
    assert f"outputs/paper_to_spec/<paper_slug>/{output_artifact}" in section
    assert f"runtime/scripts/{validator}" in section
    assert "只读取当前阶段" in section
    assert "active research repo" in section


def test_codex_readme_documents_paper_to_spec_reset() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "旧 `strategy_spec` materializer 已移除" in content
    assert "paper_data_spec.yaml" in content
    assert "paper_signal_spec.yaml" in content
    assert "paper_train_freeze_spec.yaml" in content
    assert "paper_test_evidence_spec.yaml" in content
    assert "paper_backtest_spec.yaml" in content
    assert "paper_backtest_implementation_spec.yaml" in content
    assert "contracts/paper_to_spec/paper_data_spec_contract.yaml" in content
    assert "contracts/paper_to_spec/paper_signal_spec_contract.yaml" in content
    assert "contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml" in content
    assert "contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml" in content
    assert "contracts/paper_to_spec/paper_backtest_spec_contract.yaml" in content
    assert "contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml" in content
    assert "runtime/scripts/validate_paper_data_spec.py" in content
    assert "runtime/scripts/validate_paper_signal_spec.py" in content
    assert "runtime/scripts/validate_paper_train_freeze_spec.py" in content
    assert "runtime/scripts/validate_paper_test_evidence_spec.py" in content
    assert "runtime/scripts/validate_paper_backtest_spec.py" in content
    assert "runtime/scripts/validate_paper_backtest_implementation_spec.py" in content
    assert "strict blocking" in content
    assert "train/test policy" in content
    assert "artifact identity" in content
    assert "evidence identity" in content
    assert "implementation handoff plan" in content
    assert "active research repo boundary" in content
    assert "下一版会采用 data-spec-first" not in content
    assert QROS_BIN + "qros-paper-to-spec" not in content
    assert QROS_BIN + "qros-paper-to-spec" + "-baseline" not in content
    assert "--auto" + "-implement" not in content
