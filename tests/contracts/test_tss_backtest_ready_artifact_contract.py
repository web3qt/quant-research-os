from tests.helpers.tss_stage_parity import assert_tss_artifact_contract_is_stage_specific


def test_tss_backtest_ready_artifact_contract_is_stage_specific() -> None:
    assert_tss_artifact_contract_is_stage_specific("tss_backtest_ready")
