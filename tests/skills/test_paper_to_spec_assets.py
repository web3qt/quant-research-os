from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/core/qros-paper-to-spec/SKILL.md"


def test_paper_to_spec_skill_exists() -> None:
    assert SKILL_PATH.exists(), f"missing skill: {SKILL_PATH}"


def test_paper_to_spec_skill_contains_required_contract_strings() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")

    required_strings = [
        "implementable strategy spec",
        "独立于 `qros-research-session`",
        "$qros-paper-to-spec <url>",
        "$qros-paper-to-spec <url|pdf|summary>",
        "URL / 本地 PDF 路径 / 粘贴文本摘要",
        "默认先产 spec，不先写代码",
        "source -> spec -> materialize -> stop",
        "auto_implement",
        "detect `auto_implement`",
        "derive source metadata",
        "`source_kind`",
        "`target repo`",
        "read source itself",
        "local PDF cannot be extracted with available tooling",
        "pasted text instead of inventing content",
        "build internal inventories",
        "`claim inventory`",
        "`formula inventory`",
        "`ambiguity inventory`",
        "produce structured spec draft",
        "只有阻断自动实现的歧义才追问",
        "ask at most 1-3 follow-up questions only for blocking ambiguities",
        "默认合同",
        "普通路径",
        "paper_stated",
        "agent_inferred",
        "implementation_handoff",
        "temp spec file",
        "mandate_admission",
        "heavy governance flow",
        "outputs/paper_to_spec/<paper_slug>/",
        "active research repo",
        "active research repo 本地 `outputs/` 树下",
        "./.qros/bin/qros-paper-to-spec --spec-file",
        "./.qros/bin/qros-paper-to-spec-baseline --spec-path",
        "lower-level materializer/debug surface",
        "`--source` is provenance metadata only",
        "wrapper never fetches/parses paper body itself",
        "`--source` 只作为 provenance metadata",
        "wrapper 不会抓取或解析论文正文",
        "--spec-file",
        "--source",
        "--source-kind",
        "--title",
        "--slug",
        "strategy_spec.yaml",
        "strategy_spec.md",
        "source_manifest.yaml",
        "默认只产出 `strategy_spec.yaml`、`strategy_spec.md` 和 `source_manifest.yaml`，然后停止",
        "report where the spec bundle was written",
        "report where the baseline files were written",
    ]

    for needle in required_strings:
        assert needle in content

    assert "--paper-url" not in content
    assert "--paper-slug" not in content
    assert "source_manifest.json" not in content
    assert "source_inventory.md" not in content
    assert "ambiguities.md" not in content
    assert "implementation_notes.md" not in content
