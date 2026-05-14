from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
import sys

from tests.helpers.repo_paths import REPO_ROOT


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_passed_mandate(outputs_root: Path, lineage_id: str) -> None:
    stage_dir = outputs_root / lineage_id / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    for name in (
        "mandate.md",
        "research_scope.md",
        "artifact_catalog.md",
        "field_dictionary.md",
    ):
        _write(formal_dir / name, "ok\n")
    _write(
        formal_dir / "research_route.yaml",
        "\n".join(
            [
                "research_route: cross_sectional_factor",
                "factor_role: standalone_alpha",
                "factor_structure: single_factor",
                "portfolio_expression: long_short_rank_based",
                "neutralization_policy: market_beta_neutral",
                "",
            ]
        ),
    )
    _write(formal_dir / "time_split.json", "{}\n")
    _write(formal_dir / "parameter_grid.yaml", "parameters: []\n")
    _write(formal_dir / "run_config.toml", "version = 1\n")
    _write(formal_dir / "program_execution_manifest.json", "{}\n")
    for name in (
        "latest_review_pack.yaml",
        "stage_completion_certificate.yaml",
        "stage_gate_review.yaml",
    ):
        _write(stage_dir / "review" / "closure" / name, "final_verdict: PASS\nstage_status: PASS\n")


def test_run_resume_script_reports_direct_handoff_from_disk_state(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    _prepare_passed_mandate(outputs_root, "topic_a")

    result = run(
        [
            sys.executable,
            str(REPO_ROOT / "runtime" / "scripts" / "run_resume.py"),
            "--outputs-root",
            str(outputs_root),
            "--lineage-id",
            "topic_a",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["current_stage"] == "mandate_next_stage_confirmation_pending"
    assert payload["recommended_skill"] == "qros-research-session"
    assert payload["handoff_hint"] == "Continue with qros-research-session."
    assert payload["next_action"] == "Continue with qros-research-session."
    assert "clear_required" not in payload
    assert "clear_instruction" not in payload
