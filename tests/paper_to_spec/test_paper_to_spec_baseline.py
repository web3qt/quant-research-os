from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

import runtime.tools.paper_to_spec_baseline as baseline_runtime
from runtime.tools.paper_to_spec_baseline import BaselineScaffoldError, scaffold_baseline_from_spec


def _strategy_spec_yaml(*, strategy_type: str) -> str:
    return yaml.safe_dump(
        {
            "spec_version": "v1",
            "strategy_identity": {
                "title": "Value Paper",
                "summary": "Rank cheap assets and trade the spread.",
                "strategy_type": strategy_type,
            },
            "paper_stated": {
                "strategy_claim": {"statement": "Cheap assets outperform expensive assets."},
                "market_scope": {"asset_class": "US equities"},
                "universe_rule": {"rule": "Top 1000 by market cap"},
                "data_requirements": ["prices", "fundamentals"],
                "feature_definition": {"feature": "Book-to-market rank"},
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
        },
        sort_keys=False,
        allow_unicode=True,
    )


def test_scaffold_baseline_from_spec_fallback_layout_writes_runnable_bundle(tmp_path: Path) -> None:
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="cross_sectional_factor"), encoding="utf-8")

    result = scaffold_baseline_from_spec(
        target_repo=target_repo,
        spec_path=spec_path,
        prefer_repo_native=True,
    )

    bundle_root = target_repo / "paper_specs" / "value_paper"
    assert result["layout_mode"] == "fallback"
    assert result["bundle_root"] == str(bundle_root)
    assert result["run_entrypoint"] == str(bundle_root / "run_backtest.py")
    assert result["smoke_test_path"] == str(bundle_root / "tests" / "test_smoke.py")
    assert (target_repo / "paper_specs" / "value_paper" / "strategy_config.yaml").exists()
    assert (target_repo / "paper_specs" / "value_paper" / "build_dataset.py").exists()
    assert (target_repo / "paper_specs" / "value_paper" / "build_signal.py").exists()
    assert (target_repo / "paper_specs" / "value_paper" / "run_backtest.py").exists()
    assert (target_repo / "paper_specs" / "value_paper" / "tests" / "test_smoke.py").exists()



def test_scaffold_baseline_from_spec_prefers_repo_native_research_root(tmp_path: Path) -> None:
    target_repo = tmp_path / "research_repo"
    (target_repo / "research").mkdir(parents=True)
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="cross_sectional_factor"), encoding="utf-8")

    result = scaffold_baseline_from_spec(
        target_repo=target_repo,
        spec_path=spec_path,
        prefer_repo_native=True,
    )

    bundle_root = target_repo / "research" / "value_paper"
    assert result["layout_mode"] == "repo_native"
    assert result["bundle_root"] == str(bundle_root)
    assert (bundle_root / "strategy_config.yaml").exists()
    assert (bundle_root / "tests" / "test_smoke.py").exists()



def test_scaffold_baseline_from_spec_does_not_treat_src_alone_as_repo_native(tmp_path: Path) -> None:
    target_repo = tmp_path / "research_repo"
    (target_repo / "src").mkdir(parents=True)
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="cross_sectional_factor"), encoding="utf-8")

    result = scaffold_baseline_from_spec(
        target_repo=target_repo,
        spec_path=spec_path,
        prefer_repo_native=True,
    )

    assert result["layout_mode"] == "fallback"
    assert (target_repo / "paper_specs" / "value_paper").exists()
    assert not (target_repo / "src" / "value_paper").exists()



def test_scaffold_baseline_from_spec_rejects_missing_target_repo(tmp_path: Path) -> None:
    missing_repo = tmp_path / "missing_repo"
    spec_path = tmp_path / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="time_series_signal"), encoding="utf-8")

    with pytest.raises(BaselineScaffoldError) as excinfo:
        scaffold_baseline_from_spec(
            target_repo=missing_repo,
            spec_path=spec_path,
            prefer_repo_native=True,
        )

    assert "target repo" in str(excinfo.value)


