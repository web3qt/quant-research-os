from pathlib import Path


def test_tests_tree_is_grouped_by_subject() -> None:
    root = Path("tests")
    expected_dirs = (
        "anti_drift",
        "bootstrap",
        "contracts",
        "docs",
        "helpers",
        "review",
        "runtime",
        "session",
        "skills",
    )

    for rel in expected_dirs:
        assert (root / rel).is_dir(), f"missing grouped tests directory: tests/{rel}"


def test_tests_tree_has_navigation_readmes_and_representative_entries() -> None:
    assert Path("tests/README.md").exists()

    expected_paths = (
        "tests/contracts/README.md",
        "tests/contracts/test_verification_tiers.py",
        "tests/bootstrap/README.md",
        "tests/bootstrap/test_project_bootstrap.py",
        "tests/docs/README.md",
        "tests/docs/test_install_docs.py",
        "tests/review/README.md",
        "tests/review/test_review_engine.py",
        "tests/runtime/README.md",
        "tests/runtime/test_train_runtime.py",
        "tests/session/README.md",
        "tests/session/test_research_session_runtime.py",
        "tests/skills/README.md",
        "tests/skills/test_skill_tree.py",
    )

    for rel in expected_paths:
        assert Path(rel).exists(), f"missing expected grouped test artifact: {rel}"
