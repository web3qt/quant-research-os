from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/guides/qros-paper-to-spec-usage.md"
README_PATH = ROOT / "docs/README.codex.md"


def test_paper_to_spec_usage_guide_exists() -> None:
    assert GUIDE_PATH.exists(), f"missing guide: {GUIDE_PATH}"


def test_paper_to_spec_usage_guide_contains_entrypoints() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "$qros-paper-to-spec <url>" in content
    assert "$qros-paper-to-spec <url|pdf|summary>" in content
    assert "URL / 本地 PDF 路径 / 粘贴文本摘要" in content
    assert "默认先产 spec，不先写代码" in content
    assert "--auto-implement" in content
    assert "auto_implement" in content
    assert "detect `auto_implement`" in content
    assert "`source_kind`" in content
    assert "`target repo`" in content
    assert "read source itself" in content
    assert "claim inventory" in content
    assert "formula inventory" in content
    assert "ambiguity inventory" in content
    assert "paper_stated" in content
    assert "agent_inferred" in content
    assert "implementation_handoff" in content
    assert "temp spec file" in content
    assert "只有阻断自动实现的歧义才追问" in content
    assert "ask at most 1-3 follow-up questions only for blocking ambiguities" in content
    assert "默认合同" in content
    assert "strategy_spec.yaml" in content
    assert "strategy_spec.md" in content
    assert "source_manifest.yaml" in content
    assert "不是 `qros-research-session` 的阶段入口" in content
    assert "heavy governance flow" in content
    assert "outputs/paper_to_spec/<paper_slug>/" in content
    assert "active research repo" in content
    assert "active research repo 本地 `outputs/` 树下" in content
    assert "默认停在 `strategy_spec.yaml`、`strategy_spec.md` 和 `source_manifest.yaml`" in content
    assert "source -> spec -> materialize -> stop" in content
    assert "./.qros/bin/qros-paper-to-spec --spec-file" in content
    assert "./.qros/bin/qros-paper-to-spec-baseline" in content
    assert "lower-level materializer/debug surface" in content
    assert "lower-level deterministic scaffold/debug surface" in content
    assert "`--source` is provenance metadata only" in content
    assert "wrapper never fetches/parses paper body itself" in content
    assert "`--source` 只作为 provenance metadata" in content
    assert "wrapper 不会抓取或解析论文正文" in content
    assert "--spec-file" in content
    assert "--source" in content
    assert "--source-kind" in content
    assert "--title" in content
    assert "--slug" in content
    assert "--paper-url" not in content
    assert "--paper-slug" not in content
    assert "source_manifest.json" not in content
    assert "source_inventory.md" not in content
    assert "ambiguities.md" not in content
    assert "implementation_notes.md" not in content


def test_codex_readme_references_paper_to_spec() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "$qros-paper-to-spec https://example.com/paper.pdf" in content
    assert "普通 skill 入口" in content
    assert "source ingestion" in content
    assert "read source itself" in content
    assert "`source_kind`" in content
    assert "`target repo`" in content
    assert "claim inventory" in content
    assert "formula inventory" in content
    assert "ambiguity inventory" in content
    assert "paper_stated" in content
    assert "agent_inferred" in content
    assert "implementation_handoff" in content
    assert "temp spec file" in content
    assert "strategy_spec.yaml" in content
    assert "strategy_spec.md" in content
    assert "source_manifest.yaml" in content
    assert "--auto-implement" in content
    assert "lower-level debug/materializer wrapper" in content
    assert "./.qros/bin/qros-paper-to-spec-baseline" in content
    assert "lower-level deterministic scaffold/debug surface" in content
    assert "active research repo" in content
    assert "active research repo output tree" in content
    assert "不属于 QROS framework repo" in content
    assert "`--source` is provenance metadata only" in content
    assert "wrapper never fetches/parses paper body itself" in content
    assert "`--source` 只作为 provenance metadata" in content
    assert "wrapper 不会抓取或解析论文正文" in content
    assert "./.qros/bin/qros-paper-to-spec --spec-file" in content
    assert "./.qros/bin/qros-paper-to-spec-baseline --spec-path" in content
    assert "--source" in content
    assert "--source-kind" in content
    assert "--title" in content
    assert "--slug" in content
    assert "--paper-url" not in content
    assert "--paper-slug" not in content
    assert "docs/guides/qros-paper-to-spec-usage.md" in content
    assert "/Users/mac08/workspace/web3qt/quant-research-os/docs/guides/qros-paper-to-spec-usage.md" not in content
