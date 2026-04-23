from pathlib import Path


def test_codex_native_install_docs_reference_clone_and_symlink() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    installation = Path("docs/guides/installation.md").read_text(encoding="utf-8")
    quickstart = Path("docs/guides/quickstart-codex.md").read_text(encoding="utf-8")

    combined = "\n".join([readme, installation, quickstart])

    assert "./.qros" in combined
    assert "~/.codex/skills" in combined
    assert "Manual Installation" not in combined
    assert "Manual fallback" not in combined
    assert "手动安装" not in combined
