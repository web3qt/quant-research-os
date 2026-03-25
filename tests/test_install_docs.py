from pathlib import Path


def test_install_docs_reference_supported_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/experience/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")
    idea_flow = Path("docs/experience/idea-intake-to-mandate-flow.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart, idea_flow])

    assert "./setup --host codex --mode repo-local" in combined
    assert "./setup --host codex --mode user-global" in combined
    assert "python scripts/scaffold_idea_intake.py" in combined
    assert "python scripts/build_mandate_from_intake.py" in combined
    assert "python scripts/run_stage_review.py" in combined