def test_scaffold_baseline_from_spec_validates_required_fields_before_creating_bundle(
    tmp_path: Path,
) -> None:
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_payload = yaml.safe_load(_strategy_spec_yaml(strategy_type="cross_sectional_factor"))
    spec_payload["implementation_handoff"].pop("validation_targets")
    spec_path.write_text(
        yaml.safe_dump(spec_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(BaselineScaffoldError, match="validation_targets"):
        scaffold_baseline_from_spec(
            target_repo=target_repo,
            spec_path=spec_path,
            prefer_repo_native=True,
        )

    assert not (target_repo / "paper_specs" / "value_paper").exists()



def test_scaffold_baseline_from_spec_reuses_main_strategy_spec_validator(
    tmp_path: Path,
) -> None:
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_payload = yaml.safe_load(_strategy_spec_yaml(strategy_type="cross_sectional_factor"))
    spec_payload["paper_stated"]["strategy_claim"] = "not-a-map"
    spec_path.write_text(
        yaml.safe_dump(spec_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    with pytest.raises(BaselineScaffoldError, match="paper_stated.strategy_claim"):
        scaffold_baseline_from_spec(
            target_repo=target_repo,
            spec_path=spec_path,
            prefer_repo_native=True,
        )

    assert not (target_repo / "paper_specs" / "value_paper").exists()


def test_scaffold_baseline_from_spec_cleans_partial_bundle_on_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="cross_sectional_factor"), encoding="utf-8")
    bundle_root = target_repo / "paper_specs" / "value_paper"

    original_write_text = baseline_runtime._write_text

    def failing_write_text(path: Path, content: str) -> None:
        if path.name == "build_signal.py":
            raise OSError("disk full")
        original_write_text(path, content)

    monkeypatch.setattr(baseline_runtime, "_write_text", failing_write_text)

    with pytest.raises(BaselineScaffoldError, match="disk full"):
        scaffold_baseline_from_spec(
            target_repo=target_repo,
            spec_path=spec_path,
            prefer_repo_native=True,
        )

    assert not bundle_root.exists()



def test_run_paper_to_spec_baseline_script_success_path_returns_json(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "runtime" / "scripts" / "run_paper_to_spec_baseline.py"
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="time_series_signal"), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--target-repo",
            str(target_repo),
            "--spec-path",
            str(spec_path),
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["layout_mode"] == "fallback"
    assert payload["bundle_root"] == str(target_repo / "paper_specs" / "value_paper")
    assert (target_repo / "paper_specs" / "value_paper" / "run_backtest.py").exists()



def test_run_paper_to_spec_baseline_script_normalizes_duplicate_bundle_errors(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "runtime" / "scripts" / "run_paper_to_spec_baseline.py"
    target_repo = tmp_path / "research_repo"
    target_repo.mkdir()
    spec_dir = target_repo / "outputs" / "paper_to_spec" / "value_paper"
    spec_dir.mkdir(parents=True)
    spec_path = spec_dir / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="time_series_signal"), encoding="utf-8")
    (target_repo / "paper_specs" / "value_paper").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--target-repo",
            str(target_repo),
            "--spec-path",
            str(spec_path),
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.startswith("qros-paper-to-spec-baseline: ")
    assert "target bundle already exists" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("target_repo_arg", [["--target-repo", "/tmp/override"], ["--target-repo=/tmp/override"]])
def test_qros_paper_to_spec_baseline_wrapper_rejects_manual_target_repo(
    tmp_path: Path,
    target_repo_arg: list[str],
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec-baseline"
    spec_path = tmp_path / "strategy_spec.yaml"
    spec_path.write_text(_strategy_spec_yaml(strategy_type="time_series_signal"), encoding="utf-8")

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(tmp_path),
            *target_repo_arg,
            "--spec-path",
            str(spec_path),
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert (
        result.stderr.strip()
        == "qros-paper-to-spec-baseline: does not accept --target-repo; it is derived from --cwd or current directory"
    )


def test_qros_paper_to_spec_baseline_wrapper_rejects_framework_repo_as_project_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec-baseline"

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(repo_root),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.strip() == (
        f"qros-paper-to-spec-baseline: --cwd must point to an active research repo, "
        f"not the QROS framework repo: {repo_root}"
    )
