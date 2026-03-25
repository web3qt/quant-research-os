from tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from tools.review_skillgen.render import render_stage_skill


def test_render_stage_skill_includes_stage_specific_contract() -> None:
    gates = load_gate_schema("docs/gates/workflow_stage_gates.yaml")
    checklist = load_checklist_schema("docs/check-sop/review_checklist_master.yaml")

    text = render_stage_skill(
        stage_key="mandate",
        skill_name="qros-mandate-review",
        gate_schema=gates,
        checklist_schema=checklist,
    )

    assert "Mandate" in text
    assert "formal gate" in text.lower()
    assert "latest_review_pack.yaml" in text
    assert "time_split.json" in text
    assert "PASS FOR RETRY" in text
    assert "Default rollback stage: mandate" in text
    assert "Audit-only items" in text
    assert "专题样板写法是否足够清楚" in text
