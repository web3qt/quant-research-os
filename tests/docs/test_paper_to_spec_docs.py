from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/guides/qros-paper-to-spec-usage.md"
README_PATH = ROOT / "docs/README.codex.md"
QROS_BIN = "./.qros/bin/"


def test_paper_to_spec_usage_guide_exists() -> None:
    assert GUIDE_PATH.exists(), f"missing guide: {GUIDE_PATH}"


def test_paper_to_spec_usage_guide_documents_removed_legacy_path() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "PDF 读取覆盖",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不直接生成回测代码",
        "不是 `qros-research-session` 的阶段入口",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        QROS_BIN + "qros-paper-to-spec",
        QROS_BIN + "qros-paper-to-spec" + "-baseline",
        "--spec" + "-file",
        "--auto" + "-implement",
        "auto" + "_implement",
        "source -> spec -> materialize -> stop",
        "默认停在 `" + "strategy_" + "spec.yaml`",
    ]

    for needle in forbidden_strings:
        assert needle not in content


def test_codex_readme_documents_paper_to_spec_reset() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "$qros-paper-to-spec" in content
    assert "旧 `strategy_spec` materializer 已移除" in content
    assert "paper_data_spec.yaml" in content
    assert QROS_BIN + "qros-paper-to-spec" not in content
    assert QROS_BIN + "qros-paper-to-spec" + "-baseline" not in content
    assert "--auto" + "-implement" not in content
