from tests.helpers.tss_stage_parity import assert_tss_sop_documents_contract_first_usage


def test_tss_train_freeze_sop_documents_contract_first_usage() -> None:
    assert_tss_sop_documents_contract_first_usage("tss_train_freeze")
