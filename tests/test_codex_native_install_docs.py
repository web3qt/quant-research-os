from pathlib import Path


def test_codex_native_install_docs_reference_clone_and_symlink() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/experience/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/experience/quickstart-codex.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart])

    assert "git clone" in combined
    assert "~/.qros" in combined
    assert "~/.agents/skills" in combined
    assert "ln -s" in combined
    assert "git pull" in combined

