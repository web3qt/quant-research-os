import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


def _valid_spec_payload():
    return {
        "spec_version": "v1",
        "strategy_identity": {
            "title": "Intraday Reversal",
            "summary": "Trade short-horizon reversal after intraday dislocations.",
            "strategy_type": "time_series_signal",
        },
        "paper_stated": {
            "strategy_claim": {"statement": "Intraday overshoots mean-revert by the close."},
            "market_scope": {"asset_class": "US equities"},
            "universe_rule": {"rule": "Liquid large-cap names"},
            "data_requirements": ["intraday_prices", "daily_prices"],
            "feature_definition": {"feature": "Open-to-midday reversal score"},
            "label_or_target": {"target": "Close-to-next-open return"},
            "portfolio_construction": {"construction": "Trade sign-aligned intraday baskets"},
            "risk_controls": ["beta cap", "sector cap"],
            "cost_model": {"transaction_cost": "5 bps one-way"},
            "evaluation_protocol": {"protocol": "Daily rebalance simulation"},
        },
        "agent_inferred": {
            "inference_log": ["Assume the signal is evaluated on liquid names only."],
            "implementation_choices": {"execution_timing": "Enter near close"},
            "default_assumptions": {"price_field": "Use split-adjusted bars"},
            "ambiguities": [
                {
                    "id": "holding-horizon",
                    "severity": "blocking_for_auto_implement",
                    "question": "Should the holding horizon end at the close or next open?",
                    "paper_evidence": ["Source summary mentions reversal by the close but not exit timing."],
                }
            ],
            "fallback_plan": {"holding_horizon": "Default to close-to-next-open"},
        },
        "implementation_handoff": {
            "required_modules": ["intraday_loader", "signal_builder"],
            "expected_inputs": ["minute_bars", "daily_reference"],
            "expected_outputs": ["signal_series", "trade_intents"],
            "validation_targets": ["hit_rate", "turnover"],
        },
    }


def test_run_paper_to_spec_wrapper_materializes_bundle_and_returns_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"
    spec_file = tmp_path / "spec.yaml"

    spec_file.write_text(
        yaml.safe_dump(_valid_spec_payload(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(tmp_path),
            "--spec-file",
            str(spec_file),
            "--source",
            "https://example.com/intraday-reversal",
            "--source-kind",
            "webpage",
            "--title",
            "Intraday Reversal",
            "--slug",
            "intraday_reversal",
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["slug"] == "intraday_reversal"
    assert (
        tmp_path / "outputs" / "paper_to_spec" / "intraday_reversal" / "strategy_spec.yaml"
    ).exists()


def test_run_paper_to_spec_script_prefixes_argument_errors(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "runtime" / "scripts" / "run_paper_to_spec.py"
    outputs_root = tmp_path / "outputs"

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--outputs-root",
            str(outputs_root),
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.startswith("qros-paper-to-spec: ")


@pytest.mark.parametrize(
    "argv",
    [
        ["--outputs-root", "outputs-placeholder"],
        ["--outputs-root=outputs-placeholder"],
    ],
)
def test_qros_paper_to_spec_wrapper_rejects_manual_outputs_root(tmp_path, argv):
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"

    result = subprocess.run(
        ["/bin/bash", str(wrapper_path), *argv],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert (
        result.stderr.strip()
        == "qros-paper-to-spec: does not accept --outputs-root; it is derived from the project root"
    )


def test_qros_paper_to_spec_wrapper_rejects_bad_cwd(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"
    bad_cwd = tmp_path / "missing-project-root"

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(bad_cwd),
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.strip() == f"qros-paper-to-spec: invalid --cwd path: {bad_cwd}"


def test_qros_paper_to_spec_wrapper_rejects_framework_repo_as_project_root():
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"

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
        f"qros-paper-to-spec: --cwd must point to an active research repo, "
        f"not the QROS framework repo: {repo_root}"
    )


def test_qros_paper_to_spec_wrapper_rejects_unsafe_explicit_slug(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"
    spec_file = tmp_path / "spec.yaml"

    spec_file.write_text(
        yaml.safe_dump(_valid_spec_payload(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(tmp_path),
            "--spec-file",
            str(spec_file),
            "--source",
            "https://example.com/intraday-reversal",
            "--source-kind",
            "webpage",
            "--title",
            "Intraday Reversal",
            "--slug",
            "../intraday_reversal",
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.startswith("qros-paper-to-spec: requested_slug")


@pytest.mark.parametrize("collision_target", ["outputs", "outputs/paper_to_spec"])
def test_qros_paper_to_spec_wrapper_normalizes_parent_directory_collisions(
    tmp_path, collision_target
):
    repo_root = Path(__file__).resolve().parents[2]
    wrapper_path = repo_root / "runtime" / "bin" / "qros-paper-to-spec"
    spec_file = tmp_path / "spec.yaml"

    spec_file.write_text(
        yaml.safe_dump(_valid_spec_payload(), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    collision_path = tmp_path / collision_target
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_path.write_text("not-a-directory", encoding="utf-8")

    result = subprocess.run(
        [
            "/bin/bash",
            str(wrapper_path),
            "--cwd",
            str(tmp_path),
            "--spec-file",
            str(spec_file),
            "--source",
            "https://example.com/intraday-reversal",
            "--source-kind",
            "webpage",
            "--title",
            "Intraday Reversal",
            "--slug",
            "intraday_reversal",
            "--json",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stderr.startswith(
        "qros-paper-to-spec: failed to create strategy spec bundle parent directory "
    )
    assert "Traceback" not in result.stderr
