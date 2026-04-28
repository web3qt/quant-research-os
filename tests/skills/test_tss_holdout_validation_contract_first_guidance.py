from tests.helpers.tss_stage_parity import assert_tss_skill_guidance_is_contract_first


def test_tss_holdout_validation_skills_are_contract_first() -> None:
    assert_tss_skill_guidance_is_contract_first("tss_holdout_validation")
