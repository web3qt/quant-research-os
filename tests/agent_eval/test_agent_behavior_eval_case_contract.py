from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/agent_eval/qros_agent_behavior_eval_cases.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_agent_behavior_eval_case_contract_exists_and_declares_mvp_cases() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["schema_id"] == "qros-agent-behavior-eval-cases-v1"
    assert contract["schema_version"] == "v1"
    case_ids = {case["id"] for case in contract["cases"]}
    assert case_ids == {
        "naive_raw_idea_triggers_research_session",
        "explicit_idea_intake_author_skill_first",
        "partial_intake_does_not_go_to_mandate",
        "no_confirmation_no_mandate_formal_artifacts",
        "raw_idea_scaffold_passes_artifact_shape_validator",
        "explicit_csf_data_ready_author_skill_first",
        "csf_data_ready_rejects_non_csf_mandate",
        "csf_data_ready_rejects_unreviewed_mandate",
        "csf_data_ready_rejects_unconfirmed_freeze_groups",
        "csf_data_ready_rejects_placeholder_parquet_completion",
        "csf_data_ready_runs_validator_before_review",
        "explicit_csf_signal_ready_author_skill_first",
        "naive_csf_signal_ready_prompt_triggers_author_skill",
        "csf_signal_ready_rejects_missing_csf_data_ready_review_closure",
        "csf_signal_ready_rejects_non_csf_mandate_route",
        "csf_signal_ready_rejects_unconfirmed_freeze_groups",
        "csf_signal_ready_rejects_placeholder_factor_panel_completion",
        "csf_signal_ready_runs_artifact_validator_before_review",
        "csf_signal_ready_runs_semantic_validator_before_review",
        "csf_signal_ready_rejects_route_inheritance_drift",
        "csf_signal_ready_rejects_raw_field_without_input_binding",
        "explicit_csf_train_freeze_author_skill_first",
        "naive_csf_train_freeze_prompt_triggers_author_skill",
        "csf_train_freeze_rejects_missing_csf_signal_ready_review_closure",
        "csf_train_freeze_rejects_unconfirmed_freeze_groups",
        "csf_train_freeze_rejects_placeholder_variant_ledger_completion",
        "csf_train_freeze_runs_artifact_validator_before_review",
        "csf_train_freeze_runs_semantic_validator_before_review",
        "csf_train_freeze_rejects_signal_axis_drift",
        "explicit_csf_test_evidence_author_skill_first",
        "naive_csf_test_evidence_prompt_triggers_author_skill",
        "csf_test_evidence_rejects_missing_csf_train_freeze_review_closure",
        "csf_test_evidence_rejects_unconfirmed_freeze_groups",
        "csf_test_evidence_rejects_placeholder_rank_ic_completion",
        "csf_test_evidence_runs_artifact_validator_before_review",
        "csf_test_evidence_runs_semantic_validator_before_review",
        "csf_test_evidence_rejects_variant_drift",
        "explicit_csf_backtest_ready_author_skill_first",
        "naive_csf_backtest_ready_prompt_triggers_author_skill",
        "csf_backtest_ready_rejects_missing_csf_test_evidence_review_closure",
        "csf_backtest_ready_rejects_unconfirmed_freeze_groups",
        "csf_backtest_ready_rejects_placeholder_weight_panel_completion",
        "csf_backtest_ready_runs_artifact_validator_before_review",
        "csf_backtest_ready_runs_semantic_validator_before_review",
        "csf_backtest_ready_rejects_variant_drift",
    }


def test_agent_behavior_eval_cases_have_stable_behavior_assertions() -> None:
    contract = _load_contract()

    for case in contract["cases"]:
        assert case["prompt"].strip(), case["id"]
        assert case["expected_skill"].startswith("qros-"), case["id"]
        assert case["premature_tool_policy"] == "forbid_before_expected_skill", case["id"]
        assert "lineage_id" in case, case["id"]
        assert isinstance(case.get("expected_artifacts", {}).get("present", []), list), case["id"]
        assert isinstance(case.get("expected_artifacts", {}).get("absent", []), list), case["id"]


