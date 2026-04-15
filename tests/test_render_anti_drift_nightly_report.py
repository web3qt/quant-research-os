from runtime.scripts.render_anti_drift_nightly_report import render_markdown_report
from pathlib import Path
from subprocess import run
import sys


def test_render_markdown_report_for_clean_compare() -> None:
    report = render_markdown_report(
        {
            "baseline_root": "baseline",
            "current_root": "current",
            "matches": True,
            "missing_files": [],
            "added_files": [],
            "changed_files": {},
        }
    )

    assert "# Anti-Drift Nightly Report" in report
    assert "No semantic drift detected against the blessed baseline." in report


def test_render_markdown_report_lists_changed_fields() -> None:
    report = render_markdown_report(
        {
            "baseline_root": "baseline",
            "current_root": "current",
            "matches": False,
            "missing_files": ["missing.json"],
            "added_files": ["added.json"],
            "changed_files": {
                "snapshot.json": {
                    "baseline": {"route_skill": "qros-mandate-review"},
                    "current": {"route_skill": "qros-data-ready-review"},
                }
            },
        }
    )

    assert "## Missing files" in report
    assert "`missing.json`" in report
    assert "## Added files" in report
    assert "`added.json`" in report
    assert "### `snapshot.json`" in report
    assert "`route_skill`" in report


def test_render_anti_drift_nightly_report_cli_runs_from_repo_root(tmp_path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "runtime" / "scripts" / "render_anti_drift_nightly_report.py"
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    output = tmp_path / "nightly.md"
    baseline.mkdir()
    current.mkdir()
    (baseline / "snapshot.json").write_text('{"fixture_id":"demo","route_skill":"qros-mandate-review"}\n', encoding="utf-8")
    (current / "snapshot.json").write_text('{"fixture_id":"demo","route_skill":"qros-mandate-review"}\n', encoding="utf-8")

    result = run(
        [sys.executable, str(script_path), "--baseline", str(baseline), "--current", str(current), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_root,
    )

    assert result.returncode == 0
    assert output.exists()
    assert "No semantic drift detected against the blessed baseline." in output.read_text(encoding="utf-8")
