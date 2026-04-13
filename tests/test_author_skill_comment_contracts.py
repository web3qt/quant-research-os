from pathlib import Path

from tests.skill_test_utils import skill_path, skill_text


# 用关键词集合锁定契约语义，避免只靠一整句精确匹配导致后续微调过脆。
REQUIRED_SUBSTRINGS = (
    "新增或修改代码",
    "关键逻辑",
    "阶段门禁",
    "分支判断",
    "易误解流程",
    "中文注释",
    "不要求逐行注释",
    "不要求回填历史代码",
)

LANGUAGE_GUIDANCE_SUBSTRINGS = (
    "machine-readable 字段名",
    "解释性内容",
    "适合则优先用中文表达",
    "用户明确要求英文",
)

AUTHOR_SKILL_NAMES = (
    "qros-idea-intake-author",
    "qros-mandate-author",
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

EXCLUDED_SKILL_PATHS = (
    skill_path("qros-research-session"),
    skill_path("qros-stage-failure-handler"),
)


def test_author_skill_comment_contract_substrings_exist_in_grouped_source_tree() -> None:
    for skill_name in AUTHOR_SKILL_NAMES:
        repo_text = skill_text(skill_name)
        for needle in REQUIRED_SUBSTRINGS:
            assert needle in repo_text, f"{needle} missing in {skill_path(skill_name)}"


def test_author_skill_comment_contract_keeps_required_substrings_complete() -> None:
    for skill_name in AUTHOR_SKILL_NAMES:
        repo_text = skill_text(skill_name)
        repo_hits = {needle for needle in REQUIRED_SUBSTRINGS if needle in repo_text}
        assert repo_hits == set(REQUIRED_SUBSTRINGS)


def test_author_skill_language_guidance_substrings_exist_in_grouped_source_tree() -> None:
    for skill_name in AUTHOR_SKILL_NAMES:
        repo_text = skill_text(skill_name)
        for needle in LANGUAGE_GUIDANCE_SUBSTRINGS:
            assert needle in repo_text, f"{needle} missing in {skill_path(skill_name)}"


def test_excluded_skill_surfaces_do_not_pick_up_the_contract_marker() -> None:
    marker = "易误解流程补充清晰、简短、面向维护者的中文注释"
    for path in EXCLUDED_SKILL_PATHS:
        assert marker not in path.read_text(encoding="utf-8"), f"unexpected contract marker in {path}"
