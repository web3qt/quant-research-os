from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_test_evidence_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-test-evidence-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_train_freeze_spec.yaml",
        "schema_id": "qros-paper-train-freeze-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_train_freeze_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "train_freeze_spec_reference",
        "test_evidence_intent",
        "core_test_evidence_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_test_evidence_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
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
    ]
    expected_strict_fields = [
        "test_window",
        "frozen_artifact_binding",
        "signal_diagnostics",
        "performance_diagnostics",
        "no_retune_attestation",
        "test_result_usage_policy",
        "provenance",
        "evidence_identity",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_strict_fields


def test_paper_test_evidence_spec_contract_declares_statuses_and_sources() -> None:
    contract = _load_contract()

    assert contract["allowed_requirement_sources"] == [
        "train_freeze_spec_inherited",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
    ]
    assert contract["allowed_train_freeze_spec_validation_statuses"] == [
        "valid",
        "blocked",
        "unknown",
    ]


def test_paper_test_evidence_spec_contract_declares_optional_blocks_and_handoff() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["core"]) == set(contract["core_required_fields"])
    assert set(contract["field_library"]["optional_blocks"]) == {
        "rule_based_test_evidence",
        "parameter_fit_test_evidence",
        "ml_model_test_evidence",
        "cost_sensitivity_evidence",
        "robustness_evidence",
        "failure_case_evidence",
    }
    assert contract["required_implementation_handoff_fields"] == [
        "evidence_inputs",
        "evidence_outputs",
        "validation_checks",
        "next_stage_recommendation",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "paper_backtest_ready_spec",
        "ask_researcher",
    ]


def test_paper_test_evidence_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "evidence_scope": ["test_window", "frozen_artifact_binding"],
        "diagnostics": ["signal_diagnostics", "performance_diagnostics"],
        "no_retune": ["no_retune_attestation", "test_result_usage_policy"],
        "provenance_identity": ["provenance", "evidence_identity"],
    }
