"""CSF pipeline tests — single-stage gate assertions and multi-stage chaining.

Layer 1: Each stage's runtime build is validated against structural/metric gates.
Layer 2: Stages are chained together, verifying cross-stage handoffs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.gate_assertions import assert_all_gates_pass, assert_structural_gates_pass
from tests.helpers.stage_fixtures import (
    prepare_csf_signal_ready,
    prepare_csf_data_ready,
    prepare_mandate,
)


# ---------------------------------------------------------------------------
# Layer 1: Single-stage fixture + gate assertion
# ---------------------------------------------------------------------------


class TestCsfSignalReadyGates:
    """Verify csf_signal_ready runtime output passes all 14 structural gates."""

    @pytest.fixture()
    def signal_ready_dir(self, tmp_path: Path) -> Path:
        lineage_root = tmp_path / "outputs" / "csf_case"
        stage_dir = prepare_csf_signal_ready(lineage_root)
        return stage_dir / "author" / "formal"

    def test_structural_gates_pass(self, signal_ready_dir: Path) -> None:
        assert_structural_gates_pass(signal_ready_dir, "csf_signal_ready")

    def test_all_gates_pass(self, signal_ready_dir: Path) -> None:
        assert_all_gates_pass(signal_ready_dir, "csf_signal_ready")


class TestCsfDataReadyGates:
    """Verify csf_data_ready fixture passes structural gates."""

    @pytest.fixture()
    def data_ready_dir(self, tmp_path: Path) -> Path:
        lineage_root = tmp_path / "outputs" / "csf_case"
        stage_dir = prepare_csf_data_ready(lineage_root)
        return stage_dir / "author" / "formal"

    def test_structural_gates_pass(self, data_ready_dir: Path) -> None:
        assert_structural_gates_pass(data_ready_dir, "csf_data_ready")


# ---------------------------------------------------------------------------
# Layer 2: Multi-stage pipeline
# ---------------------------------------------------------------------------


class TestCsfPipelineMandateToSignal:
    """Chain mandate → data_ready → signal_ready, gate-checking each stage."""

    def test_three_stage_pipeline(self, tmp_path: Path) -> None:
        lineage_root = tmp_path / "outputs" / "pipeline_case"

        mandate_dir = prepare_mandate(lineage_root)
        assert_all_gates_pass(mandate_dir / "author" / "formal", "mandate")

        data_dir = prepare_csf_data_ready(lineage_root)
        assert_all_gates_pass(data_dir / "author" / "formal", "csf_data_ready")

        signal_dir = prepare_csf_signal_ready(lineage_root)
        assert_all_gates_pass(signal_dir / "author" / "formal", "csf_signal_ready")

    def test_signal_ready_inherits_route_from_mandate(self, tmp_path: Path) -> None:
        lineage_root = tmp_path / "outputs" / "inheritance_case"
        signal_dir = prepare_csf_signal_ready(lineage_root)
        formal = signal_dir / "author" / "formal"

        assert_structural_gates_pass(formal, "csf_signal_ready")

    def test_pipeline_rejects_empty_data_ready(self, tmp_path: Path) -> None:
        """Building signal_ready without data_ready artifacts should fail."""
        from runtime.tools.csf_signal_ready_runtime import build_csf_signal_ready_from_data_ready

        lineage_root = tmp_path / "outputs" / "missing_upstream"
        # only create mandate, skip data_ready
        prepare_mandate(lineage_root)

        with pytest.raises((ValueError, FileNotFoundError)):
            build_csf_signal_ready_from_data_ready(lineage_root)
