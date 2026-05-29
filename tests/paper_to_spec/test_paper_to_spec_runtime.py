from pathlib import Path

import yaml
import pytest

from runtime.tools import paper_to_spec as paper_to_spec_runtime
from runtime.tools.paper_to_spec import (
    PaperToSpecError,
    materialize_strategy_spec_bundle,
    validate_strategy_spec,
)


def _valid_spec_payload():
    return {
        "spec_version": "v1",
        "strategy_identity": {
            "title": "Quality Spread",
            "summary": "Rank quality and trade the cross-sectional spread.",
            "strategy_type": "cross_sectional_factor",
        },
        "paper_stated": {
            "strategy_claim": {"statement": "High quality names outperform low quality names."},
            "market_scope": {"asset_class": "US equities"},
            "universe_rule": {"rule": "Top 1000 by market cap"},
            "data_requirements": ["prices", "fundamentals"],
            "feature_definition": {"feature": "Gross profitability rank"},
            "label_or_target": {"target": "Next month excess return"},
            "portfolio_construction": {"construction": "Long top decile, short bottom decile"},
            "risk_controls": ["sector neutral"],
            "cost_model": {"transaction_cost": "10 bps one-way"},
            "evaluation_protocol": {"protocol": "Monthly rebalance backtest"},
        },
        "agent_inferred": {
            "inference_log": ["Rank within sector"],
            "implementation_choices": {"feature_processing": "Winsorize features"},
            "default_assumptions": {"price_field": "Use adjusted close"},
            "ambiguities": [],
            "fallback_plan": {"rebalance_calendar": "Default to month-end rebalance"},
        },
        "implementation_handoff": {
            "required_modules": ["data_loader", "factor_builder"],
            "expected_inputs": ["daily_prices", "quarterly_fundamentals"],
            "expected_outputs": ["factor_scores", "portfolio_weights"],
            "validation_targets": ["top_bottom_spread", "turnover"],
        },
    }


@pytest.mark.parametrize("missing_section", ["paper_stated", "agent_inferred"])
def test_validate_strategy_spec_rejects_missing_dual_layer_sections(missing_section):
    spec_payload = _valid_spec_payload()
    spec_payload.pop(missing_section)

    with pytest.raises(PaperToSpecError, match=missing_section):
        validate_strategy_spec(spec_payload)


def test_materialize_strategy_spec_bundle_writes_bundle_and_preserves_key_fields(tmp_path):
    spec_payload = _valid_spec_payload()

    result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Quality Spread Paper",
        spec_payload=spec_payload,
        requested_slug="quality-spread-paper",
    )

    strategy_spec_path = tmp_path / "outputs" / "paper_to_spec" / "quality-spread-paper" / "strategy_spec.yaml"
    source_manifest_path = tmp_path / "outputs" / "paper_to_spec" / "quality-spread-paper" / "source_manifest.yaml"
    strategy_markdown_path = tmp_path / "outputs" / "paper_to_spec" / "quality-spread-paper" / "strategy_spec.md"

    assert result["bundle_root"] == str(tmp_path / "outputs" / "paper_to_spec" / "quality-spread-paper")
    assert result["slug"] == "quality-spread-paper"
    assert strategy_spec_path.exists()
    assert source_manifest_path.exists()
    assert strategy_markdown_path.exists()

    strategy_spec = yaml.safe_load(strategy_spec_path.read_text(encoding="utf-8"))
    source_manifest = yaml.safe_load(source_manifest_path.read_text(encoding="utf-8"))
    strategy_markdown = strategy_markdown_path.read_text(encoding="utf-8")

    assert strategy_spec["strategy_identity"]["strategy_type"] == "cross_sectional_factor"
    assert source_manifest["source"]["kind"] == "pdf_url"
    assert source_manifest["source"]["locator"] == "https://example.com/paper.pdf"
    assert source_manifest["source"]["capture_time"] == "not_captured_in_deterministic_bridge"
    assert "- spec_version: v1" in strategy_markdown
    assert "- title: Quality Spread" in strategy_markdown
    assert "- summary: Rank quality and trade the cross-sectional spread." in strategy_markdown
    assert "- strategy_type: cross_sectional_factor" in strategy_markdown
    assert "strategy_identity" in strategy_markdown
    assert "paper_stated" in strategy_markdown
    assert "agent_inferred" in strategy_markdown


