from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_train_freeze_rejects_kept_variant_outside_candidate_set as _case,
)


def test_tss_train_freeze_semantic_validator_rejects_unfrozen_kept_variant(tmp_path: Path) -> None:
    _case(tmp_path)
