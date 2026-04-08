from pathlib import Path


def test_install_docs_reference_supported_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/experience/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")
    codex_guide = Path("docs/README.codex.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart, session_usage, codex_guide])

    assert "git clone" in combined
    assert "~/.qros" in combined
    assert "~/.agents/skills" in combined
    assert "ln -s" in combined
    assert "git pull" in combined
    assert "./setup --host codex --mode user-global" in combined
    assert "pipx install qros" not in combined
    assert "uv tool install qros" not in combined
    assert "qros-research-session" in combined
    assert "qros-research-session help" in combined
    assert "~/.qros/bin/qros-session" in combined
    assert "~/.qros/bin/qros-review" in combined
    assert "~/.qros/bin/qros-verify" in combined
    assert "Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md" in combined
    assert "Restart Codex" in combined
    assert "Uninstalling" in combined


def test_install_docs_reference_stage_field_guide() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")
    session_usage = Path("docs/experience/qros-research-session-usage.md").read_text(encoding="utf-8")
    guide = Path("docs/experience/stage-freeze-group-field-guide.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, quickstart, session_usage])

    assert "stage-freeze-group-field-guide.md" in combined
    assert "qros-verification-tiers.md" in combined
    assert "research_intent" in guide
    assert "scope_contract" in guide
    assert "delivery_contract" in guide
    assert "| 字段 | 含义 | 为什么需要 | 不该怎么填 |" in guide
    assert "为什么需要" in guide
    assert "不该怎么填" in guide
    assert "param_identity" in guide
    assert "reuse_contract" in guide
    assert "best_h" in guide
    assert "selected_symbols" in guide
    assert "panel_primary_key" in guide
    assert "factor_id" in guide
    assert "search_governance_contract" in guide
    assert "portfolio_contract" in guide
    assert "stability_contract" in guide
