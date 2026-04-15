from runtime.tools.review_skillgen.loaders import load_checklist_schema, load_gate_schema
from runtime.tools.review_skillgen.render import render_stage_skill


def test_render_stage_skill_includes_stage_specific_contract() -> None:
    gates = load_gate_schema("contracts/stages/workflow_stage_gates.yaml")
    checklist = load_checklist_schema("contracts/review/review_checklist_master.yaml")

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
    assert "默认 rollback stage：mandate" in text
    assert "仅审计项" in text
    assert "专题样板写法是否足够清楚" in text
    assert "review_findings.yaml" in text
    assert "./.qros/bin/qros-review" in text
