import json
from pathlib import Path


def test_stage_evaluator_schema_exists_and_exposes_unified_required_fields() -> None:
    schema_path = Path("contracts/stages/stage_evaluator.schema.json")
    assert schema_path.exists()

    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    assert payload["type"] == "object"
    required = set(payload["required"])
    assert {
        "schema_version",
        "lineage_id",
        "stage",
        "stage_dir",
        "pass",
        "can_progress",
        "status",
        "reason",
        "blocking_findings",
        "warnings",
        "required_outputs_checked",
        "review_summary",
        "evaluated_at",
    } <= required

    properties = payload["properties"]
    assert properties["pass"]["type"] == "boolean"
    assert properties["can_progress"]["type"] == "boolean"
    assert properties["blocking_findings"]["type"] == "array"
    assert properties["warnings"]["type"] == "array"
    assert properties["required_outputs_checked"]["type"] == "object"
    assert properties["review_summary"]["type"] == "object"
