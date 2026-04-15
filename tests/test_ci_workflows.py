from pathlib import Path

import yaml


def test_anti_drift_workflow_exists_and_references_gate_scripts() -> None:
    workflow_path = Path(".github/workflows/anti-drift.yml")
    assert workflow_path.exists()

    payload = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert "jobs" in payload
    assert "pr-gate" in payload["jobs"]
    assert "nightly-release-gate" in payload["jobs"]

    text = workflow_path.read_text(encoding="utf-8")
    assert "runtime/scripts/export_anti_drift_snapshots.py" in text
    assert "runtime/scripts/build_anti_drift_gate_summary.py" in text
    assert "runtime/scripts/build_anti_drift_release_artifact.py" in text
    assert "python -m pip install PyYAML pytest" in text
