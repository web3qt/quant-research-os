from pathlib import Path

import yaml

from runtime.tools.review_skillgen.closure_models import build_review_payload
from runtime.tools.review_skillgen.closure_writer import write_closure_artifacts


def test_write_closure_artifacts_mirrors_latest_review_pack_to_lineage_root(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
    )

    write_closure_artifacts(
        payload,
        explicit_context={"stage_dir": stage_dir, "lineage_root": stage_dir.parent},
    )

    lineage_latest = stage_dir.parent / "latest_review_pack.yaml"
    assert lineage_latest.exists()

    mirrored_payload = yaml.safe_load(lineage_latest.read_text(encoding="utf-8"))
    assert mirrored_payload["lineage_id"] == "topic_a"
    assert mirrored_payload["stage"] == "mandate"
    assert mirrored_payload["final_verdict"] == "PASS"
