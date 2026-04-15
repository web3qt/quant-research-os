from pathlib import Path


def test_real_directory_agents_files_exist() -> None:
    assert Path("AGENTS.md").exists()
    assert Path("contracts/AGENTS.md").exists()
    assert Path("skills/AGENTS.md").exists()
    assert Path("runtime/AGENTS.md").exists()
    assert Path("docs/AGENTS.md").exists()
    assert Path("tests/AGENTS.md").exists()


def test_root_agents_declares_real_governance_entrypoints() -> None:
    content = Path("AGENTS.md").read_text(encoding="utf-8")

    assert "contracts/AGENTS.md" in content
    assert "skills/AGENTS.md" in content
    assert "runtime/AGENTS.md" in content
    assert "docs/AGENTS.md" in content
    assert "tests/AGENTS.md" in content
    assert "instruction 分层示例" in content
    assert "不是主仓真实治理面" in content
    assert "runtime/tools/" in content
    assert "runtime/scripts/" in content
    assert "runtime/bin/" in content
    assert "python -m pytest tests/test_agents_layout.py tests/test_project_bootstrap.py tests/test_install_docs.py" in content
    assert "python runtime/scripts/run_verification_tier.py --tier smoke" in content
    assert "python runtime/scripts/run_verification_tier.py --tier full-smoke" in content
    assert "docs/guides/qros-verification-tiers.md" in content
    assert "runtime/scripts/run_verification_tier.py" in content


def test_docs_readme_marks_harness_as_example_only() -> None:
    content = Path("docs/README.md").read_text(encoding="utf-8")

    assert "示例子树，不是主仓真实治理面" in content
    assert "../contracts/AGENTS.md" in content
    assert "../skills/AGENTS.md" in content
    assert "../runtime/AGENTS.md" in content
    assert "AGENTS.md" in content
    assert "../tests/AGENTS.md" in content