def test_materialize_strategy_spec_bundle_rejects_invalid_source_kind(tmp_path):
    with pytest.raises(PaperToSpecError, match="source_kind"):
        materialize_strategy_spec_bundle(
            outputs_root=tmp_path / "outputs",
            source_locator="https://example.com/paper.pdf",
            source_kind="not_real",
            source_title="Quality Spread Paper",
            spec_payload=_valid_spec_payload(),
        )


def test_validate_strategy_spec_rejects_invalid_strategy_type():
    spec_payload = _valid_spec_payload()
    spec_payload["strategy_identity"]["strategy_type"] = "unknown_strategy"

    with pytest.raises(PaperToSpecError, match="strategy_type"):
        validate_strategy_spec(spec_payload)


def test_validate_strategy_spec_rejects_malformed_value_shape():
    spec_payload = _valid_spec_payload()
    spec_payload["paper_stated"]["strategy_claim"] = "not-a-map"

    with pytest.raises(PaperToSpecError, match="paper_stated.strategy_claim"):
        validate_strategy_spec(spec_payload)


@pytest.mark.parametrize("severity", ["best_effort", "blocking_for_auto_implement"])
def test_validate_strategy_spec_accepts_allowed_ambiguity_severity(severity):
    spec_payload = _valid_spec_payload()
    spec_payload["agent_inferred"]["ambiguities"] = [
        {
            "id": "rebalance-calendar",
            "severity": severity,
            "question": "Should the strategy rebalance at month-end or first trading day?",
            "paper_evidence": ["Section 4"],
        }
    ]

    validated = validate_strategy_spec(spec_payload)

    assert validated["agent_inferred"]["ambiguities"] == spec_payload["agent_inferred"]["ambiguities"]


def test_validate_strategy_spec_rejects_unknown_ambiguity_severity():
    spec_payload = _valid_spec_payload()
    spec_payload["agent_inferred"]["ambiguities"] = [
        {
            "id": "rebalance-calendar",
            "severity": "warn_only",
            "question": "Should the strategy rebalance at month-end or first trading day?",
        }
    ]

    with pytest.raises(PaperToSpecError, match="agent_inferred.ambiguities\\[0\\].severity"):
        validate_strategy_spec(spec_payload)


def test_validate_strategy_spec_rejects_ambiguity_entry_without_required_structure():
    spec_payload = _valid_spec_payload()
    spec_payload["agent_inferred"]["ambiguities"] = [{}]

    with pytest.raises(PaperToSpecError, match="agent_inferred.ambiguities\\[0\\]"):
        validate_strategy_spec(spec_payload)


def test_validate_strategy_spec_rejects_non_mapping_ambiguity_entry():
    spec_payload = _valid_spec_payload()
    spec_payload["agent_inferred"]["ambiguities"] = ["Rebalance calendar not explicit"]

    with pytest.raises(PaperToSpecError, match="agent_inferred.ambiguities\\[0\\]"):
        validate_strategy_spec(spec_payload)


def test_materialize_strategy_spec_bundle_uses_distinct_non_ascii_slugs(tmp_path):
    first_result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/a.pdf",
        source_kind="pdf_url",
        source_title="中文标题甲",
        spec_payload=_valid_spec_payload(),
    )
    second_result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/b.pdf",
        source_kind="pdf_url",
        source_title="中文标题乙",
        spec_payload=_valid_spec_payload(),
    )

    assert first_result["slug"] != second_result["slug"]
    assert first_result["slug"].startswith("strategy-spec-")
    assert second_result["slug"].startswith("strategy-spec-")


def test_rendered_markdown_has_balanced_fences(tmp_path):
    result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Quality Spread Paper",
        spec_payload=_valid_spec_payload(),
        requested_slug="quality-spread-paper",
    )

    strategy_markdown = (
        tmp_path / "outputs" / "paper_to_spec" / result["slug"] / "strategy_spec.md"
    ).read_text(encoding="utf-8")

    assert strategy_markdown.startswith(
        "# Strategy Spec\n\n- spec_version: v1\n- title: Quality Spread\n"
    )
    assert "\n## strategy_identity\n```yaml\n" in strategy_markdown
    assert strategy_markdown.count("```") == 8


def test_materialize_strategy_spec_bundle_falls_back_to_strategy_identity_title_for_slug(tmp_path):
    spec_payload = _valid_spec_payload()
    spec_payload["strategy_identity"]["title"] = "纯中文标题"

    result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="",
        spec_payload=spec_payload,
        requested_slug=None,
    )

    assert result["slug"].startswith("strategy-spec-")
    assert result["slug"] != "strategy-spec"