def test_csf_data_ready_eval_cases_lock_gate_specific_event_assertions() -> None:
    contract = _load_contract()
    cases = {case["id"]: case for case in contract["cases"]}

    success_case = cases["csf_data_ready_runs_validator_before_review"]
    assert success_case["expected_skill"] == "qros-csf-data-ready-author"
    assert success_case["expected_events"]["ordered_substrings"] == [
        "qros-validate-stage --stage csf_data_ready",
        "qros-review-preflight",
        "qros-review-cycle prepare",
    ]
    assert success_case["validators"] == [{"stage": "csf_data_ready"}]

    for case_id in (
        "csf_data_ready_rejects_non_csf_mandate",
        "csf_data_ready_rejects_unreviewed_mandate",
        "csf_data_ready_rejects_unconfirmed_freeze_groups",
        "csf_data_ready_rejects_placeholder_parquet_completion",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-data-ready-author"
        assert "qros-review-cycle prepare" in case["expected_events"]["forbidden_substrings"]


def test_csf_signal_ready_eval_cases_lock_gate_specific_event_assertions() -> None:
    contract = _load_contract()
    cases = {case["id"]: case for case in contract["cases"]}

    for case_id in (
        "csf_signal_ready_runs_artifact_validator_before_review",
        "csf_signal_ready_runs_semantic_validator_before_review",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-signal-ready-author"
        assert case["expected_events"]["ordered_substrings"] == [
            "qros-validate-stage --stage csf_signal_ready",
            "csf_signal_ready semantic validator",
            "qros-review-preflight",
            "qros-review-cycle prepare",
        ]
        assert case["validators"] == [{"stage": "csf_signal_ready"}]

    for case_id in (
        "csf_signal_ready_rejects_missing_csf_data_ready_review_closure",
        "csf_signal_ready_rejects_non_csf_mandate_route",
        "csf_signal_ready_rejects_unconfirmed_freeze_groups",
        "csf_signal_ready_rejects_placeholder_factor_panel_completion",
        "csf_signal_ready_rejects_route_inheritance_drift",
        "csf_signal_ready_rejects_raw_field_without_input_binding",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-signal-ready-author"
        assert "qros-review-cycle prepare" in case["expected_events"]["forbidden_substrings"]


def test_csf_train_freeze_eval_cases_lock_gate_specific_event_assertions() -> None:
    contract = _load_contract()
    cases = {case["id"]: case for case in contract["cases"]}

    for case_id in (
        "csf_train_freeze_runs_artifact_validator_before_review",
        "csf_train_freeze_runs_semantic_validator_before_review",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-train-freeze-author"
        assert case["expected_events"]["ordered_substrings"] == [
            "qros-validate-stage --stage csf_train_freeze",
            "csf_train_freeze semantic validator",
            "qros-review-preflight",
            "qros-review-cycle prepare",
        ]
        assert case["validators"] == [{"stage": "csf_train_freeze"}]

    for case_id in (
        "csf_train_freeze_rejects_missing_csf_signal_ready_review_closure",
        "csf_train_freeze_rejects_unconfirmed_freeze_groups",
        "csf_train_freeze_rejects_placeholder_variant_ledger_completion",
        "csf_train_freeze_rejects_signal_axis_drift",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-train-freeze-author"
        assert "qros-review-cycle prepare" in case["expected_events"]["forbidden_substrings"]


def test_csf_test_evidence_eval_cases_lock_gate_specific_event_assertions() -> None:
    contract = _load_contract()
    cases = {case["id"]: case for case in contract["cases"]}

    for case_id in (
        "csf_test_evidence_runs_artifact_validator_before_review",
        "csf_test_evidence_runs_semantic_validator_before_review",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-test-evidence-author"
        assert case["expected_events"]["ordered_substrings"] == [
            "qros-validate-stage --stage csf_test_evidence",
            "csf_test_evidence semantic validator",
            "qros-review-preflight",
            "qros-review-cycle prepare",
        ]
        assert case["validators"] == [{"stage": "csf_test_evidence"}]

    for case_id in (
        "csf_test_evidence_rejects_missing_csf_train_freeze_review_closure",
        "csf_test_evidence_rejects_unconfirmed_freeze_groups",
        "csf_test_evidence_rejects_placeholder_rank_ic_completion",
        "csf_test_evidence_rejects_variant_drift",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-test-evidence-author"
        assert "qros-review-cycle prepare" in case["expected_events"]["forbidden_substrings"]


def test_csf_backtest_ready_eval_cases_lock_gate_specific_event_assertions() -> None:
    contract = _load_contract()
    cases = {case["id"]: case for case in contract["cases"]}

    for case_id in (
        "csf_backtest_ready_runs_artifact_validator_before_review",
        "csf_backtest_ready_runs_semantic_validator_before_review",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-backtest-ready-author"
        assert case["expected_events"]["ordered_substrings"] == [
            "qros-validate-stage --stage csf_backtest_ready",
            "csf_backtest_ready semantic validator",
            "qros-review-preflight",
            "qros-review-cycle prepare",
        ]
        assert case["validators"] == [{"stage": "csf_backtest_ready"}]

    for case_id in (
        "csf_backtest_ready_rejects_missing_csf_test_evidence_review_closure",
        "csf_backtest_ready_rejects_unconfirmed_freeze_groups",
        "csf_backtest_ready_rejects_placeholder_weight_panel_completion",
        "csf_backtest_ready_rejects_variant_drift",
    ):
        case = cases[case_id]
        assert case["expected_skill"] == "qros-csf-backtest-ready-author"
        assert "qros-review-cycle prepare" in case["expected_events"]["forbidden_substrings"]


def test_agent_behavior_eval_contract_keeps_live_agent_eval_out_of_default_ci() -> None:
    contract = _load_contract()

    assert contract["execution_mode"] == "manual_or_nightly"
    assert contract["default_pytest_behavior"] == "fake_transcripts_only"
    assert contract["requires_agent_command_template"] is True
