from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_backtest_implementation_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_backtest_implementation_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-backtest-implementation-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_backtest_spec.yaml",
        "schema_id": "qros-paper-backtest-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_backtest_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "backtest_spec_reference",
        "implementation_intent",
        "core_implementation_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]
    assert contract["required_backtest_spec_reference_fields"] == [
        "paper_slug",
        "path",
        "validation_status",
        "inherited_backtest_fields",
        "inherited_backtest_identity",
    ]


def test_paper_backtest_implementation_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
        "active_research_repo_boundary",
        "target_stage_program",
        "backtest_entrypoint",
        "input_artifacts",
        "frozen_config_binding",
        "data_access_plan",
        "output_artifacts",
        "execution_manifest",
        "validation_checks",
        "no_retune_controls",
        "reproducibility_controls",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_core_fields
    assert set(contract["field_library"]["core"]) == set(expected_core_fields)


def test_paper_backtest_implementation_spec_contract_declares_statuses_and_sources() -> None:
    contract = _load_contract()

    assert contract["allowed_requirement_statuses"] == [
        "required",
        "optional",
        "not_needed",
        "unknown",
    ]
    assert contract["allowed_requirement_sources"] == [
        "backtest_spec_inherited",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
        "repo_policy_required",
    ]
    assert contract["allowed_backtest_spec_validation_statuses"] == [
        "valid",
        "blocked",
        "unknown",
    ]


def test_paper_backtest_implementation_spec_contract_declares_optional_blocks_and_handoff() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["optional_blocks"]) == {
        "vectorbt_engine",
        "backtrader_engine",
        "custom_engine",
        "data_materialization",
        "performance_report",
    }
    assert contract["required_implementation_handoff_fields"] == [
        "implementation_inputs",
        "implementation_outputs",
        "validation_checks",
        "next_stage_recommendation",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "generate_active_repo_paperspec_chain_scaffold",
        "ask_researcher",
    ]


def test_paper_backtest_implementation_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "repo_boundary": ["active_research_repo_boundary", "target_stage_program"],
        "execution_inputs": [
            "backtest_entrypoint",
            "input_artifacts",
            "frozen_config_binding",
            "data_access_plan",
        ],
        "outputs_and_validation": [
            "output_artifacts",
            "execution_manifest",
            "validation_checks",
        ],
        "controls": ["no_retune_controls", "reproducibility_controls"],
    }
