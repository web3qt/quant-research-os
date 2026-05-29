from __future__ import annotations

from pathlib import Path

import yaml

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
    program_dir = ensure_stage_program(lineage_root, "tss_data_ready")
    manifest_path = program_dir / "stage_program.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("data_implementation_contract", None)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")

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
