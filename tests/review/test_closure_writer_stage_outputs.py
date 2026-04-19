from pathlib import Path

import yaml

from runtime.tools.review_skillgen.closure_models import build_review_payload
from runtime.tools.review_skillgen.closure_writer import write_closure_artifacts


def test_write_closure_artifacts_creates_stage_files(tmp_path: Path) -> None:
    stage_dir = tmp_path / "outputs" / "topic_a" / "mandate"
    stage_dir.mkdir(parents=True)

    payload = build_review_payload(
        lineage_id="topic_a",
        stage="mandate",
        final_verdict="PASS",
        stage_status="PASS",
        reviewer_identity="codex",
        rollback_stage="mandate",
        allowed_modifications=["clarify wording"],
        downstream_permissions=["data_ready"],
        contract_source="contracts/stages/workflow_stage_gates.yaml",
        checklist_source="contracts/review/review_checklist_master.yaml",
        required_outputs_checked={"expected": ["mandate.md"], "missing": []},
        evidence_summary={"recommended_gate_doc": "mandate.md"},
    )

    write_closure_artifacts(
        payload,
        explicit_context={"stage_dir": stage_dir, "lineage_root": stage_dir.parent},
    )

    latest_review_pack = stage_dir / "review" / "closure" / "latest_review_pack.yaml"
    stage_gate_review = stage_dir / "review" / "closure" / "stage_gate_review.yaml"
    certificate = stage_dir / "review" / "closure" / "stage_completion_certificate.yaml"

    assert latest_review_pack.exists()
    assert stage_gate_review.exists()
    assert certificate.exists()

    latest_payload = yaml.safe_load(latest_review_pack.read_text(encoding="utf-8"))
    assert latest_payload["lineage_id"] == "topic_a"
    assert latest_payload["stage"] == "mandate"
    assert latest_payload["final_verdict"] == "PASS"

    gate_payload = yaml.safe_load(stage_gate_review.read_text(encoding="utf-8"))
    assert gate_payload["stage_status"] == "PASS"
    assert gate_payload["rollback_stage"] == "mandate"
    assert gate_payload["reviewer_identity"] == "codex"
    assert gate_payload["contract_source"] == "contracts/stages/workflow_stage_gates.yaml"

    certificate_payload = yaml.safe_load(certificate.read_text(encoding="utf-8"))
    assert certificate_payload["allowed_modifications"] == ["clarify wording"]
    assert certificate_payload["downstream_permissions"] == ["data_ready"]
    assert certificate_payload["required_outputs_checked"] == {"expected": ["mandate.md"], "missing": []}
    assert certificate_payload["evidence_summary"] == {"recommended_gate_doc": "mandate.md"}
