from pathlib import Path


def test_project_bootstrap_files_exist() -> None:
    assert Path("pyproject.toml").exists()
    assert Path("tools/review_skillgen/__init__.py").exists()
    assert Path("tools/review_skillgen/closure_models.py").exists()
    assert Path("tools/review_skillgen/context_inference.py").exists()
    assert Path("tools/review_skillgen/closure_writer.py").exists()
    assert Path("tools/review_skillgen/review_findings.py").exists()
    assert Path("tools/review_skillgen/review_engine.py").exists()
    assert Path("scripts/run_stage_review.py").exists()
    assert Path("scripts/scaffold_idea_intake.py").exists()
    assert Path("scripts/build_mandate_from_intake.py").exists()
    assert Path("tools/idea_runtime.py").exists()
    assert Path("docs/intake-sop/qualification_scorecard_schema.yaml").exists()
    assert Path("docs/intake-sop/idea_gate_decision_schema.yaml").exists()
    assert Path(".agents/skills/qros-idea-intake-author/SKILL.md").exists()
    assert Path(".agents/skills/qros-mandate-author/SKILL.md").exists()


def test_usage_doc_exists() -> None:
    assert Path("docs/experience/codex-stage-review-skill-usage.md").exists()
    assert Path("docs/experience/closure-artifact-writer-usage.md").exists()
    assert Path("docs/experience/idea-intake-to-mandate-flow.md").exists()
