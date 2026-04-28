"""TSS pipeline tests — mirrors CSF pipeline coverage for time_series_signal."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.gate_assertions import assert_all_gates_pass, assert_structural_gates_pass
from tests.helpers.stage_fixtures import (
    prepare_tss_backtest_ready,
    prepare_tss_data_ready,
    prepare_tss_holdout_validation,
    prepare_tss_mandate,
    prepare_tss_signal_ready,
    prepare_tss_test_evidence,
    prepare_tss_train_freeze,
)


class TestTssSignalReadyGates:
    @pytest.fixture()
    def signal_ready_dir(self, tmp_path: Path) -> Path:
        lineage_root = tmp_path / "outputs" / "tss_case"
        stage_dir = prepare_tss_signal_ready(lineage_root)
        return stage_dir / "author" / "formal"

    def test_structural_gates_pass(self, signal_ready_dir: Path) -> None:
        assert_structural_gates_pass(signal_ready_dir, "tss_signal_ready")

    def test_all_gates_pass(self, signal_ready_dir: Path) -> None:
        assert_all_gates_pass(signal_ready_dir, "tss_signal_ready")


class TestTssDataReadyGates:
    @pytest.fixture()
    def data_ready_dir(self, tmp_path: Path) -> Path:
        lineage_root = tmp_path / "outputs" / "tss_case"
        stage_dir = prepare_tss_data_ready(lineage_root)
        return stage_dir / "author" / "formal"

    def test_structural_gates_pass(self, data_ready_dir: Path) -> None:
        assert_structural_gates_pass(data_ready_dir, "tss_data_ready")


class TestTssPipelineMandateToHoldout:
    def test_full_tss_pipeline(self, tmp_path: Path) -> None:
        lineage_root = tmp_path / "outputs" / "pipeline_case"

        mandate_dir = prepare_tss_mandate(lineage_root)
        assert_all_gates_pass(mandate_dir / "author" / "formal", "mandate")

        for stage_id, builder in [
            ("tss_data_ready", prepare_tss_data_ready),
            ("tss_signal_ready", prepare_tss_signal_ready),
            ("tss_train_freeze", prepare_tss_train_freeze),
            ("tss_test_evidence", prepare_tss_test_evidence),
            ("tss_backtest_ready", prepare_tss_backtest_ready),
            ("tss_holdout_validation", prepare_tss_holdout_validation),
        ]:
            stage_dir = builder(lineage_root)
            assert_all_gates_pass(stage_dir / "author" / "formal", stage_id)

    def test_signal_ready_inherits_time_series_route_from_mandate(self, tmp_path: Path) -> None:
        lineage_root = tmp_path / "outputs" / "inheritance_case"
        signal_dir = prepare_tss_signal_ready(lineage_root)

        assert_structural_gates_pass(signal_dir / "author" / "formal", "tss_signal_ready")

    def test_pipeline_rejects_empty_data_ready(self, tmp_path: Path) -> None:
        from runtime.tools.tss_signal_ready_runtime import build_tss_signal_ready_from_data_ready

        lineage_root = tmp_path / "outputs" / "missing_upstream"
        prepare_tss_mandate(lineage_root)

        with pytest.raises((ValueError, FileNotFoundError)):
            build_tss_signal_ready_from_data_ready(lineage_root)
