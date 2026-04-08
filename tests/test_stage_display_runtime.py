from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_run_research_session_script import _write_yaml

from tools.stage_display_runtime import export_stage_display, render_stage_display_html


# 用最小夹具锁住 qros-stage-display 的成功/失败产物合同。
def _build_csf_data_ready_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_lineage"
    mandate_dir = lineage_root / "01_mandate"
    stage_dir = lineage_root / "02_csf_data_ready"
    mandate_dir.mkdir(parents=True)
    stage_dir.mkdir(parents=True)

    _write_yaml(
        mandate_dir / "research_route.yaml",
        {
            "research_route": "cross_sectional_factor",
        },
    )

    (stage_dir / "panel_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_data_ready",
                "lineage_id": lineage_root.name,
                "panel_primary_key": ["date", "asset"],
                "cross_section_time_key": "date",
                "asset_key": "asset",
                "shared_feature_outputs": ["shared_feature_base"],
                "machine_artifacts": [
                    "panel_manifest.json",
                    "asset_universe_membership.parquet",
                    "eligibility_base_mask.parquet",
                    "cross_section_coverage.parquet",
                    "shared_feature_base/",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "asset_universe_membership.parquet",
        "eligibility_base_mask.parquet",
        "cross_section_coverage.parquet",
        "csf_data_contract.md",
        "run_manifest.json",
        "artifact_catalog.md",
        "field_dictionary.md",
        "csf_data_ready_gate_decision.md",
        "rebuild_csf_data_ready.py",
    ]:
        (stage_dir / name).write_text("ok\n", encoding="utf-8")
    (stage_dir / "shared_feature_base").mkdir()
    (stage_dir / "asset_taxonomy_snapshot.parquet").write_text("ok\n", encoding="utf-8")
    return lineage_root


def test_export_stage_display_writes_structured_summary_and_html(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    manifest = export_stage_display(
        lineage_root=lineage_root,
        stage_id="csf_data_ready",
        html_renderer=render_stage_display_html,
    )

    summary_path = Path(manifest["structured_summary_path"])
    html_path = Path(manifest["html_path"])

    assert summary_path.exists()
    assert html_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")

    assert summary["stage_id"] == "csf_data_ready"
    assert summary["artifact_status"] == "complete"
    assert summary["html_path"] == str(html_path)
    assert [section["title"] for section in summary["sections"]] == [
        "Panel Contract And Coverage",
        "Eligibility / Universe Artifacts",
        "Shared Feature Base And Runtime",
    ]
    assert "CSF Data Ready Display Summary" in html
    assert "Panel Contract And Coverage" in html
    assert "Eligibility / Universe Artifacts" in html
    assert "Shared Feature Base And Runtime" in html


def test_unsupported_stage_fails_without_partial_html_or_summary(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    with pytest.raises(ValueError, match="Unsupported stage for qros-stage-display: shadow"):
        export_stage_display(
            lineage_root=lineage_root,
            stage_id="shadow",
            html_renderer=render_stage_display_html,
        )

    display_dir = lineage_root / "reports" / "stage_display" / "shadow"
    assert not display_dir.exists()
