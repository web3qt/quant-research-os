import json
from pathlib import Path

from scripts.anti_drift_baseline import compare_json_roots, promote_json_roots


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_compare_json_roots_reports_match_for_identical_payloads(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    _write_json(baseline / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-mandate-review"})
    _write_json(current / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-mandate-review"})

    result = compare_json_roots(baseline, current)

    assert result["matches"] is True
    assert result["missing_files"] == []
    assert result["added_files"] == []
    assert result["changed_files"] == {}


def test_compare_json_roots_reports_changed_payloads(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    _write_json(baseline / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-mandate-review"})
    _write_json(current / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-data-ready-review"})

    result = compare_json_roots(baseline, current)

    assert result["matches"] is False
    assert "snapshot.json" in result["changed_files"]
    assert result["changed_files"]["snapshot.json"]["baseline"]["route_skill"] == "qros-mandate-review"
    assert result["changed_files"]["snapshot.json"]["current"]["route_skill"] == "qros-data-ready-review"


def test_promote_json_roots_copies_payloads_and_writes_manifest(tmp_path: Path) -> None:
    current = tmp_path / "current"
    baseline = tmp_path / "baseline"
    _write_json(current / "nested" / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-mandate-review"})

    manifest = promote_json_roots(
        current,
        baseline,
        label="anti-drift-v1",
        source_note="promote test fixtures",
    )

    assert (baseline / "nested" / "snapshot.json").exists()
    assert (baseline / "baseline_manifest.json").exists()
    assert manifest["label"] == "anti-drift-v1"
    assert manifest["source_note"] == "promote test fixtures"
    assert manifest["files"] == ["nested/snapshot.json"]


def test_compare_json_roots_ignores_baseline_manifest_metadata(tmp_path: Path) -> None:
    current = tmp_path / "current"
    baseline = tmp_path / "baseline"
    _write_json(current / "snapshot.json", {"fixture_id": "a", "route_skill": "qros-mandate-review"})
    promote_json_roots(current, baseline, label="anti-drift-v1", source_note="test")

    result = compare_json_roots(baseline, current)

    assert result["matches"] is True
    assert result["changed_files"] == {}


def test_compare_json_roots_fails_when_roots_are_missing(tmp_path: Path) -> None:
    result = compare_json_roots(tmp_path / "missing-baseline", tmp_path / "missing-current")

    assert result["matches"] is False
    assert result["input_errors"] == ["baseline_root_missing", "current_root_missing"]


def test_compare_json_roots_fails_when_roots_are_empty(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    current = tmp_path / "current"
    baseline.mkdir()
    current.mkdir()

    result = compare_json_roots(baseline, current)

    assert result["matches"] is False
    assert result["input_errors"] == ["baseline_root_empty", "current_root_empty"]
