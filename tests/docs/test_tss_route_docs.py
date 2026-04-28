from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_FLOW = ROOT / "docs" / "sop" / "main-flow"


TSS_SOPS = [
    "02_tss_data_ready_sop_cn.md",
    "03_tss_signal_ready_sop_cn.md",
    "04_tss_train_freeze_sop_cn.md",
    "05_tss_test_evidence_sop_cn.md",
    "06_tss_backtest_ready_sop_cn.md",
    "07_tss_holdout_validation_sop_cn.md",
]

LEGACY_UNPREFIXED_TSS_DOCS = [
    MAIN_FLOW / "02_data_ready_sop_cn.md",
    MAIN_FLOW / "03_signal_ready_sop_cn.md",
    MAIN_FLOW / "04_train_freeze_sop_cn.md",
    MAIN_FLOW / "05_test_evidence_sop_cn.md",
    MAIN_FLOW / "06_backtest_ready_sop_cn.md",
    MAIN_FLOW / "07_holdout_validation_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "02_data_ready_failure_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "03_signal_ready_failure_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "04_train_freeze_failure_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "05_test_evidence_failure_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "06_backtest_failure_sop_cn.md",
    ROOT / "docs" / "sop" / "failures" / "07_holdout_failure_sop_cn.md",
]


def test_research_workflow_sop_uses_tss_route_names() -> None:
    content = (MAIN_FLOW / "research_workflow_sop.md").read_text(encoding="utf-8")
    for stage_dir in [
        "02_tss_data_ready",
        "03_tss_signal_ready",
        "04_tss_train_freeze",
        "05_tss_test_evidence",
        "06_tss_backtest_ready",
        "07_tss_holdout_validation",
    ]:
        assert stage_dir in content
    assert "02_data_ready → 03_signal_ready" not in content


def test_tss_stage_sops_exist_and_define_time_series_scope() -> None:
    for name in TSS_SOPS:
        path = MAIN_FLOW / name
        assert path.exists(), f"{name} missing"
        content = path.read_text(encoding="utf-8")
        assert "time_series_signal" in content
        assert "单个资产用自己的历史预测自己的未来路径/方向" in content
        assert "不是横截面排序" in content
        assert "qros-validate-stage --stage tss_" in content
        assert "Rank IC / Top-Bottom / bucket monotonicity" in content


def test_unprefixed_time_series_sops_are_marked_legacy_compatibility() -> None:
    for path in LEGACY_UNPREFIXED_TSS_DOCS:
        content = path.read_text(encoding="utf-8")
        assert "Legacy compatibility doc" in content, f"{path} missing legacy banner"
        assert "new `time_series_signal` lineages" in content, f"{path} missing new-lineage warning"
        assert "02_tss_data_ready" in content, f"{path} missing canonical TSS route pointer"


def test_codex_entry_docs_use_skill_entries_not_backend_scripts() -> None:
    research_session = (ROOT / "skills" / "core" / "qros-research-session" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    using_qros = (ROOT / "skills" / "core" / "using-qros" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    combined = research_session + "\n" + using_qros
    assert "$qros-research-session" in combined
    assert "$qros-progress" in combined
    assert "不要让用户直接执行底层脚本" in combined
    assert "qros-session --raw-idea" in research_session
    assert "backend mechanics" in research_session


def test_research_session_skill_marks_unprefixed_time_series_dirs_as_legacy() -> None:
    content = (ROOT / "skills" / "core" / "qros-research-session" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "Legacy unprefixed time_series_signal directories" in content
    assert "not canonical for new `time_series_signal` lineages" in content


def test_research_session_usage_does_not_present_legacy_data_ready_as_tss_normal_path() -> None:
    usage = (ROOT / "docs" / "guides" / "qros-research-session-usage.md").read_text(encoding="utf-8")

    assert "build `02_data_ready/`" not in usage
    assert "build `02_tss_data_ready/`" in usage
    assert "tss_data_ready" in usage
    assert "tss_holdout_validation review" in usage
    assert "$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断" in usage


def test_current_readme_and_visual_docs_use_prefixed_tss_and_csf_stage_names() -> None:
    docs = {
        "README.md": ROOT / "README.md",
        "docs/visuals/README.md": ROOT / "docs" / "visuals" / "README.md",
        "docs/visuals/qros-simple.drawio": ROOT / "docs" / "visuals" / "qros-simple.drawio",
        "docs/visuals/qros-long.drawio": ROOT / "docs" / "visuals" / "qros-long.drawio",
        "docs/visuals/qros-stage-artifact-map.drawio": ROOT
        / "docs"
        / "visuals"
        / "qros-stage-artifact-map.drawio",
        "docs/sop/main-flow/drawio/qros_factor_research_workflow_overview.drawio": ROOT
        / "docs"
        / "sop"
        / "main-flow"
        / "drawio"
        / "qros_factor_research_workflow_overview.drawio",
        "docs/sop/main-flow/drawio/factor-workflow.drawio": ROOT
        / "docs"
        / "sop"
        / "main-flow"
        / "drawio"
        / "factor-workflow.drawio",
    }

    required = [
        "02_tss_data_ready",
        "03_tss_signal_ready",
        "04_tss_train_freeze",
        "05_tss_test_evidence",
        "06_tss_backtest_ready",
        "07_tss_holdout_validation",
        "02_csf_data_ready",
        "03_csf_signal_ready",
        "04_csf_train_freeze",
        "05_csf_test_evidence",
        "06_csf_backtest_ready",
        "07_csf_holdout_validation",
    ]
    legacy_tokens = [
        "01 data_ready",
        "02 signal_ready",
        "03 train_freeze",
        "04 test_evidence",
        "05 backtest_ready",
        "06 holdout_validation",
        "01 csf_data_ready",
        "02 csf_signal_ready",
        "03 csf_train_freeze",
        "04 csf_test_evidence",
        "05 csf_backtest_ready",
        "06 csf_holdout_validation",
        "02_data_ready -> 03_signal_ready",
        "02_data_ready -&gt; 03_signal_ready",
    ]

    for label, path in docs.items():
        content = path.read_text(encoding="utf-8")
        for token in required:
            assert token in content, f"{label} missing {token}"
        for token in legacy_tokens:
            assert token not in content, f"{label} still contains {token}"
