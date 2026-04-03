from pathlib import Path

import yaml


def test_lineage_local_program_contract_is_documented_in_entry_docs() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    readme_en = Path("README_EN.md").read_text(encoding="utf-8")
    usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")
    workflow = Path("docs/main-flow-sop/research_workflow_sop.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, readme_en, usage, workflow])

    assert "outputs/<lineage_id>/program/" in combined
    assert "stage_program.yaml" in combined
    assert "program_execution_manifest.json" in combined
    assert "freeze approval -> lineage-local program -> artifact build -> review closure" in combined
    assert "framework-side shared builder" in combined


def test_lineage_local_program_gate_truth_is_present_in_gate_yaml() -> None:
    gates = yaml.safe_load(Path("docs/gates/workflow_stage_gates.yaml").read_text(encoding="utf-8"))

    global_rule_ids = {rule["id"] for rule in gates["global_rules"]}
    assert "lineage_local_program_required_for_executable_stages" in global_rule_ids
    assert "no_shared_builder_completion_path" in global_rule_ids

    contract = gates["lineage_program_contract"]
    assert contract["invariant"] == "freeze approval -> lineage-local program -> artifact build -> review closure"
    assert contract["generated_provenance_file"] == "<stage_artifact_dir>/program_execution_manifest.json"
    assert contract["shared_helper_root"] == "outputs/<lineage_id>/program/common/"

    stage_program_keys = contract["stage_program_keys"]
    assert stage_program_keys["mandate"]["program_dir"] == "outputs/<lineage_id>/program/mandate/"
    assert stage_program_keys["data_ready"]["program_dir"] == "outputs/<lineage_id>/program/time_series/data_ready/"
    assert stage_program_keys["train_calibration"]["program_dir"] == "outputs/<lineage_id>/program/time_series/train_freeze/"
    assert (
        stage_program_keys["csf_holdout_validation"]["program_dir"]
        == "outputs/<lineage_id>/program/cross_sectional_factor/holdout_validation/"
    )

    assert "awaiting_stage_program" in contract["status_contract"]["stage_status"]
    assert "STAGE_PROGRAM_MISSING" in contract["status_contract"]["blocking_reason_code"]


def test_session_usage_documents_program_gate_status_fields() -> None:
    usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "awaiting_stage_program" in usage
    assert "STAGE_PROGRAM_MISSING" in usage
    assert "required_program_dir" in usage
    assert "required_program_entrypoint" in usage
    assert "program_contract_status" in usage
    assert "provenance_status" in usage
