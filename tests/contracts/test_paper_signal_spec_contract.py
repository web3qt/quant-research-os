from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_signal_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_signal_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-signal-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_data_spec.yaml",
        "schema_id": "qros-paper-data-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_data_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "data_spec_reference",
        "signal_research_intent",
        "core_signal_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_signal_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
        "signal_family",
        "prediction_target",
        "feature_inputs",
        "signal_definition",
        "signal_timing",
        "lookahead_controls",
        "train_test_policy",
        "portfolio_mapping",
        "diagnostics",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_core_fields


def test_paper_signal_spec_contract_declares_signal_and_train_test_enums() -> None:
    contract = _load_contract()

    assert contract["allowed_signal_families"] == [
        "cross_sectional_factor",
        "time_series_signal",
        "hybrid",
        "event_driven",
        "unknown",
    ]
    assert contract["allowed_train_test_modes"] == [
        "not_required_rule_based",
        "required_parameter_fit",
        "required_ml_model",
        "unknown",
    ]
    assert contract["allowed_requirement_sources"] == [
        "paper_stated",
        "data_spec_inherited",
        "agent_inferred",
        "researcher_required",
    ]


def test_paper_signal_spec_contract_declares_optional_blocks_and_handoff() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["core"]) == set(contract["core_required_fields"])
    assert set(contract["field_library"]["optional_blocks"]) == {
        "cross_sectional_ranking",
        "time_series_thresholds",
        "parameter_search",
        "machine_learning_model",
        "regime_filter",
        "risk_filter",
    }
    assert contract["required_implementation_handoff_fields"] == [
        "signal_inputs",
        "signal_outputs",
        "validation_checks",
        "next_stage_recommendation",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "paper_train_freeze_spec",
        "paper_test_evidence_spec",
        "ask_researcher",
    ]


def test_paper_signal_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "signal_identity": ["signal_family", "signal_definition"],
        "prediction_and_inputs": ["prediction_target", "feature_inputs", "signal_timing"],
        "leakage_and_training": ["lookahead_controls", "train_test_policy"],
        "portfolio_and_diagnostics": ["portfolio_mapping", "diagnostics"],
    }
