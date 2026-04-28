from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_test_evidence_rejects_selected_variant_outside_train_kept_set as _case,
)


def test_tss_test_evidence_semantic_validator_rejects_untrained_selected_variant(tmp_path: Path) -> None:
    _case(tmp_path)
