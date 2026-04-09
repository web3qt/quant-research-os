from tests.skill_test_utils import skill_bundle_dir


EXPECTED_STAGES = (
    "mandate",
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)


def _skill_text() -> str:
    return (skill_bundle_dir("qros-stage-display") / "SKILL.md").read_text(encoding="utf-8")


def test_stage_display_guidance_skill_exists_with_metadata() -> None:
    bundle_dir = skill_bundle_dir("qros-stage-display")
    assert (bundle_dir / "SKILL.md").exists()
    assert (bundle_dir / "agents" / "openai.yaml").exists()


def test_stage_display_guidance_skill_is_user_triggered_and_not_orchestration_owned() -> None:
    text = _skill_text()
    assert "只在用户**明确提出**类似请求时使用" in text
    assert "**不是** stage orchestration 的一部分" in text
    assert "**不是** mandatory gate" in text
    assert "mandatory gate" in text
    assert "自动在 review 结束后触发" in text
    assert "`*_display_pending`" in text
    assert "runtime HTML renderer" in text
    assert "data acquisition subsystem" in text


def test_stage_display_guidance_skill_covers_exact_v1_scope() -> None:
    text = _skill_text()
    for stage in EXPECTED_STAGES:
        assert f"`{stage}`" in text
    assert "当前第一版**不覆盖** mainline 的" in text
    for stage in ("data_ready", "signal_ready", "train_freeze", "test_evidence", "backtest_ready", "holdout_validation"):
        assert f"- `{stage}`" in text


def test_stage_display_guidance_skill_defines_four_substructures_for_each_stage() -> None:
    text = _skill_text()
    for stage in EXPECTED_STAGES:
        anchor = f"## Stage: `{stage}`"
        start = text.index(anchor)
        next_start = text.find("\n## Stage: `", start + 1)
        section = text[start:] if next_start == -1 else text[start:next_start]
        assert "### Recommended Summary Blocks" in section, stage
        assert "### Recommended Charts / Tables / Visuals" in section, stage
        assert "### Interpretation Questions" in section, stage
        assert "### Stage-Specific Do / Don’t Rules" in section, stage


def test_stage_display_guidance_skill_does_not_restore_old_runtime_surface() -> None:
    text = _skill_text()
    assert "run_stage_display.py" not in text
    assert "stage_display_runtime.py" not in text
    assert "mandatory post-review" not in text.lower()
