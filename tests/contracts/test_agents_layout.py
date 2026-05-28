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
    assert "instruction 分层示例" not in content
    assert "不是主仓真实治理面" not in content
    assert "runtime/tools/" in content
    assert "runtime/scripts/" in content
    assert "runtime/bin/" in content
    assert "harness/" not in content
    assert (
        "python -m pytest tests/contracts/test_agents_layout.py "
        "tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py" in content
    )
    assert "python runtime/scripts/run_verification_tier.py --tier smoke" in content
    assert "python runtime/scripts/run_verification_tier.py --tier full-smoke" in content
    assert "docs/guides/qros-verification-tiers.md" in content
    assert "runtime/scripts/run_verification_tier.py" in content
    assert "## References" in content
    assert "docs/guides/qros-research-session-usage.md" in content
    assert "docs/guides/qros-review-constraint-map.md" in content
    assert "docs/guides/stage-freeze-group-field-guide.md" in content
    assert "docs/guides/installation.md" in content


def test_research_repo_agents_template_locks_consumer_repo_boundaries() -> None:
    content = Path("templates/research-repo/AGENTS.md.tmpl").read_text(encoding="utf-8")

    assert "QROS Research Repo Agent Contract" in content
    assert "active research repo" in content
    assert "不是 QROS 框架仓" in content
    assert "outputs/<lineage_id>/" in content
    assert "$qros-research-session" in content
    assert "$qros-progress" in content
    assert "$qros-update" in content
    assert "./.qros/bin/qros-*" in content
    assert "placeholder" in content
    assert "failure handling" in content
    assert "review closure" in content


def test_removed_harness_tree_is_not_part_of_active_docs() -> None:
    content = Path("docs/README.md").read_text(encoding="utf-8")

    assert not Path("harness").exists()
    assert "harness/" not in content
    assert "../contracts/AGENTS.md" in content
    assert "../skills/AGENTS.md" in content
    assert "../runtime/AGENTS.md" in content
    assert "AGENTS.md" in content
    assert "../tests/AGENTS.md" in content
