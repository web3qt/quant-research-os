from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/core/qros-paper-to-spec/SKILL.md"


def test_paper_to_spec_skill_exists() -> None:
    assert SKILL_PATH.exists(), f"missing skill: {SKILL_PATH}"


def test_paper_to_spec_skill_documents_removed_legacy_path_and_v2_direction() -> None:
    content = SKILL_PATH.read_text(encoding="utf-8")

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
        "独立于 `qros-research-session`",
        "heavy governance flow",
    ]

    for needle in required_strings:
        assert needle in content

    forbidden_strings = [
        "./.qros/bin/qros-paper-to-spec",
        "./.qros/bin/qros-paper-to-spec-baseline",
        "--spec-file",
        "--auto-implement",
        "auto_implement",
        "source -> spec -> materialize -> stop",
        "默认只产出 `strategy_spec.yaml`",
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
