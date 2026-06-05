from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/core/qros-paper-to-spec/SKILL.md"
QROS_BIN = "./.qros/bin/"

STAGE_GUIDES = [
    (
        "Data Execution Protocol",
        "paper_data_spec.fields.xml",
        "paper_data_spec_contract.yaml",
    ),
    (
        "Signal Execution Protocol",
        "paper_signal_spec.fields.xml",
        "paper_signal_spec_contract.yaml",
    ),
    (
        "Train-Freeze Execution Protocol",
        "paper_train_freeze_spec.fields.xml",
        "paper_train_freeze_spec_contract.yaml",
    ),
    (
        "Test-Evidence Execution Protocol",
        "paper_test_evidence_spec.fields.xml",
        "paper_test_evidence_spec_contract.yaml",
    ),
    (
        "Backtest Execution Protocol",
        "paper_backtest_spec.fields.xml",
        "paper_backtest_spec_contract.yaml",
    ),
    (
        "Backtest Implementation Execution Protocol",
        "paper_backtest_implementation_spec.fields.xml",
        "paper_backtest_implementation_spec_contract.yaml",
    ),
]


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}"
    start = content.index(marker)
    next_heading = content.find("\n## ", start + len(marker))
    if next_heading == -1:
        return content[start:]
    return content[start:next_heading]


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
        "XML field guide",
        "只读取当前阶段",
        "stage-specific XML field guide",
        "XML field guides are semantic aids only",
        "不是正式 artifact",
        "不是 validator",
        "YAML contract remains canonical",
        "正式 artifact 仍然是 `paper_*_spec.yaml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_data_spec.fields.xml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_signal_spec.fields.xml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_train_freeze_spec.fields.xml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_test_evidence_spec.fields.xml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_backtest_spec.fields.xml`",
        "只读取当前阶段的 `contracts/paper_to_spec/field_guides/paper_backtest_implementation_spec.fields.xml`",
        "runtime/scripts/validate_paper_data_spec.py",
        "runtime/scripts/validate_paper_signal_spec.py",
        "runtime/scripts/validate_paper_train_freeze_spec.py",
        "runtime/scripts/validate_paper_test_evidence_spec.py",
        "runtime/scripts/validate_paper_backtest_spec.py",
        "runtime/scripts/validate_paper_backtest_implementation_spec.py",
        "runtime/scripts/validate_paper_auto_implementation_handoff.py",
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


def test_paper_to_spec_skill_locks_post_spec_handoff_gates() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")
    section = _section(content, "Post-Spec Implementation Handoff Protocol")

    assert "只有 requested PaperSpec chain 全部通过对应 deterministic validator 后" in section
    assert "任一 validation_status 不是 `valid`，不得询问或执行实现" in section
    assert "未回答或回答 declined 时，必须停止在 specs 之后" in section
    assert "先列 required data、optional data、market scope、symbol universe" in section
    assert "询问研究员能否提供 required datasets" in section
    assert "只有研究员明确 `cannot_provide` required datasets 时" in section
    assert "未获批准不得下载、物化或声称数据可用" in section


@pytest.mark.parametrize(("heading", "guide", "contract"), STAGE_GUIDES)
def test_paper_to_spec_skill_stage_protocol_uses_only_matching_xml_guide(
    heading: str,
    guide: str,
    contract: str,
) -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")
    section = _section(content, heading)
    expected_guide_path = f"contracts/paper_to_spec/field_guides/{guide}"
    expected_contract_path = f"contracts/paper_to_spec/{contract}"

    assert "只读取当前阶段" in section
    assert expected_guide_path in section
    assert expected_contract_path in section

    for _, other_guide, _ in STAGE_GUIDES:
        if other_guide == guide:
            continue
        assert f"contracts/paper_to_spec/field_guides/{other_guide}" not in section
