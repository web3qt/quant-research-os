from copy import deepcopy

from scripts.evaluate_classification import build_split_report, compare_split_reports


def test_compare_split_reports_matches_identical_payloads() -> None:
    baseline = build_split_report("test")
    current = build_split_report("test")

    diff = compare_split_reports(baseline, current)

    assert diff["matches"] is True
    assert diff["missing_ids"] == []
    assert diff["added_ids"] == []
    assert diff["changed_samples"] == {}


def test_compare_split_reports_flags_changed_prompt_hash() -> None:
    baseline = build_split_report("test")
    current = deepcopy(baseline)
    current["samples"][0]["prompt_sha256"] = "changed"

    diff = compare_split_reports(baseline, current)

    assert diff["matches"] is False
    assert diff["changed_samples"][current["samples"][0]["id"]]["prompt_sha256"] == {
        "baseline": baseline["samples"][0]["prompt_sha256"],
        "current": "changed",
    }
