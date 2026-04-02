import json

from scripts.evaluate_classification import FAILURE_CLASSES, build_split_report


def test_build_split_report_returns_regression_friendly_structure() -> None:
    payload = build_split_report("train")

    assert payload["split"] == "train"
    assert payload["sample_count"] == len(payload["samples"])
    assert payload["sample_count"] > 0
    assert payload["class_counts"]
    assert sorted(payload["class_counts"]) == sorted(FAILURE_CLASSES)

    first = payload["samples"][0]
    assert first["id"]
    assert first["ground_truth"] in FAILURE_CLASSES
    assert first["severity"] in {"FAIL-HARD", "FAIL-SOFT", "PASS_WITH_RESTRICTIONS", "UNKNOWN"}
    assert first["prompt"]
    assert first["prompt_sha256"]


def test_build_split_report_is_json_serializable() -> None:
    encoded = json.dumps({"train": build_split_report("test")}, ensure_ascii=False)
    decoded = json.loads(encoded)

    assert decoded["train"]["split"] == "test"
    assert decoded["train"]["sample_count"] == len(decoded["train"]["samples"])
