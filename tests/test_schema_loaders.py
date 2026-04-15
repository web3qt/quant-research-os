from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema


def test_gate_schema_contains_first_wave_stages() -> None:
    gates = load_gate_schema("contracts/stages/workflow_stage_gates.yaml")
    assert "mandate" in gates["stages"]
    assert "data_ready" in gates["stages"]
    assert "signal_ready" in gates["stages"]
    assert set(gates["review_closure_vocabulary"]) == {
        "PASS",
        "CONDITIONAL PASS",
        "PASS FOR RETRY",
        "RETRY",
        "NO-GO",
        "GO",
        "CHILD LINEAGE",
    }
    assert set(gates["review_passing_verdicts"]) == {"PASS", "CONDITIONAL PASS"}
    assert set(gates["review_retry_verdicts"]) == {"PASS FOR RETRY", "RETRY"}


def test_checklist_schema_contains_first_wave_stages() -> None:
    checklist = load_checklist_schema("contracts/review/review_checklist_master.yaml")
    assert "mandate" in checklist["stages"]
    assert "data_ready" in checklist["stages"]
    assert "signal_ready" in checklist["stages"]
    assert set(checklist["verdict_guidance"]) == {
        "PASS",
        "CONDITIONAL PASS",
        "PASS FOR RETRY",
        "RETRY",
        "NO-GO",
        "CHILD LINEAGE",
    }


def test_gate_schema_enforces_required_stage_contract_keys() -> None:
    gates = load_gate_schema("contracts/stages/workflow_stage_gates.yaml")
    required_stage_keys = {
        "stage_id",
        "stage_name",
        "required_inputs",
        "required_outputs",
        "formal_gate",
        "verdict_rules",
        "rollback_rules",
        "downstream_permissions",
    }
    allowed_downstream_key_sets = {
        (
            "frozen_outputs_consumable_by_next_stage",
            "may_advance_to",
            "next_stage_must_not_consume",
            "precondition_before_advance",
        ),
        (
            "frozen_outputs_consumable_by_next_stage",
            "may_advance_to",
            "next_stage_must_not_reestimate",
        ),
    }

    for stage_key, stage in gates["stages"].items():
        assert required_stage_keys.issubset(stage), stage_key
        assert stage["stage_id"] == stage_key
        assert isinstance(stage["required_outputs"], list), stage_key
        assert isinstance(stage["required_inputs"], list), stage_key
        downstream_permissions = stage["downstream_permissions"]
        assert tuple(sorted(downstream_permissions)) in allowed_downstream_key_sets, stage_key
        for key in downstream_permissions:
            assert isinstance(downstream_permissions[key], list), f"{stage_key}.{key}"


def test_checklist_schema_enforces_required_stage_contract_keys() -> None:
    checklist = load_checklist_schema("contracts/review/review_checklist_master.yaml")

    for stage_key, stage in checklist["stages"].items():
        assert stage.get("stage_name"), stage_key
        assert isinstance(stage.get("documents_to_read", []), list), stage_key
        assert isinstance(stage.get("checks", []), list), stage_key
        assert stage["checks"], stage_key
