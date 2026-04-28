from pathlib import Path

from tests.helpers.tss_stage_parity import assert_tss_generated_artifacts_match_contract


def test_generated_tss_backtest_ready_artifacts_match_contract(tmp_path: Path) -> None:
    assert_tss_generated_artifacts_match_contract("tss_backtest_ready", tmp_path)
