from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys

import pytest

from tools.stage_display_runtime import (
    StageDisplayRenderError,
    UnsupportedStageError,
    build_stage_display_summary,
    write_stage_display_report,
)


def _build_csf_data_ready_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_factor_panel"
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    (stage_dir / "shared_feature_base").mkdir()
    (stage_dir / "panel_manifest.json").write_text(
        json.dumps(
            {
                "date_key": "trade_date",
                "asset_key": "asset_id",
                "panel_frequency": "1d",
                "coverage_rule": "date x asset explicit membership",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "replay_command": "python rebuild_csf_data_ready.py --lineage btc_factor_panel",
                "program_artifacts": ["rebuild_csf_data_ready.py", "shared_feature_base"],
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
        "artifact_catalog.md",
        "field_dictionary.md",
        "rebuild_csf_data_ready.py",
        "csf_data_ready_gate_decision.md",
    ]:
        (stage_dir / name).write_text("ok\n", encoding="utf-8")
    return lineage_root


def _write_renderer_stub(tmp_path: Path, *, fail: bool = False) -> Path:
    script_path = tmp_path / ("fail_renderer.py" if fail else "ok_renderer.py")
    script_path.write_text(
        """
from __future__ import annotations

import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output-last-message', required=True)
parser.add_argument('prompt_arg')
args = parser.parse_args()
prompt = sys.stdin.read()
if "Structured summary JSON" not in prompt:
    print("missing prompt payload", file=sys.stderr)
    raise SystemExit(4)
if "--fail" in prompt:
    print("unexpected fail token", file=sys.stderr)
    raise SystemExit(5)
if "fail_renderer.py" in __file__:
    print("renderer exploded", file=sys.stderr)
    raise SystemExit(3)
Path(args.output_last_message).write_text(
    "<!DOCTYPE html><html><body><h1>CSF Data Ready Display</h1><p>available</p></body></html>\\n",
    encoding='utf-8',
)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return script_path


def test_build_stage_display_summary_for_csf_data_ready_has_stable_sections_and_markers(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id="csf_data_ready")

    assert summary["stage_id"] == "csf_data_ready"
    assert summary["supported_stage_ids"] == ["csf_data_ready"]
    assert summary["status"] == "complete"
    assert summary["missing_required_inputs"] == []
    assert summary["section_order"] == [
        "Panel Contract And Core Evidence",
        "Coverage And Eligibility Evidence",
        "Delivery And Rebuild Evidence",
    ]
    assert [section["title"] for section in summary["sections"]] == summary["section_order"]
    first_section_items = summary["sections"][0]["items"]
    assert any(item["text"] == "date_key: trade_date" for item in first_section_items)
    assert any(item["marker"] == "question" for section in summary["sections"] for item in section["items"])


def test_write_stage_display_report_writes_summary_and_html_via_subagent_command(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)
    renderer = _write_renderer_stub(tmp_path)

    result = write_stage_display_report(
        lineage_root=lineage_root,
        stage_id="csf_data_ready",
        renderer_command=[sys.executable, str(renderer)],
    )

    summary_path = Path(result["structured_summary_path"])
    html_path = Path(result["html_path"])
    assert result["render_status"] == "complete"
    assert result["required_subagent"] is True
    assert summary_path.exists()
    assert html_path.exists()
    assert "CSF Data Ready Display" in html_path.read_text(encoding="utf-8")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["render_status"] == "complete"
    assert summary["artifacts"]["html_path"] == str(html_path)


# 失败时保留 summary 诊断件，但不能留下伪成功 HTML。
def test_write_stage_display_report_preserves_incomplete_summary_when_subagent_fails(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)
    renderer = _write_renderer_stub(tmp_path, fail=True)

    with pytest.raises(StageDisplayRenderError):
        write_stage_display_report(
            lineage_root=lineage_root,
            stage_id="csf_data_ready",
            renderer_command=[sys.executable, str(renderer)],
        )

    summary_path = lineage_root / "reports" / "stage_display" / "csf_data_ready.summary.json"
    html_path = lineage_root / "reports" / "stage_display" / "csf_data_ready.summary.html"
    assert summary_path.exists()
    assert not html_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["render_status"] == "incomplete_diagnostic"
    assert "renderer exploded" in summary["render_error"]


def test_unsupported_stage_fails_without_writing_partial_outputs(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    with pytest.raises(UnsupportedStageError):
        write_stage_display_report(
            lineage_root=lineage_root,
            stage_id="signal_ready",
            renderer_command=[sys.executable, str(_write_renderer_stub(tmp_path))],
        )

    assert not (lineage_root / "reports" / "stage_display").exists()


def test_run_stage_display_script_uses_renderer_override(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_stage_display.py"
    lineage_root = _build_csf_data_ready_lineage(tmp_path)
    renderer = _write_renderer_stub(tmp_path)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-id",
            "csf_data_ready",
            "--lineage-root",
            str(lineage_root),
            "--renderer-command",
            f"{sys.executable} {renderer}",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["supported_stage_ids"] == ["csf_data_ready"]
    assert Path(manifest["structured_summary_path"]).exists()
    assert Path(manifest["html_path"]).exists()
