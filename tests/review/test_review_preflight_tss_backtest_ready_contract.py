from pathlib import Path

from tests.helpers.tss_stage_parity import assert_tss_review_preflight_is_contract_wired


def test_review_preflight_tss_backtest_ready_is_contract_wired(tmp_path: Path) -> None:
    assert_tss_review_preflight_is_contract_wired("tss_backtest_ready", tmp_path)
