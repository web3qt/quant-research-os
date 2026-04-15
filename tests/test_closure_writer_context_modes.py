from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.closure_models import build_review_payload
from runtime.tools.review_skillgen.closure_writer import write_closure_artifacts


def test_write_closure_artifacts_can_infer_context_from_cwd(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "signal_ready"
    nested_dir = stage_dir / "review_workspace"
    nested_dir.mkdir(parents=True)

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="signal_ready",
        final_verdict="PASS FOR RETRY",
        stage_status="RETRY",
    )

    write_closure_artifacts(payload, cwd=nested_dir)

    gate_payload = yaml.safe_load((stage_dir / "stage_gate_review.yaml").read_text(encoding="utf-8"))
    assert gate_payload["stage"] == "signal_ready"
    assert gate_payload["final_verdict"] == "PASS FOR RETRY"


def test_write_closure_artifacts_raises_clear_error_when_context_missing(tmp_path: Path) -> None:
    outside_dir = tmp_path / "scratch"
    outside_dir.mkdir(parents=True)

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    with pytest.raises(ValueError, match="Could not infer review context"):
        write_closure_artifacts(payload, cwd=outside_dir)
