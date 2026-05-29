from __future__ import annotations

from tests.helpers.skill_test_utils import skill_text


def test_csf_data_ready_author_skill_treats_artifact_contract_as_shape_truth() -> None:
    content = skill_text("qros-csf-data-ready-author")

    assert "contracts/artifacts/csf_data_ready_artifacts.yaml" in content
    assert "不得把 `SKILL.md` 当作字段真值" in content
    assert "必须先确认 freeze groups" in content
    assert "lineage-local stage program" in content
    assert "qros-validate-stage --stage csf_data_ready" in content
    assert "validator/preflight 不通过，不得进入 `csf_data_ready` review" in content
    assert "split_sample_adequacy_report.yaml" in content
    assert "cross_section_snapshot" in content


def test_csf_data_ready_author_skill_requires_data_implementation_contract_gate() -> None:
    content = skill_text("qros-csf-data-ready-author")

    assert "data_implementation_contract" in content
    assert "Polars" in content
    assert "pl.scan_parquet" in content
    assert "pandas" in content
    assert "逐行循环" in content
    assert "逐 symbol" in content
    assert "不得询问用户技术实现细节" in content
    assert "stage_program.yaml" in content
    assert "门禁不通过时停在 author lane 修复程序，不得进入 review" in content
    assert "门禁通过后才生成正式 `02_csf_data_ready` artifacts" in content
    assert (
        "Python loop 只能用于 manifest、artifact catalog、field dictionary、输出文件枚举和小型 metadata/report 控制流，"
        "不能承担面板主路径计算。"
    ) in content
    assert "manifest" in content
    assert "artifact catalog" in content
    assert "field dictionary" in content
    assert "输出文件枚举" in content
    assert "metadata/report" in content


def test_csf_data_ready_review_skill_defers_shape_truth_to_runtime_preflight() -> None:
    content = skill_text("qros-csf-data-ready-review")

    assert "reviewer 不替 runtime 重定义字段" in content
    assert "deterministic preflight" in content
    assert "contracts/artifacts/csf_data_ready_artifacts.yaml" in content
    assert "semantic validation" in content
    assert "机制和残留风险" in content
