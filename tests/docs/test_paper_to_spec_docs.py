from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE_PATH = ROOT / "docs/guides/qros-paper-to-spec-usage.md"
README_PATH = ROOT / "docs/README.codex.md"
QROS_BIN = "./.qros/bin/"


def test_paper_to_spec_usage_guide_exists() -> None:
    assert GUIDE_PATH.exists(), f"missing guide: {GUIDE_PATH}"


def test_paper_to_spec_usage_guide_documents_first_paper_data_spec_version() -> None:
    content = GUIDE_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "contracts/paper_to_spec/paper_data_spec_contract.yaml",
        "runtime/scripts/validate_paper_data_spec.py",
        "deterministic validator",
        "reading_coverage",
        "target_market",
        "core_data_requirements",
        "triggered_optional_blocks",
        "strict blocking",
        "strict blocking field",
        "Requirement entry shape",
        "paper_stated",
        "agent_inferred",
        "researcher_required",
        "exchange_profile_default",
        "universe",
        "price_bars",
        "funding",
        "fees_and_slippage",
        "label_or_return_target",
        "timestamp_alignment",
        "data_availability",
        "blocking_question_groups",
        "market_scope",
        "bar_and_price",
        "return_accounting",
        "source_coverage",
        "crypto perpetual",
        "不直接生成完整 strategy spec",
        "不直接生成回测代码",
        "不把 validator failure 包装成 review verdict",
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
    assert "contracts/paper_to_spec/paper_data_spec_contract.yaml" in content
    assert "runtime/scripts/validate_paper_data_spec.py" in content
    assert "strict blocking" in content
    assert "下一版会采用 data-spec-first" not in content
    assert QROS_BIN + "qros-paper-to-spec" not in content
    assert QROS_BIN + "qros-paper-to-spec" + "-baseline" not in content
    assert "--auto" + "-implement" not in content
