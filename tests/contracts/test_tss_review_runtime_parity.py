from pathlib import Path

import yaml

from runtime.tools.stage_evaluator import STAGE_EVALUATOR_SPEC_ALIASES, STAGE_EVALUATOR_SPECS


ROOT = Path(__file__).resolve().parents[2]
GATES_PATH = ROOT / "contracts" / "stages" / "workflow_stage_gates.yaml"
CHECKLIST_PATH = ROOT / "contracts" / "review" / "review_checklist_master.yaml"


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_tss_reviewable_stages_have_review_checklist_and_evaluator_specs() -> None:
    gates = _load_yaml(GATES_PATH)
    checklist = _load_yaml(CHECKLIST_PATH)

    tss_stages = [
        stage_id
        for stage_id in gates["stages"]
        if stage_id.startswith("tss_") and gates["stages"][stage_id].get("required_outputs")
    ]

    missing_checklists = [stage_id for stage_id in tss_stages if stage_id not in checklist["stages"]]
    missing_aliases = [stage_id for stage_id in tss_stages if stage_id not in STAGE_EVALUATOR_SPEC_ALIASES]
    missing_specs = [
        stage_id
        for stage_id in tss_stages
        if STAGE_EVALUATOR_SPEC_ALIASES.get(stage_id) not in STAGE_EVALUATOR_SPECS
    ]
    mismatched_outputs = {
        stage_id: {
            "gate": gates["stages"][stage_id]["required_outputs"],
            "evaluator": list(STAGE_EVALUATOR_SPECS[STAGE_EVALUATOR_SPEC_ALIASES[stage_id]].required_outputs),
        }
        for stage_id in tss_stages
        if stage_id in STAGE_EVALUATOR_SPEC_ALIASES
        and STAGE_EVALUATOR_SPEC_ALIASES[stage_id] in STAGE_EVALUATOR_SPECS
        and list(STAGE_EVALUATOR_SPECS[STAGE_EVALUATOR_SPEC_ALIASES[stage_id]].required_outputs)
        != list(gates["stages"][stage_id]["required_outputs"])
    }

    assert missing_checklists == []
    assert missing_aliases == []
    assert missing_specs == []
    assert mismatched_outputs == {}
