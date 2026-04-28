from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


PARITY_FILES = [
    "tests/contracts/test_tss_data_ready_artifact_contract.py",
    "tests/contracts/test_tss_signal_ready_artifact_contract.py",
    "tests/contracts/test_tss_train_freeze_artifact_contract.py",
    "tests/contracts/test_tss_test_evidence_artifact_contract.py",
    "tests/contracts/test_tss_backtest_ready_artifact_contract.py",
    "tests/contracts/test_tss_holdout_validation_artifact_contract.py",
    "tests/session/test_tss_data_ready_artifact_shape.py",
    "tests/session/test_tss_signal_ready_artifact_shape.py",
    "tests/session/test_tss_train_freeze_artifact_shape.py",
    "tests/session/test_tss_test_evidence_artifact_shape.py",
    "tests/session/test_tss_backtest_ready_artifact_shape.py",
    "tests/session/test_tss_holdout_validation_artifact_shape.py",
    "tests/runtime/test_tss_data_ready_semantic_validation.py",
    "tests/runtime/test_tss_signal_ready_semantic_validation.py",
    "tests/runtime/test_tss_train_freeze_semantic_validation.py",
    "tests/runtime/test_tss_test_evidence_semantic_validation.py",
    "tests/runtime/test_tss_backtest_ready_semantic_validation.py",
    "tests/runtime/test_tss_holdout_validation_semantic_validation.py",
    "tests/review/test_review_preflight_tss_data_ready_contract.py",
    "tests/review/test_review_preflight_tss_signal_ready_contract.py",
    "tests/review/test_review_preflight_tss_train_freeze_contract.py",
    "tests/review/test_review_preflight_tss_test_evidence_contract.py",
    "tests/review/test_review_preflight_tss_backtest_ready_contract.py",
    "tests/review/test_review_preflight_tss_holdout_validation_contract.py",
    "tests/skills/test_tss_data_ready_contract_first_guidance.py",
    "tests/skills/test_tss_signal_ready_contract_first_guidance.py",
    "tests/skills/test_tss_train_freeze_contract_first_guidance.py",
    "tests/skills/test_tss_test_evidence_contract_first_guidance.py",
    "tests/skills/test_tss_backtest_ready_contract_first_guidance.py",
    "tests/skills/test_tss_holdout_validation_contract_first_guidance.py",
    "tests/docs/test_tss_data_ready_contract_first_docs.py",
    "tests/docs/test_tss_signal_ready_contract_first_docs.py",
    "tests/docs/test_tss_train_freeze_contract_first_docs.py",
    "tests/docs/test_tss_test_evidence_contract_first_docs.py",
    "tests/docs/test_tss_backtest_ready_contract_first_docs.py",
    "tests/docs/test_tss_holdout_validation_contract_first_docs.py",
    "tests/pipeline/test_tss_pipeline.py",
    "tests/e2e/test_tss_agent_session.py",
    "tests/agent_eval/test_tss_data_ready_agent_behavior_cases.py",
    "tests/agent_eval/test_tss_signal_ready_agent_behavior_cases.py",
    "tests/agent_eval/test_tss_train_freeze_agent_behavior_cases.py",
    "tests/agent_eval/test_tss_test_evidence_agent_behavior_cases.py",
    "tests/agent_eval/test_tss_backtest_ready_agent_behavior_cases.py",
    "tests/agent_eval/test_tss_holdout_validation_agent_behavior_cases.py",
]


def test_tss_has_route_specific_test_files_matching_csf_coverage_families() -> None:
    missing = [path for path in PARITY_FILES if not (ROOT / path).exists()]

    assert missing == []
