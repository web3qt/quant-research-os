from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_data_ready_rejects_forward_label_timestamp_not_after_signal_timestamp as _case,
)


def test_tss_data_ready_semantic_validator_rejects_forward_label_leakage(tmp_path: Path) -> None:
    _case(tmp_path)
