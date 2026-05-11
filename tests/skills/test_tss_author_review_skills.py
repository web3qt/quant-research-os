from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


STAGES = [
    ("tss_data_ready", "qros-tss-data-ready"),
    ("tss_signal_ready", "qros-tss-signal-ready"),
    ("tss_train_freeze", "qros-tss-train-freeze"),
    ("tss_test_evidence", "qros-tss-test-evidence"),
    ("tss_backtest_ready", "qros-tss-backtest-ready"),
    ("tss_holdout_validation", "qros-tss-holdout-validation"),
]


def _skill_path(stage: str, skill_name: str, lane: str) -> Path:
    return ROOT / "skills" / stage / f"{skill_name}-{lane}" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    match = re.match(r"---\n(?P<body>.*?)\n---\n", content, re.DOTALL)
    assert match, "skill frontmatter missing"
    result: dict[str, str] = {}
    for line in match.group("body").splitlines():
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def test_tss_author_and_review_skills_exist_with_valid_frontmatter() -> None:
    for stage, skill_name in STAGES:
        for lane in ("author", "review"):
            path = _skill_path(stage, skill_name, lane)
            assert path.exists(), f"{path.relative_to(ROOT)} missing"
            content = path.read_text(encoding="utf-8")
            frontmatter = _frontmatter(content)
            assert frontmatter["name"] == f"{skill_name}-{lane}"
            assert re.fullmatch(r"[a-z0-9-]+", frontmatter["name"])
            assert frontmatter["description"].startswith("Use when ")
            assert len(frontmatter["description"]) < 500
            assert stage in content


def test_tss_author_skills_separate_authoring_from_review() -> None:
    for stage, skill_name in STAGES:
        content = _skill_path(stage, skill_name, "author").read_text(encoding="utf-8")
        for heading in [
            "## Artifact Contract Truth",
            "## Required Inputs",
            "## Required Outputs",
            "## Freeze Groups",
            "## Mandatory Discipline",
            "## Gate Discipline",
            "## Working Rules",
        ]:
            assert heading in content
        assert f"qros-validate-stage --stage {stage}" in content
        assert "只能消费 `research_route = time_series_signal` 的上游产物" in content
        assert "不得产出或消费 `csf_*` 横截面因子产物" in content
        assert "不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据" in content
        assert "不得写入 review/result" in content


def test_tss_review_skills_separate_review_from_authoring() -> None:
    for stage, skill_name in STAGES:
        content = _skill_path(stage, skill_name, "review").read_text(encoding="utf-8")
        for heading in [
            "## 共享审查协议",
            "## 独立 reviewer 子代理要求",
            "## 共用输入",
            "## 必需输入",
            "## 必需输出",
            "## 正式门禁",
            "## 审查清单",
            "## Rollback 规则",
            "## 下游权限",
            "## 执行顺序",
        ]:
            assert heading in content
        assert f"qros-validate-stage --stage {stage}" in content
        assert "不得修改 author/formal" in content
        assert "reviewer_findings.raw.yaml" in content
        assert "review_cycle_id: copy the literal review cycle value printed in the reviewer handoff" in content
        assert "reviewer_agent_id: copy the literal reviewer agent id printed in the reviewer handoff" in content
        assert "review_loop_outcome: one of FIX_REQUIRED" in content
        assert "qros-review-cycle prepare" in content
        assert "qros-review" in content


def test_tss_skills_do_not_route_to_signal_diagnostics_scope() -> None:
    combined = "\n".join(
        _skill_path(stage, skill_name, lane).read_text(encoding="utf-8")
        for stage, skill_name in STAGES
        for lane in ("author", "review")
    )
    assert "qros-factor-diagnostics" not in combined
    assert "qros-signal-diagnostics" not in combined
