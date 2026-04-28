from tests.helpers.tss_stage_parity import assert_tss_artifact_contract_is_stage_specific


def test_tss_train_freeze_artifact_contract_is_stage_specific() -> None:
    assert_tss_artifact_contract_is_stage_specific("tss_train_freeze")
