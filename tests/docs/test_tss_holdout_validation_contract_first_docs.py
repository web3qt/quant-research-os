from tests.helpers.tss_stage_parity import assert_tss_sop_documents_contract_first_usage


def test_tss_holdout_validation_sop_documents_contract_first_usage() -> None:
    assert_tss_sop_documents_contract_first_usage("tss_holdout_validation")
