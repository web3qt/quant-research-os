from scripts.build_anti_drift_gate_summary import build_gate_summary


def test_build_gate_summary_passes_clean_compare() -> None:
    summary = build_gate_summary(
        compare_result={
            "baseline_root": "baseline",
            "current_root": "current",
            "matches": True,
            "missing_files": [],
            "added_files": [],
            "changed_files": {},
        },
        report_path="reports/nightly.md",
        freshness_ok=True,
    )

    assert summary["status"] == "PASS"
    assert summary["failure_reasons"] == []
    assert summary["report_path"] == "reports/nightly.md"


def test_build_gate_summary_fails_on_drift_or_staleness() -> None:
    summary = build_gate_summary(
        compare_result={
            "baseline_root": "baseline",
            "current_root": "current",
            "matches": False,
            "missing_files": [],
            "added_files": ["new.json"],
            "changed_files": {"snapshot.json": {"baseline": {}, "current": {}}},
        },
        report_path=None,
        freshness_ok=False,
    )

    assert summary["status"] == "FAIL"
    assert summary["failure_reasons"] == ["semantic_drift_detected", "nightly_report_stale"]
    assert summary["changed_files"] == ["snapshot.json"]


def test_build_gate_summary_propagates_input_errors_without_masking_them() -> None:
    summary = build_gate_summary(
        compare_result={
            "baseline_root": "baseline",
            "current_root": "current",
            "matches": False,
            "input_errors": ["baseline_root_missing"],
            "missing_files": [],
            "added_files": [],
            "changed_files": {},
        },
        report_path=None,
        freshness_ok=True,
    )

    assert summary["status"] == "FAIL"
    assert summary["failure_reasons"] == ["baseline_root_missing"]
    assert summary["input_errors"] == ["baseline_root_missing"]
