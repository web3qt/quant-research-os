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
    load_stage_display_request,
    load_stage_display_result,
    prepare_stage_display_handoff,
    resolve_stage_display_config,
    supported_stage_ids,
    write_stage_display_result,
    write_stage_display_report,
)


EXPECTED_SUPPORTED_STAGE_IDS = (
    "mandate",
    "csf_data_ready",
    "data_ready",
    "signal_ready",
    "train_freeze",
    "test_evidence",
    "backtest_ready",
    "holdout_validation",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)
GENERIC_SUPPORTED_STAGE_IDS = tuple(
    stage_id for stage_id in EXPECTED_SUPPORTED_STAGE_IDS if stage_id not in {"mandate", "csf_data_ready"}
)


def _build_mandate_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = lineage_root / "01_mandate"
    stage_dir.mkdir(parents=True)
    (stage_dir / "mandate.md").write_text(
        "\n".join(
            [
                "# Mandate",
                "",
                "- 研究问题: BTC 冲击发生时，哪些 ALT 在同一横截面里更容易出现后续相对弱势？",
                "- 主假设: BTC 冲击会暴露横截面脆弱性差异。",
                "- 对立假设: 只是共同 beta 去风险，并不存在相对弱势机制。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "research_scope.md").write_text(
        "\n".join(
            [
                "# Research Scope",
                "",
                "- 市场: crypto perpetuals",
                "- 数据来源: /Users/mac08/workspace/coin-data",
                "- Universe: liquid ALT perpetuals ex-BTC",
                "- Bar 粒度: 5m",
                "- 研究任务: cross-sectional ranking",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "research_route.yaml").write_text(
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_only_rank",
                "neutralization_policy: group_neutral",
                "target_strategy_reference: post_shock_weakness_v1",
                "group_taxonomy_reference: sector_bucket_v1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_dir / "time_split.json").write_text('{"train":"2024-01-01/2024-06-30","test":"2024-07-01/2024-09-30","holdout":"2024-10-01/2024-12-31"}\n', encoding="utf-8")
    (stage_dir / "parameter_grid.yaml").write_text("shock_window: [15m, 30m]\n", encoding="utf-8")
    (stage_dir / "run_config.toml").write_text("no_lookahead = true\n", encoding="utf-8")
    (stage_dir / "artifact_catalog.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")
    (stage_dir / "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_completion_certificate.yaml").write_text("stage_status: PASS\nfinal_verdict: PASS\n", encoding="utf-8")
    return lineage_root


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


def _build_generic_signal_ready_lineage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "btc_signal_lineage"
    stage_dir = lineage_root / "03_signal_ready"
    stage_dir.mkdir(parents=True)
    (stage_dir / "params").mkdir()
    (stage_dir / "artifact_catalog.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")
    (stage_dir / "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_completion_certificate.yaml").write_text("stage_status: PASS\nfinal_verdict: PASS\n", encoding="utf-8")
    (stage_dir / "signal_contract.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "signal_gate_decision.md").write_text("ok\n", encoding="utf-8")
    return lineage_root


def _build_generic_stage_lineage(tmp_path: Path, *, stage_id: str) -> Path:
    lineage_root = tmp_path / "outputs" / f"{stage_id}_lineage"
    config = resolve_stage_display_config(stage_id)
    stage_dir = lineage_root / config.stage_dir_name
    stage_dir.mkdir(parents=True)
    (stage_dir / "artifact_catalog.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "field_dictionary.md").write_text("ok\n", encoding="utf-8")
    (stage_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")
    (stage_dir / "latest_review_pack.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_gate_review.yaml").write_text("status: ok\n", encoding="utf-8")
    (stage_dir / "stage_completion_certificate.yaml").write_text(
        "stage_status: PASS\nfinal_verdict: PASS\n",
        encoding="utf-8",
    )
    (stage_dir / f"{stage_id}_marker.txt").write_text("ok\n", encoding="utf-8")
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
    assert summary["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
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


def test_supported_stage_ids_cover_current_reviewable_stages() -> None:
    assert supported_stage_ids() == EXPECTED_SUPPORTED_STAGE_IDS


def test_build_stage_display_summary_for_generic_signal_ready_uses_generic_sections(tmp_path: Path) -> None:
    lineage_root = _build_generic_signal_ready_lineage(tmp_path)

    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id="signal_ready")

    assert summary["stage_id"] == "signal_ready"
    assert summary["title"] == "Signal Ready Display Summary"
    assert summary["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert summary["status"] == "complete"
    assert summary["missing_required_inputs"] == []
    assert summary["section_order"] == [
        "Stage Metadata And Core Evidence",
        "Frozen Artifact Inventory",
        "Review Closure Evidence",
    ]
    assert [section["title"] for section in summary["sections"]] == summary["section_order"]
    first_section_items = summary["sections"][0]["items"]
    assert any(item["text"] == "stage_id: signal_ready" for item in first_section_items)
    assert any(item["text"] == "review_verdict: PASS" for item in first_section_items)
    inventory_items = summary["sections"][1]["items"]
    assert any(item["text"] == "params/: directory present" for item in inventory_items)
    assert any(item["text"] == "signal_contract.md: present" for item in inventory_items)


def test_build_stage_display_summary_for_mandate_has_bounded_sections_and_review_evidence(tmp_path: Path) -> None:
    lineage_root = _build_mandate_lineage(tmp_path)

    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id="mandate")

    assert summary["stage_id"] == "mandate"
    assert summary["title"] == "Mandate Display Summary"
    assert summary["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert summary["status"] == "complete"
    assert summary["missing_required_inputs"] == []
    assert summary["section_order"] == [
        "Mandate Question And Route",
        "Scope And Data Contract",
        "Execution And Review Evidence",
    ]
    first_section_items = summary["sections"][0]["items"]
    assert any(
        item["text"] == "research_question: BTC 冲击发生时，哪些 ALT 在同一横截面里更容易出现后续相对弱势？"
        for item in first_section_items
    )
    assert any(item["text"] == "review_verdict: PASS" for item in summary["sections"][2]["items"])


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


def test_prepare_stage_display_handoff_writes_summary_request_and_prompt_only(tmp_path: Path) -> None:
    lineage_root = _build_mandate_lineage(tmp_path)

    result = prepare_stage_display_handoff(
        lineage_root=lineage_root,
        stage_id="mandate",
    )

    assert Path(result["structured_summary_path"]).exists()
    assert Path(result["request_path"]).exists()
    assert Path(result["prompt_path"]).exists()
    assert not Path(result["html_path"]).exists()
    assert not Path(result["result_path"]).exists()
    request = load_stage_display_request(lineage_root=lineage_root, stage_id="mandate")
    assert request is not None
    assert request["status"] == "awaiting_native_subagent_render"


def test_write_stage_display_report_supports_mandate(tmp_path: Path) -> None:
    lineage_root = _build_mandate_lineage(tmp_path)
    renderer = _write_renderer_stub(tmp_path)

    result = write_stage_display_report(
        lineage_root=lineage_root,
        stage_id="mandate",
        renderer_command=[sys.executable, str(renderer)],
    )

    summary_path = Path(result["structured_summary_path"])
    html_path = Path(result["html_path"])
    assert result["render_status"] == "complete"
    assert summary_path.exists()
    assert html_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["stage_id"] == "mandate"
    assert summary["render_status"] == "complete"


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
    result_path = lineage_root / "reports" / "stage_display" / "csf_data_ready.display_result.json"
    assert summary_path.exists()
    assert not html_path.exists()
    assert result_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["render_status"] == "failed"
    assert "renderer exploded" in summary["render_error"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"


def test_write_stage_display_result_writes_completion_artifact_from_html(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)
    prepare_stage_display_handoff(lineage_root=lineage_root, stage_id="csf_data_ready")

    payload = write_stage_display_result(
        lineage_root=lineage_root,
        stage_id="csf_data_ready",
        html="<!DOCTYPE html><html><body><h1>Rendered</h1></body></html>",
        rendered_by="visible-subagent",
    )

    assert payload["status"] == "complete"
    result = load_stage_display_result(lineage_root=lineage_root, stage_id="csf_data_ready")
    assert result is not None
    assert result["status"] == "complete"
    assert (lineage_root / "reports" / "stage_display" / "csf_data_ready.summary.html").exists()


@pytest.mark.parametrize("stage_id", GENERIC_SUPPORTED_STAGE_IDS)
def test_prepare_and_complete_stage_display_for_every_generic_supported_stage(
    tmp_path: Path,
    stage_id: str,
) -> None:
    lineage_root = _build_generic_stage_lineage(tmp_path, stage_id=stage_id)

    handoff = prepare_stage_display_handoff(lineage_root=lineage_root, stage_id=stage_id)
    assert Path(handoff["structured_summary_path"]).exists()
    assert Path(handoff["request_path"]).exists()
    assert Path(handoff["prompt_path"]).exists()
    summary = json.loads(Path(handoff["structured_summary_path"]).read_text(encoding="utf-8"))
    assert summary["stage_id"] == stage_id
    assert summary["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert summary["status"] == "complete"

    result = write_stage_display_result(
        lineage_root=lineage_root,
        stage_id=stage_id,
        html=f"<!DOCTYPE html><html><body><h1>{stage_id}</h1></body></html>",
        rendered_by="visible-subagent",
    )
    assert result["status"] == "complete"
    assert Path(handoff["html_path"]).exists()
    loaded_result = load_stage_display_result(lineage_root=lineage_root, stage_id=stage_id)
    assert loaded_result is not None
    assert loaded_result["status"] == "complete"


def test_unsupported_stage_fails_without_writing_partial_outputs(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    with pytest.raises(UnsupportedStageError):
        write_stage_display_report(
            lineage_root=lineage_root,
            stage_id="shadow",
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
            "mandate",
            "--lineage-root",
            str(_build_mandate_lineage(tmp_path)),
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
    assert manifest["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert Path(manifest["structured_summary_path"]).exists()
    assert Path(manifest["html_path"]).exists()


def test_run_stage_display_script_default_writes_handoff_only(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_stage_display.py"
    lineage_root = _build_mandate_lineage(tmp_path)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-id",
            "mandate",
            "--lineage-root",
            str(lineage_root),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert Path(manifest["structured_summary_path"]).exists()
    assert Path(manifest["request_path"]).exists()
    assert Path(manifest["prompt_path"]).exists()
    assert not Path(manifest["html_path"]).exists()


def test_run_stage_display_script_can_write_completion_from_html(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_stage_display.py"
    lineage_root = _build_mandate_lineage(tmp_path)
    html_input = tmp_path / "rendered.html"
    html_input.write_text("<!DOCTYPE html><html><body><h1>Mandate</h1></body></html>\n", encoding="utf-8")

    prep = run(
        [
            sys.executable,
            str(script_path),
            "--stage-id",
            "mandate",
            "--lineage-root",
            str(lineage_root),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert prep.returncode == 0, prep.stderr

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-id",
            "mandate",
            "--lineage-root",
            str(lineage_root),
            "--complete-from-html",
            str(html_input),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["status"] == "complete"
    assert (lineage_root / "reports" / "stage_display" / "mandate.summary.html").exists()


def test_run_stage_display_script_uses_renderer_override_for_csf_data_ready(tmp_path: Path) -> None:
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
    assert manifest["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert Path(manifest["structured_summary_path"]).exists()
    assert Path(manifest["html_path"]).exists()
