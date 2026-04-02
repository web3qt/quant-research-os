from scripts.render_anti_drift_nightly_report import render_markdown_report


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
