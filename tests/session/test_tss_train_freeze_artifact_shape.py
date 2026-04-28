from pathlib import Path

from tests.helpers.tss_stage_parity import assert_tss_generated_artifacts_match_contract


def test_generated_tss_train_freeze_artifacts_match_contract(tmp_path: Path) -> None:
    assert_tss_generated_artifacts_match_contract("tss_train_freeze", tmp_path)
