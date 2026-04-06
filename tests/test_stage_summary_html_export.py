from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys

from tests.lineage_program_support import write_fake_stage_provenance
from tests.test_run_research_session_script import _write_yaml
from tools.research_session_reflection import build_data_ready_reflection_payload
from tools.stage_summary_html import build_subagent_render_prompt, render_data_ready_summary_html, write_subagent_bundle


# 用最小夹具锁住 data_ready v1 的 HTML export 语义边界。
def _build_signal_ready_confirmation_lineage(tmp_path: Path) -> tuple[Path, Path]:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = lineage_root / "02_data_ready"
    mandate_dir.mkdir(parents=True)
    data_ready_dir.mkdir(parents=True)
    _write_yaml(
        mandate_dir / "research_route.yaml",
        {
            "research_route": "time_series_signal",
        },
    )
    for name in [
        "qc_report.parquet",
        "dataset_manifest.json",
        "validation_report.md",
        "data_contract.md",
        "dedupe_rule.md",
        "universe_summary.md",
        "universe_exclusions.csv",
        "universe_exclusions.md",
        "data_ready_gate_decision.md",
        "run_manifest.json",
        "rebuild_data_ready.py",
        "artifact_catalog.md",
        "field_dictionary.md",
        "stage_completion_certificate.yaml",
    ]:
        (data_ready_dir / name).write_text("ok\n", encoding="utf-8")
    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_dir / name).mkdir()
    write_fake_stage_provenance(lineage_root, "data_ready")
    return outputs_root, lineage_root


def test_build_data_ready_reflection_payload_preserves_metadata_and_order(tmp_path: Path) -> None:
    _, lineage_root = _build_signal_ready_confirmation_lineage(tmp_path)

    payload = build_data_ready_reflection_payload(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert payload is not None
    assert payload["stage_id"] == "data_ready"
    assert payload["lineage_id"] == "btc_leads_alts"
    assert payload["session_stage"] == "signal_ready_confirmation_pending"
    assert [section["title"] for section in payload["sections"]] == [
        "Data Coverage And Gaps",
        "QC / Anomaly Summary",
        "Artifact Directory And Key Files",
    ]


def test_payload_and_html_preserve_missing_evidence_markers(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_leads_alts"
    stage_dir = lineage_root / "02_data_ready"
    stage_dir.mkdir(parents=True)
    (stage_dir / "aligned_bars").mkdir()
    (stage_dir / "dataset_manifest.json").write_text("ok\n", encoding="utf-8")

    payload = build_data_ready_reflection_payload(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert payload is not None
    flattened = "\n".join(line for section in payload["sections"] for line in section["lines"])
    assert "qc_report.parquet: missing" in flattened
    assert "question: which missing QC artifacts must be reviewed before the stage can be trusted?" in flattened

    html = render_data_ready_summary_html(payload)
    assert "qc_report.parquet: missing" in html
    assert "question: which missing QC artifacts must be reviewed before the stage can be trusted?" in html


# subagent prompt/bundle 只验证 handoff contract，不在 Python runtime 内真的调用 subagent。
def test_build_subagent_render_prompt_locks_forbidden_behaviors(tmp_path: Path) -> None:
    _, lineage_root = _build_signal_ready_confirmation_lineage(tmp_path)
    payload = build_data_ready_reflection_payload(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert payload is not None
    prompt = build_subagent_render_prompt(
        payload,
        output_html_path=lineage_root / "reports" / "data_ready_summary.subagent.html",
    )

    assert "Use ONLY the payload below as the source of truth." in prompt
    assert "Do not infer parquet metrics or statistics beyond the payload." in prompt
    assert "Do not hide, rewrite, or soften missing-evidence markers or question prompts." in prompt
    assert '"stage_id": "data_ready"' in prompt


def test_write_subagent_bundle_writes_payload_prompt_and_output_path(tmp_path: Path) -> None:
    _, lineage_root = _build_signal_ready_confirmation_lineage(tmp_path)
    payload = build_data_ready_reflection_payload(
        lineage_root=lineage_root,
        current_stage="signal_ready_confirmation_pending",
        current_route="time_series_signal",
    )

    assert payload is not None
    bundle = write_subagent_bundle(
        bundle_dir=tmp_path / "bundle",
        payload=payload,
        output_html_path=tmp_path / "reports" / "data_ready_summary.subagent.html",
    )

    assert bundle["bundle_dir"].exists()
    assert bundle["payload"].exists()
    assert bundle["prompt"].exists()
    assert bundle["output_path"].exists()


def test_export_stage_summary_html_script_writes_bundle_and_deterministic_html(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "export_stage_summary_html.py"
    outputs_root, lineage_root = _build_signal_ready_confirmation_lineage(tmp_path)

    result = run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "btc_leads_alts",
            "--renderer",
            "both",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    assert manifest["current_stage"] == "signal_ready_confirmation_pending"
    assert manifest["current_route"] == "time_series_signal"
    assert manifest["codex_time_dependency_only"] is True

    payload_path = Path(manifest["payload_path"])
    deterministic_path = Path(manifest["deterministic_html_path"])
    bundle_dir = Path(manifest["subagent_bundle_dir"])
    bundle_payload_path = Path(manifest["subagent_bundle_payload_path"])
    prompt_path = Path(manifest["subagent_prompt_path"])
    output_path_file = Path(manifest["subagent_output_path_file"])

    assert payload_path.exists()
    assert deterministic_path.exists()
    assert bundle_dir.exists()
    assert bundle_payload_path.exists()
    assert prompt_path.exists()
    assert output_path_file.exists()
    assert deterministic_path.parent == lineage_root / "reports"

    prompt = prompt_path.read_text(encoding="utf-8")
    html = deterministic_path.read_text(encoding="utf-8")
    assert "Data Coverage And Gaps" in html
    assert "QC / Anomaly Summary" in html
    assert "Artifact Directory And Key Files" in html
    assert "Codex-time orchestration dependency" not in html
    assert "Data Ready HTML Renderer Task" in prompt
