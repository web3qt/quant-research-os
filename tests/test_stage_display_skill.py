from __future__ import annotations

import json
import os
from pathlib import Path
from subprocess import run
import sys

import pytest

import tools.stage_display_runtime as stage_display_runtime
from tools.stage_display_runtime import (
    StageDisplayRenderError,
    UnsupportedStageError,
    build_stage_display_summary,
    export_stage_display,
    resolve_stage_display_config,
    supported_stage_ids,
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
    (stage_dir / "stage_completion_certificate.yaml").write_text("stage_status: PASS\nfinal_verdict: PASS\n", encoding="utf-8")
    (stage_dir / f"{stage_id}_marker.txt").write_text("ok\n", encoding="utf-8")
    return lineage_root


def test_supported_stage_ids_cover_current_reviewable_stages() -> None:
    assert supported_stage_ids() == EXPECTED_SUPPORTED_STAGE_IDS


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
    assert any(
        item["text"] == "research_question: BTC 冲击发生时，哪些 ALT 在同一横截面里更容易出现后续相对弱势？"
        for item in summary["sections"][0]["items"]
    )
    assert any(item["text"] == "review_verdict: PASS" for item in summary["sections"][2]["items"])


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
    assert any(item["text"] == "date_key: trade_date" for item in summary["sections"][0]["items"])
    assert any(item["marker"] == "question" for section in summary["sections"] for item in section["items"])


def test_build_stage_display_summary_for_generic_signal_ready_uses_generic_sections(tmp_path: Path) -> None:
    lineage_root = _build_generic_stage_lineage(tmp_path, stage_id="signal_ready")

    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id="signal_ready")

    assert summary["stage_id"] == "signal_ready"
    assert summary["title"] == "Signal Ready Display Summary"
    assert summary["supported_stage_ids"] == list(EXPECTED_SUPPORTED_STAGE_IDS)
    assert summary["status"] == "complete"
    assert summary["section_order"] == [
        "Stage Metadata And Core Evidence",
        "Frozen Artifact Inventory",
        "Review Closure Evidence",
    ]
    assert any(item["text"] == "stage_id: signal_ready" for item in summary["sections"][0]["items"])
    assert any(item["text"] == "review_verdict: PASS" for item in summary["sections"][0]["items"])


def test_write_stage_display_report_writes_summary_and_html_for_mandate(tmp_path: Path) -> None:
    lineage_root = _build_mandate_lineage(tmp_path)

    result = write_stage_display_report(lineage_root=lineage_root, stage_id="mandate")

    summary_path = Path(result["structured_summary_path"])
    html_path = Path(result["html_path"])
    assert result["render_status"] == "complete"
    assert summary_path.exists()
    assert html_path.exists()
    assert not (lineage_root / "reports" / "stage_display" / "mandate.display_request.json").exists()
    assert not (lineage_root / "reports" / "stage_display" / "mandate.display_prompt.txt").exists()
    assert not (lineage_root / "reports" / "stage_display" / "mandate.display_result.json").exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["render_status"] == "complete"
    assert summary["artifacts"]["html_path"] == str(html_path)
    assert summary["artifacts"]["summary_path"] == str(summary_path)


def test_write_stage_display_report_marks_failed_summary_when_render_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    def _boom(summary: dict[str, object]) -> str:
        raise StageDisplayRenderError("renderer exploded")

    monkeypatch.setattr(stage_display_runtime, "render_stage_display_html", _boom)
    result = write_stage_display_report(lineage_root=lineage_root, stage_id="csf_data_ready")

    summary_path = Path(result["structured_summary_path"])
    html_path = Path(result["html_path"])
    assert result["render_status"] == "failed"
    assert summary_path.exists()
    assert not html_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["render_status"] == "failed"
    assert summary["render_error"] == "renderer exploded"


@pytest.mark.parametrize("stage_id", GENERIC_SUPPORTED_STAGE_IDS)
def test_write_stage_display_report_supports_every_generic_supported_stage(tmp_path: Path, stage_id: str) -> None:
    lineage_root = _build_generic_stage_lineage(tmp_path, stage_id=stage_id)

    result = write_stage_display_report(lineage_root=lineage_root, stage_id=stage_id)

    assert result["render_status"] == "complete"
    summary_path = Path(result["structured_summary_path"])
    html_path = Path(result["html_path"])
    assert summary_path.exists()
    assert html_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["stage_id"] == stage_id
    assert summary["render_status"] == "complete"


def test_unsupported_stage_fails_without_writing_partial_outputs(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    with pytest.raises(UnsupportedStageError):
        write_stage_display_report(lineage_root=lineage_root, stage_id="shadow")

    assert not (lineage_root / "reports" / "stage_display").exists()


def test_export_stage_display_writes_runtime_owned_compat_summary_and_html(tmp_path: Path) -> None:
    lineage_root = _build_csf_data_ready_lineage(tmp_path)

    manifest = export_stage_display(lineage_root=lineage_root, stage_id="csf_data_ready")

    summary_path = Path(manifest["structured_summary_path"])
    html_path = Path(manifest["html_path"])
    assert summary_path.exists()
    assert html_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["artifact_status"] == "complete"
    assert summary["stage_id"] == "csf_data_ready"
    assert summary["html_path"] == str(html_path)


def test_run_stage_display_script_writes_summary_and_html(tmp_path: Path) -> None:
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
    assert manifest["render_status"] == "complete"
    assert Path(manifest["structured_summary_path"]).exists()
    assert Path(manifest["html_path"]).exists()


def test_run_stage_display_script_returns_nonzero_when_runtime_render_fails(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_stage_display.py"
    lineage_root = _build_mandate_lineage(tmp_path)
    env = {"QROS_STAGE_DISPLAY_FORCE_RENDER_ERROR": "renderer exploded"}

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
        env={**os.environ, **env},
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["render_status"] == "failed"
    assert "renderer exploded" in payload["render_error"]


@pytest.mark.parametrize("flag,value", [("--renderer-command", "python stub.py"), ("--complete-from-html", "rendered.html"), ("--render-error", "boom")])
def test_run_stage_display_script_rejects_removed_subagent_flags(tmp_path: Path, flag: str, value: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_stage_display.py"
    lineage_root = _build_mandate_lineage(tmp_path)
    if flag == "--complete-from-html":
        html_path = tmp_path / value
        html_path.write_text("<!DOCTYPE html><html><body>Rendered</body></html>\n", encoding="utf-8")
        value = str(html_path)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--stage-id",
            "mandate",
            "--lineage-root",
            str(lineage_root),
            flag,
            value,
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode != 0
    assert flag in result.stderr
