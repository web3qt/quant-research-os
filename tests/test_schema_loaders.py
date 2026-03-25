from tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema


def test_gate_schema_contains_first_wave_stages() -> None:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    assert "mandate" in gates["stages"]
    assert "data_ready" in gates["stages"]
    assert "signal_ready" in gates["stages"]


def test_checklist_schema_contains_first_wave_stages() -> None:
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")
    assert "mandate" in checklist["stages"]
    assert "data_ready" in checklist["stages"]
    assert "signal_ready" in checklist["stages"]
