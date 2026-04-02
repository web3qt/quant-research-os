import json

from scripts.export_anti_drift_snapshots import main


def test_export_anti_drift_snapshots_writes_expected_files(tmp_path, monkeypatch) -> None:
    output_dir = tmp_path / "snapshots"
    monkeypatch.setattr("sys.argv", ["export_anti_drift_snapshots.py", "--output-dir", str(output_dir)])

    rc = main()

    assert rc == 0
    written = sorted(path.name for path in output_dir.glob("*.json"))
    assert "idea_intake_confirmation_snapshot.json" in written
    assert "signal_ready_confirmation_snapshot.json" in written

    payload = json.loads((output_dir / "signal_ready_confirmation_snapshot.json").read_text(encoding="utf-8"))
    assert payload["fixture_id"] == "signal-ready-confirmation"
    assert payload["stage_id"] == "signal_ready"
