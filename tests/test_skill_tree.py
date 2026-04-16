from pathlib import Path

from tests.skill_test_utils import skill_bundle_dir, skill_path


def test_public_skill_tree_exists() -> None:
    assert Path("skills").exists()
    assert skill_path("qros-stage-display").exists()
    assert skill_path("qros-research-session").exists()
    assert skill_path("qros-update").exists()
    assert skill_path("qros-mandate-review").exists()
    assert skill_path("qros-data-ready-review").exists()
    assert skill_path("qros-signal-ready-review").exists()
    assert skill_path("qros-train-freeze-review").exists()
    assert skill_path("qros-test-evidence-review").exists()
    assert skill_path("qros-backtest-ready-review").exists()
    assert skill_path("qros-holdout-validation-review").exists()


def test_public_skill_tree_is_grouped_by_stage_family() -> None:
    assert skill_bundle_dir("qros-stage-display").parent == Path("skills/core")
    assert skill_bundle_dir("qros-research-session").parent == Path("skills/core")
    assert skill_bundle_dir("qros-update").parent == Path("skills/core")
    assert skill_bundle_dir("qros-mandate-review").parent == Path("skills/mandate")
    assert skill_bundle_dir("qros-data-ready-review").parent == Path("skills/data_ready")
    assert skill_bundle_dir("qros-csf-data-ready-review").parent == Path("skills/csf_data_ready")
    assert skill_bundle_dir("qros-stage-failure-handler").parent == Path("skills/failure_handling")


def test_codex_install_doc_exists() -> None:
    assert Path(".codex/INSTALL.md").exists()
