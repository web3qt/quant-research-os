from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_holdout_validation_rejects_tuning_performed as _case,
)


def test_tss_holdout_validation_semantic_validator_rejects_holdout_tuning(tmp_path: Path) -> None:
    _case(tmp_path)
