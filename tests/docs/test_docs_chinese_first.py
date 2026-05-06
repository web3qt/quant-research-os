from pathlib import Path


CHINESE_FIRST_HEADINGS = {
    Path("docs/README.codex.md"): (
        "# QROS Codex 使用指南",
        "## 快速安装",
        "## 安装结果",
        "## 工作方式",
    ),
    Path("docs/guides/installation.md"): (
        "# QROS 安装指南",
        "## 支持的宿主",
        "## Codex 用户推荐路径",
        "## 安装布局",
    ),
    Path("docs/guides/quickstart-codex.md"): (
        "# QROS Codex 快速开始",
        "## 1. 安装",
        "## 2. 从统一 Skill 开始",
    ),
    Path("docs/guides/qros-research-session-usage.md"): (
        "# QROS 统一研究会话使用说明",
        "## 它是什么",
        "## 当前覆盖边界",
        "## 用户入口",
    ),
    Path("docs/guides/qros-agent-behavior-eval.md"): (
        "# QROS Agent 行为评估",
        "## Fake Transcript / 假 Transcript",
        "## MVP 用例",
        "## TSS 用例",
    ),
    Path("docs/guides/qros-verification-tiers.md"): (
        "# QROS 验证分层",
        "## 目的",
        "## 验证层级",
        "## 当前边界",
    ),
    Path("docs/guides/idea-intake-to-mandate-flow.md"): (
        "# 从 Idea Intake 到 Mandate 的流程",
        "## 目标",
        "## 流程",
        "## Qualification 规则",
    ),
    Path("docs/guides/qros-review-shared-protocol.md"): (
        "# QROS 共享 Review 协议",
        "## 目的",
        "## 共享输入",
        "## Closure Artifacts / 关闭产物",
    ),
    Path("docs/guides/codex-stage-review-skill-usage.md"): (
        "# 阶段 Review Skill 使用说明",
        "## 作用域",
        "## 这些 Skill 做什么",
        "## 规则输入",
    ),
    Path("docs/guides/closure-artifact-writer-usage.md"): (
        "# Closure Artifact Writer 使用说明",
        "## 作用域",
        "## 写入文件",
        "## 上下文解析",
    ),
    Path("docs/guides/stage-freeze-group-field-guide.md"): (
        "# QROS Stage Freeze Group 字段指南",
        "## 目的",
        "## 使用方式",
    ),
    Path("docs/guides/qros-authoring-language-discipline.md"): (
        "# QROS Authoring 语言规范",
        "## 目的",
        "## 规则",
    ),
    Path("docs/guides/qros-factor-diagnostics.md"): (
        "# QROS 因子诊断",
        "## 怎么用",
        "## 输出说明",
    ),
    Path("docs/guides/qros-signal-diagnostics.md"): (
        "# QROS 信号诊断",
        "## 怎么用",
        "## 输出说明",
    ),
    Path("docs/anti_drift_baseline_promotion_protocol.md"): (
        "# QROS Anti-Drift 基线提升协议",
        "## 作用域",
        "## 核心规则",
    ),
    Path("docs/drift_coverage_matrix.md"): (
        "# QROS Skill Anti-Drift 覆盖矩阵",
        "## Canonical Decision Snapshot 字段",
        "## 当前缺口",
    ),
    Path("docs/sop/review/stage_completion_standard_cn.md"): (
        "# 阶段完成标准（机构级中文版）",
    ),
    Path("docs/sop/review/stage_completion_certificate_template_cn.md"): (
        "# 阶段完成证书模板（机构级中文版）",
    ),
    Path("docs/sop/review/strict_backtest_review_checklist_cn.md"): (
        "# 严格回测 Review 检查清单（机构级中文版）",
    ),
}


FORBIDDEN_ENGLISH_HEADINGS = (
    "# QROS for Codex",
    "# QROS Installation",
    "# QROS Quickstart For Codex",
    "# QROS Research Session Usage",
    "# QROS Agent Behavior Eval",
    "# QROS Verification Tiers",
    "# Idea Intake To Mandate Flow",
    "# QROS Shared Review Protocol",
    "# Codex Stage Review Skill Usage",
    "# Closure Artifact Writer Usage",
    "# QROS Factor Diagnostics",
    "# QROS Signal Diagnostics",
)


def test_user_facing_docs_use_chinese_first_headings() -> None:
    missing: list[str] = []

    for path, headings in CHINESE_FIRST_HEADINGS.items():
        text = path.read_text(encoding="utf-8")
        for heading in headings:
            if heading not in text:
                missing.append(f"{path}: {heading}")

    assert not missing, "Docs missing Chinese-first headings:\n" + "\n".join(missing)


def test_user_facing_docs_do_not_keep_old_english_primary_titles() -> None:
    offenders: list[str] = []

    for path in CHINESE_FIRST_HEADINGS:
        text = path.read_text(encoding="utf-8")
        for heading in FORBIDDEN_ENGLISH_HEADINGS:
            if heading in text:
                offenders.append(f"{path}: {heading}")

    assert not offenders, "Old English primary headings remain:\n" + "\n".join(offenders)
