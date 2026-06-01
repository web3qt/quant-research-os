from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_train_freeze_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-train-freeze-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_signal_spec.yaml",
        "schema_id": "qros-paper-signal-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_signal_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "signal_spec_reference",
        "train_freeze_intent",
        "core_train_freeze_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_train_freeze_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
        "train_test_mode",
        "frozen_signal_definition",
        "parameter_freeze",
        "train_window",
        "test_window",
        "split_policy",
        "selection_policy",
        "model_training",
        "refit_policy",
        "leakage_controls",
        "artifact_identity",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_core_fields


def test_paper_train_freeze_spec_contract_declares_train_test_enums_and_sources() -> None:
    contract = _load_contract()

    assert contract["allowed_train_test_modes"] == [
        "not_required_rule_based",
        "required_parameter_fit",
        "required_ml_model",
        "unknown",
    ]
    assert contract["allowed_requirement_sources"] == [
        "signal_spec_inherited",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
    ]
    assert contract["allowed_signal_spec_validation_statuses"] == [
        "valid",
        "blocked",
        "unknown",
    ]


def test_paper_train_freeze_spec_contract_declares_optional_blocks_and_handoff() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["core"]) == set(contract["core_required_fields"])
    assert set(contract["field_library"]["optional_blocks"]) == {
        "rule_based_freeze",
        "parameter_search_freeze",
        "ml_training_freeze",
        "walk_forward_freeze",
        "regime_specific_freeze",
    }
    assert contract["required_implementation_handoff_fields"] == [
        "frozen_inputs",
        "frozen_outputs",
        "validation_checks",
        "next_stage_recommendation",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "paper_test_evidence_spec",
        "ask_researcher",
    ]


def test_paper_train_freeze_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "freeze_identity": [
            "train_test_mode",
            "frozen_signal_definition",
            "artifact_identity",
        ],
        "split_and_selection": [
            "train_window",
            "test_window",
            "split_policy",
            "selection_policy",
        ],
        "fit_and_refit": [
            "parameter_freeze",
            "model_training",
            "refit_policy",
        ],
        "leakage": ["leakage_controls"],
    }