def test_materialize_strategy_spec_bundle_preserves_explicit_requested_slug(tmp_path):
    result = materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Intraday Reversal",
        spec_payload=_valid_spec_payload(),
        requested_slug="intraday_reversal",
    )

    assert result["slug"] == "intraday_reversal"
    assert (tmp_path / "outputs" / "paper_to_spec" / "intraday_reversal").exists()


def test_materialize_strategy_spec_bundle_rejects_unsafe_explicit_requested_slug(tmp_path):
    with pytest.raises(PaperToSpecError, match="requested_slug"):
        materialize_strategy_spec_bundle(
            outputs_root=tmp_path / "outputs",
            source_locator="https://example.com/paper.pdf",
            source_kind="pdf_url",
            source_title="Intraday Reversal",
            spec_payload=_valid_spec_payload(),
            requested_slug="../intraday_reversal",
        )


def test_materialize_strategy_spec_bundle_rejects_existing_explicit_requested_slug(tmp_path):
    materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Intraday Reversal",
        spec_payload=_valid_spec_payload(),
        requested_slug="intraday_reversal",
    )

    with pytest.raises(PaperToSpecError, match="target already exists"):
        materialize_strategy_spec_bundle(
            outputs_root=tmp_path / "outputs",
            source_locator="https://example.com/paper-v2.pdf",
            source_kind="pdf_url",
            source_title="Intraday Reversal V2",
            spec_payload=_valid_spec_payload(),
            requested_slug="intraday_reversal",
        )


def test_materialize_strategy_spec_bundle_rejects_duplicate_derived_slug_without_requested_slug(tmp_path):
    materialize_strategy_spec_bundle(
        outputs_root=tmp_path / "outputs",
        source_locator="https://example.com/paper.pdf",
        source_kind="pdf_url",
        source_title="Quality Spread Paper",
        spec_payload=_valid_spec_payload(),
    )

    with pytest.raises(PaperToSpecError, match="target already exists"):
        materialize_strategy_spec_bundle(
            outputs_root=tmp_path / "outputs",
            source_locator="https://example.com/paper-v2.pdf",
            source_kind="pdf_url",
            source_title="Quality   Spread Paper!!!",
            spec_payload=_valid_spec_payload(),
        )


def test_materialize_strategy_spec_bundle_converts_atomic_duplicate_slug_error(tmp_path, monkeypatch):
    outputs_root = tmp_path / "outputs"
    target_bundle = outputs_root / "paper_to_spec" / "quality-spread-paper"
    original_mkdir = Path.mkdir

    def fake_mkdir(self, mode=0o777, parents=False, exist_ok=False):
        if self == target_bundle and exist_ok is False:
            raise FileExistsError(str(self))
        return original_mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    with pytest.raises(PaperToSpecError, match="target already exists"):
        materialize_strategy_spec_bundle(
            outputs_root=outputs_root,
            source_locator="https://example.com/paper.pdf",
            source_kind="pdf_url",
            source_title="Quality Spread Paper",
            spec_payload=_valid_spec_payload(),
        )


def test_materialize_strategy_spec_bundle_normalizes_parent_directory_creation_failure(tmp_path):
    outputs_root = tmp_path / "outputs"
    outputs_root.write_text("not-a-directory", encoding="utf-8")

    with pytest.raises(
        PaperToSpecError,
        match="failed to create strategy spec bundle parent directory",
    ):
        materialize_strategy_spec_bundle(
            outputs_root=outputs_root,
            source_locator="https://example.com/paper.pdf",
            source_kind="pdf_url",
            source_title="Quality Spread Paper",
            spec_payload=_valid_spec_payload(),
        )


def test_materialize_strategy_spec_bundle_cleans_partial_bundle_on_write_failure(
    tmp_path, monkeypatch
):
    outputs_root = tmp_path / "outputs"

    def fail_write_text(path: Path, content: str) -> None:
        raise OSError("simulated markdown write failure")

    monkeypatch.setattr(paper_to_spec_runtime, "_write_text_file", fail_write_text)

    with pytest.raises(PaperToSpecError, match="failed to materialize strategy spec bundle"):
        materialize_strategy_spec_bundle(
            outputs_root=outputs_root,
            source_locator="https://example.com/paper.pdf",
            source_kind="pdf_url",
            source_title="Quality Spread Paper",
            spec_payload=_valid_spec_payload(),
            requested_slug="quality-spread-paper",
        )

    assert not (outputs_root / "paper_to_spec" / "quality-spread-paper").exists()
