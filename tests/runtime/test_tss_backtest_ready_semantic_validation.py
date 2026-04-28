from pathlib import Path

from tests.runtime.test_tss_contract_validators import (
    test_tss_backtest_ready_requires_net_after_cost_rule as _case,
)


def test_tss_backtest_ready_semantic_validator_requires_net_after_cost_rule(tmp_path: Path) -> None:
    _case(tmp_path)
