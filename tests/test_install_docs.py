from pathlib import Path


def test_install_docs_reference_supported_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/experience/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")
    codex_guide = Path("docs/README.codex.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart, session_usage, codex_guide])

    assert "git clone" in combined
    assert "~/.codex/qros" in combined
    assert "~/.agents/skills" in combined
    assert "ln -s" in combined
    assert "git pull" in combined
    assert "pipx install qros" not in combined
    assert "uv tool install qros" not in combined
    assert "qros-research-session" in combined
    assert "qros-research-session help" in combined
    assert "~/.codex/qros/bin/qros-session" in combined
    assert "~/.codex/qros/bin/qros-review" in combined
    assert "Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md" in combined
    assert "Restart Codex" in combined
    assert "Uninstalling" in combined
