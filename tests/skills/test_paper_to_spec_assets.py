from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/core/qros-paper-to-spec/SKILL.md"
QROS_BIN = "./.qros/bin/"


def test_paper_to_spec_skill_exists() -> None:
    assert SKILL_PATH.exists(), f"missing skill: {SKILL_PATH}"


def test_paper_to_spec_skill_documents_first_paper_data_spec_version() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")

    required_strings = [
        "qros-paper-to-spec",
        "旧 `strategy_spec` materializer 已移除",
        "旧 baseline scaffold 已移除",
        "data-spec-first",
        "paper_data_spec.yaml",
        "contracts/paper_to_spec/paper_data_spec_contract.yaml",
        "runtime/scripts/validate_paper_data_spec.py",
        "deterministic validator",
        "Execution protocol",
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
        "独立于 `qros-research-session`",
        "heavy governance flow",
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
        "默认只产出 `" + "strategy_" + "spec.yaml`",
        "report where the baseline files were written",
    ]

    for needle in forbidden_strings:
        assert needle not in content

    assert "--paper-url" not in content
    assert "--paper-slug" not in content
    assert "source_manifest.json" not in content
    assert "source_inventory.md" not in content
    assert "ambiguities.md" not in content
    assert "implementation_notes.md" not in content
