from pathlib import Path


def test_install_docs_reference_supported_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/experience/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart, session_usage])

    assert "./setup --host codex --mode repo-local" in combined
    assert "./setup --host codex --mode user-global" in combined
    assert "qros-research-session" in combined
    assert "qros-research-session help" in combined
