from pathlib import Path

import yaml


CONTRACT_PATH = Path(
    "contracts/paper_to_spec/paper_auto_implementation_handoff_contract.yaml"
)
GUIDE_PATH = Path(
    "contracts/paper_to_spec/field_guides/"
    "paper_auto_implementation_handoff.fields.xml"
)


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_auto_implementation_handoff_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-auto-implementation-handoff-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["depends_on"] == {
        "artifact": "paper_backtest_implementation_spec.yaml",
        "schema_id": "qros-paper-backtest-implementation-spec-contract-v1",
        "validator": "runtime/scripts/validate_paper_backtest_implementation_spec.py",
    }
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "paper_spec_chain",
        "implementation_decision",
        "data_readiness_brief",
        "researcher_data_response",
        "agent_acquisition_plan",
        "acquisition_provenance",
        "active_repo_boundary",
        "allowed_next_action",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_auto_implementation_handoff_contract_locks_enums() -> None:
    contract = _load_contract()

    assert contract["allowed_spec_validation_statuses"] == ["valid", "blocked", "unknown"]
    assert contract["allowed_implementation_decisions"] == ["pending", "accepted", "declined"]
    assert contract["allowed_researcher_data_statuses"] == [
        "pending",
        "provided",
        "cannot_provide",
    ]
    assert contract["allowed_acquisition_plan_statuses"] == [
        "not_needed",
        "pending_approval",
        "approved",
        "rejected",
    ]
    assert contract["allowed_acquisition_run_statuses"] == [
        "not_run",
        "succeeded",
        "failed",
        "partial",
    ]
    assert contract["allowed_next_actions"] == [
        "stop_after_specs",
        "ask_researcher",
        "validate_researcher_data",
        "run_agent_data_acquisition",
        "generate_active_repo_paperspec_chain_scaffold",
    ]
    assert contract["allowed_next_stage_recommendations"] == [
        "stop_after_specs",
        "ask_researcher",
        "validate_researcher_data",
        "run_agent_data_acquisition",
        "generate_active_repo_paperspec_chain_scaffold",
    ]


def test_paper_auto_implementation_handoff_contract_locks_data_item_shape() -> None:
    contract = _load_contract()

    assert contract["required_data_item_fields"] == [
        "name",
        "requirement",
        "required",
        "market_scope",
        "symbol_universe",
        "fields",
        "cadence",
        "time_range",
        "source_constraints",
        "expected_format",
        "provenance_requirements",
        "missing_data_policy",
        "blocking",
    ]
    assert contract["required_acquisition_source_fields"] == [
        "dataset",
        "source",
        "symbols",
        "time_range",
        "fields",
        "command",
        "storage_target",
        "expected_artifacts",
        "approval_required",
    ]
    assert contract["required_acquisition_provenance_fields"] == [
        "run_status",
        "source_records",
        "command",
        "timestamp",
        "snapshot_identity",
        "coverage",
        "validation_result",
        "failure_reason",
    ]
    assert contract["required_acquisition_source_record_fields"] == [
        "dataset",
        "source",
        "symbols",
        "time_range",
        "fields",
        "expected_artifacts",
        "coverage",
        "validation_result",
    ]


def test_paper_auto_implementation_handoff_contract_declares_blocking_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "implementation_consent": ["implementation_decision"],
        "data_readiness": ["data_readiness_brief", "researcher_data_response"],
        "agent_acquisition": ["agent_acquisition_plan", "acquisition_provenance"],
        "repo_boundary": ["active_repo_boundary"],
        "next_action": ["allowed_next_action"],
    }


def test_paper_auto_implementation_handoff_contract_locks_prompt_and_acquisition_rules() -> None:
    contract = _load_contract()
    rules = contract["handoff_rules"]

    assert rules["spec_chain_valid_before_prompt"] == {
        "field": "paper_spec_chain",
        "required_validation_status": "valid",
        "prompt_allowed_only_when_all_specs_valid": True,
        "blocked_implementation_decisions_before_all_valid": ["accepted"],
        "blocked_next_actions_before_all_valid": [
            "validate_researcher_data",
            "run_agent_data_acquisition",
            "generate_active_repo_paperspec_chain_scaffold",
        ],
    }
    assert rules["researcher_data_preferred"] == {
        "ask_field": "researcher_data_response.status",
        "agent_acquisition_allowed_only_when": "cannot_provide",
    }
    assert rules["data_readiness_before_implementation"] == {
        "required_before_next_actions": [
            "validate_researcher_data",
            "run_agent_data_acquisition",
            "generate_active_repo_paperspec_chain_scaffold",
        ],
        "required_field": "data_readiness_brief",
        "blocking_gaps_field": "data_readiness_brief.blocking_gaps",
        "blocked_next_actions_when_blocking_gaps_present": [
            "validate_researcher_data",
            "run_agent_data_acquisition",
            "generate_active_repo_paperspec_chain_scaffold",
        ],
    }
    assert rules["blocking_ambiguities_stop_implementation"] == {
        "field": "ambiguities",
        "blocking_field": "blocking",
        "blocked_value": True,
        "blocked_next_actions": [
            "validate_researcher_data",
            "run_agent_data_acquisition",
            "generate_active_repo_paperspec_chain_scaffold",
        ],
    }
    assert rules["agent_acquisition_requires_approval"] == {
        "plan_status_field": "agent_acquisition_plan.status",
        "approved_value": "approved",
        "executable_next_action": "run_agent_data_acquisition",
    }


def test_paper_auto_implementation_handoff_xml_guide_references_contract() -> None:
    assert GUIDE_PATH.exists(), f"missing XML field guide: {GUIDE_PATH}"
    guide_text = GUIDE_PATH.read_text(encoding="utf-8")

    assert 'artifact="paper_auto_implementation_handoff.yaml"' in guide_text
    assert 'contract="paper_auto_implementation_handoff_contract.yaml"' in guide_text


def test_paper_auto_implementation_handoff_xml_guide_covers_required_fields() -> None:
    contract = _load_contract()
    guide_text = GUIDE_PATH.read_text(encoding="utf-8")

    for field_name in contract["required_top_level_fields"]:
        assert f'<field path="{field_name}">' in guide_text
        field_start = guide_text.index(f'<field path="{field_name}">')
        field_end = guide_text.index("</field>", field_start)
        field_fragment = guide_text[field_start:field_end]
        assert "<zhName>" in field_fragment
        assert any("\u4e00" <= char <= "\u9fff" for char in field_fragment)
