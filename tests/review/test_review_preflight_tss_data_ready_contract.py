from __future__ import annotations

from pathlib import Path

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program
from tests.helpers.tss_stage_parity import assert_tss_review_preflight_is_contract_wired


def test_review_preflight_tss_data_ready_is_contract_wired(tmp_path: Path) -> None:
    assert_tss_review_preflight_is_contract_wired("tss_data_ready", tmp_path)


def test_review_preflight_tss_data_ready_blocks_missing_data_implementation_declaration(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    stage_dir = lineage_root / "02_tss_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    ensure_stage_program(lineage_root, "tss_data_ready")

    payload = run_review_preflight(
        explicit_context={
            "stage": "tss_data_ready",
            "stage_dir": str(stage_dir),
            "lineage_root": str(lineage_root),
            "author_formal_dir": str(formal_dir),
            "lineage_id": lineage_root.name,
        }
    )

    assert payload["stage"] == "tss_data_ready"
    assert payload["status"] == "FAIL"
    assert any("DATA_IMPL_DECLARATION_MISSING" in item for item in payload["content_findings"])
