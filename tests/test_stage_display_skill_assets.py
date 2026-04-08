from pathlib import Path


SKILL_PATHS = (
    Path("skills/qros-stage-display/SKILL.md"),
    Path(".agents/skills/qros-stage-display/SKILL.md"),
)

EXPECTED_SUPPORTED_STAGE_IDS = (
    "mandate",
    "data_ready",
    "signal_ready",
    "train_freeze",
    "test_evidence",
    "backtest_ready",
    "holdout_validation",
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)

REQUIRED_SUPPORT_LIST_SUBSTRINGS = (
    "## v1 Supported Stage List",
    *(f"`{stage_id}`" for stage_id in EXPECTED_SUPPORTED_STAGE_IDS),
    "v1 formally supports the current reviewable mainline and CSF stages.",
)

FORBIDDEN_STAGE_CLAIMS = (
    "v1 formally supports **only** `mandate` and `csf_data_ready`.",
    "No other stage is supported in v1.",
)


def test_stage_display_skill_assets_exist_in_both_trees() -> None:
    for path in SKILL_PATHS:
        assert path.exists(), f"missing skill asset: {path}"


def test_stage_display_skill_v1_support_list_contains_current_reviewable_stages() -> None:
    for path in SKILL_PATHS:
        text = path.read_text(encoding="utf-8")
        for needle in REQUIRED_SUPPORT_LIST_SUBSTRINGS:
            assert needle in text, f"{needle!r} missing in {path}"
        for forbidden in FORBIDDEN_STAGE_CLAIMS:
            assert forbidden not in text, f"unexpected stale support claim {forbidden!r} in {path}"


def test_stage_display_skill_text_is_aligned_between_repo_and_agent_trees() -> None:
    repo_text = SKILL_PATHS[0].read_text(encoding="utf-8")
    agent_text = SKILL_PATHS[1].read_text(encoding="utf-8")
    assert repo_text == agent_text
