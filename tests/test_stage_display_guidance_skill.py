from tests.skill_test_utils import skill_bundle_dir


EXPECTED_STAGES = (
    "mandate",
    "csf_data_ready",
    "csf_signal_ready",
    "csf_train_freeze",
    "csf_test_evidence",
    "csf_backtest_ready",
    "csf_holdout_validation",
)

EXPECTED_STAGE_FIELDS = {
    "mandate": (
        "research_question",
        "primary_hypothesis",
        "market / universe",
        "research_route",
        "target_task",
        "excluded_routes",
        "scope_contract",
        "execution_constraints",
        "must_reuse_constraints",
        "change_requires_relineage",
        "data_source",
        "bar_size",
        "time_split",
        "timestamp_semantics",
        "holding_horizons / evaluation horizons",
    ),
    "csf_data_ready": (
        "panel_primary_key",
        "asset_universe_definition",
        "panel_frequency",
        "cross_section_time_key",
        "coverage_rule",
        "panel_manifest_summary",
        "coverage_summary",
        "coverage_gaps / weak slices",
        "eligibility_base_rule",
        "eligibility_exclusion_summary",
        "taxonomy_reference / version",
        "group_neutral_readiness",
    ),
    "csf_signal_ready": (
        "factor_id",
        "factor_name / short label",
        "factor_role",
        "economic intuition / mechanism",
        "target cross-section",
        "expected directional meaning",
        "raw_factor_inputs",
        "transform_pipeline",
        "neutralization_policy",
        "ranking_method / bucket_rule",
        "score_combination_formula",
        "output_signal_definition",
        "frozen_signal_contract_reference",
        "non_governable_axes_after_signal",
        "train_governable_axes",
        "forbidden_train_changes",
        "downstream_train_input_manifest",
    ),
    "csf_train_freeze": (
        "train_window_definition",
        "window_split_logic",
        "regime_definition",
        "regime_segmentation_rule",
        "sampling / rebalance cadence",
        "train_period_rationale",
        "threshold_contract_summary",
        "preprocess_rules",
        "quality_filters",
        "governable_axes",
        "non_governable_axes",
        "threshold_change_guardrail",
    ),
    "csf_test_evidence": (
        "formal_gate_summary",
        "core_test_metrics",
        "pass_thresholds / gate_rules",
        "evidence_by_horizon",
        "winning / accepted configurations",
        "residual_uncertainty_note",
        "admissibility_summary",
        "selected_symbols / selected slices",
        "audit_findings_summary",
        "non_blocking_observations",
        "formal_vs_informational_boundary_note",
        "backtest_entry_implication",
    ),
    "csf_backtest_ready": (
        "execution_policy_summary",
        "portfolio_policy_summary",
        "risk_overlay_summary",
        "rebalance / turnover constraints",
        "positioning / neutrality rule",
        "policy_guardrails",
        "engine_contract_summary",
        "engine_compare_scope",
        "fill / slippage / fee assumptions",
        "simulation boundary assumptions",
        "engine_consistency_rule",
        "reproducibility_reference",
    ),
    "csf_holdout_validation": (
        "holdout_window_definition",
        "window_isolation_rule",
        "reuse_contract_summary",
        "frozen_inputs_reused",
        "forbidden_changes_in_holdout",
        "validation_scope_note",
        "holdout_vs_backtest_consistency_summary",
        "drift_signal_summary",
        "stability_score / stability_judgement",
        "direction_flip / regime_shift_note",
        "key_failure_or_warning_patterns",
        "decision_readiness_summary",
    ),
}


def _skill_text() -> str:
    return (skill_bundle_dir("qros-stage-display") / "SKILL.md").read_text(encoding="utf-8")


def test_stage_display_guidance_skill_exists_with_metadata() -> None:
    bundle_dir = skill_bundle_dir("qros-stage-display")
    assert (bundle_dir / "SKILL.md").exists()
    assert (bundle_dir / "agents" / "openai.yaml").exists()


def test_stage_display_guidance_skill_is_user_triggered_and_not_orchestration_owned() -> None:
    text = _skill_text()
    assert "只在用户**明确提出**类似请求时使用" in text
    assert "**不是** stage orchestration 的一部分" in text
    assert "**不是** mandatory gate" in text
    assert "mandatory gate" in text
    assert "自动在 review 结束后触发" in text
    assert "`*_display_pending`" in text
    assert "runtime HTML renderer" in text
    assert "data acquisition subsystem" in text


def test_stage_display_guidance_skill_covers_exact_v1_scope() -> None:
    text = _skill_text()
    for stage in EXPECTED_STAGES:
        assert f"`{stage}`" in text
    assert "当前第一版**不覆盖** mainline 的" in text
    for stage in ("data_ready", "signal_ready", "train_freeze", "test_evidence", "backtest_ready", "holdout_validation"):
        assert f"- `{stage}`" in text


def test_stage_display_guidance_skill_defines_four_substructures_for_each_stage() -> None:
    text = _skill_text()
    for stage in EXPECTED_STAGES:
        anchor = f"## Stage: `{stage}`"
        start = text.index(anchor)
        next_start = text.find("\n## Stage: `", start + 1)
        section = text[start:] if next_start == -1 else text[start:next_start]
        assert "### Core Blocks" in section or "### Optional Block" in section, stage
        assert "#### Recommended charts / tables / visuals" in section, stage
        assert "#### Interpretation questions" in section, stage
        assert "#### Stage-Specific Do / Don’t Rules" in section, stage


def test_stage_display_guidance_skill_includes_expected_field_level_contracts() -> None:
    text = _skill_text()
    for stage, expected_fields in EXPECTED_STAGE_FIELDS.items():
        anchor = f"## Stage: `{stage}`"
        start = text.index(anchor)
        next_start = text.find("\n## Stage: `", start + 1)
        section = text[start:] if next_start == -1 else text[start:next_start]
        for field_name in expected_fields:
            assert f"`{field_name}`" in section, (stage, field_name)


def test_stage_display_guidance_skill_does_not_restore_old_runtime_surface() -> None:
    text = _skill_text()
    assert "run_stage_display.py" not in text
    assert "stage_display_runtime.py" not in text
    assert "mandatory post-review" not in text.lower()


def test_stage_display_guidance_skill_defines_rendering_and_style_defaults() -> None:
    text = _skill_text()
    assert "## Rendering / Style Defaults" in text
    assert "默认直接输出 `HTML`" in text
    assert "`dashboard + 报告页结合`" in text
    assert "`极简投研风`" in text
    assert "`顺序阅读式`" in text
    assert "roughly `1:1`" in text
    assert "`Plotly + 自定义极简主题`" in text
    assert "同一套 `极简投研风 HTML shell`" in text
    assert "每个阶段只替换：" in text
    assert "block 内容" in text
    assert "字段" in text
    assert "图表类型" in text
