from tests.helpers.skill_test_utils import skill_text


POST_MANDATE_AUTHOR_SKILLS = (
    "qros-data-ready-author",
    "qros-signal-ready-author",
    "qros-train-freeze-author",
    "qros-test-evidence-author",
    "qros-backtest-ready-author",
    "qros-holdout-validation-author",
    "qros-csf-data-ready-author",
    "qros-csf-signal-ready-author",
    "qros-csf-train-freeze-author",
    "qros-csf-test-evidence-author",
    "qros-csf-backtest-ready-author",
    "qros-csf-holdout-validation-author",
)

REQUIRED_SUBSTRINGS = (
    "显式生成或刷新本 stage 的 lineage-local stage program",
    "真实产生产物的程序",
    "thin wrapper",
    "关键步骤",
    "中文注释",
    "docs/guides/qros-authoring-language-discipline.md",
)


def test_post_mandate_author_skills_require_explicit_stage_program_authoring() -> None:
    for skill_name in POST_MANDATE_AUTHOR_SKILLS:
        text = skill_text(skill_name)
        for needle in REQUIRED_SUBSTRINGS:
            assert needle in text, f"{needle} missing in {skill_name}"
