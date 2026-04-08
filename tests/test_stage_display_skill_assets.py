from pathlib import Path

from tests.skill_test_utils import skill_bundle_dir

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

def test_stage_display_skill_bundle_exists() -> None:
    bundle_dir = skill_bundle_dir("qros-stage-display")
    assert (bundle_dir / "SKILL.md").exists(), bundle_dir
    assert (bundle_dir / "agents" / "openai.yaml").exists(), bundle_dir


def test_stage_display_skill_v1_support_list_contains_current_reviewable_stages() -> None:
    path = skill_bundle_dir("qros-stage-display") / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_SUPPORT_LIST_SUBSTRINGS:
        assert needle in text, f"{needle!r} missing in {path}"
    for forbidden in FORBIDDEN_STAGE_CLAIMS:
        assert forbidden not in text, f"unexpected stale support claim {forbidden!r} in {path}"


def test_stage_display_skill_openai_metadata_keeps_name_alignment() -> None:
    bundle_dir = skill_bundle_dir("qros-stage-display")
    metadata = (bundle_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "name: qros-stage-display" in metadata
