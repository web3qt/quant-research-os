from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_backtest_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_backtest_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-backtest-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_test_evidence_spec.yaml",
        "schema_id": "qros-paper-test-evidence-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_test_evidence_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "test_evidence_spec_reference",
        "backtest_intent",
        "core_backtest_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]
    assert contract["required_test_evidence_spec_reference_fields"] == [
        "paper_slug",
        "path",
        "validation_status",
        "inherited_evidence_fields",
        "inherited_evidence_identity",
    ]


def test_paper_backtest_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
        "backtest_scope",
        "frozen_artifact_binding",
        "market_assumptions",
        "portfolio_construction",
        "position_sizing",
        "execution_assumptions",
        "fees_slippage_funding",
        "risk_controls",
        "required_metrics",
        "pass_fail_gate",
        "reproducibility",
        "provenance",
        "implementation_handoff_plan",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_core_fields
    assert set(contract["field_library"]["core"]) == set(expected_core_fields)


def test_paper_backtest_spec_contract_declares_statuses_and_sources() -> None:
    contract = _load_contract()

    assert contract["allowed_requirement_statuses"] == [
        "required",
        "optional",
        "not_needed",
        "unknown",
    ]
    assert contract["allowed_requirement_sources"] == [
        "test_evidence_spec_inherited",
        "train_freeze_spec_inherited",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
    ]
    assert contract["allowed_test_evidence_spec_validation_statuses"] == [
        "valid",
        "blocked",
        "unknown",
    ]


def test_paper_backtest_spec_contract_declares_optional_blocks_and_handoff() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["optional_blocks"]) == {
        "long_short_portfolio",
        "long_only_or_flat_portfolio",
        "leverage_and_margin",
        "capacity_and_turnover",
        "funding_accounting",
        "cost_sensitivity",
    }
    assert contract["required_implementation_handoff_fields"] == [
        "backtest_inputs",
        "backtest_outputs",
        "validation_checks",
        "next_stage_recommendation",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "implement_backtest",
        "ask_researcher",
    ]


def test_paper_backtest_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "scope_and_binding": ["backtest_scope", "frozen_artifact_binding"],
        "portfolio_and_execution": [
            "portfolio_construction",
            "position_sizing",
            "execution_assumptions",
        ],
        "accounting_and_risk": [
            "market_assumptions",
            "fees_slippage_funding",
            "risk_controls",
        ],
        "evidence_and_reproducibility": [
            "required_metrics",
            "pass_fail_gate",
            "reproducibility",
            "provenance",
            "implementation_handoff_plan",
        ],
    }
