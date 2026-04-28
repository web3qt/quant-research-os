from tests.helpers.tss_stage_parity import assert_tss_artifact_contract_is_stage_specific


def test_tss_test_evidence_artifact_contract_is_stage_specific() -> None:
    assert_tss_artifact_contract_is_stage_specific("tss_test_evidence")
