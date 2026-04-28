from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_signal_ready_rejects_forward_label_input_binding as _reject_case,
)
from tests.runtime.test_tss_contract_validators import (
    test_tss_signal_ready_accepts_feature_base_inputs as _accept_case,
)


def test_tss_signal_ready_semantic_validator_rejects_forward_label_inputs(tmp_path: Path) -> None:
    _reject_case(tmp_path)


def test_tss_signal_ready_semantic_validator_accepts_feature_base_inputs(tmp_path: Path) -> None:
    _accept_case(tmp_path)
