from pathlib import Path

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = ROOT / "contracts" / "artifacts"


EXPECTED = {
    "tss_data_ready": {
        "path": "tss_data_ready_artifacts.yaml",
        "stage_dir": "02_tss_data_ready/author/formal",
        "artifacts": {
            "time_index_manifest.json",
            "asset_time_index.parquet",
            "quality_flags.parquet",
            "split_sample_adequacy_report.yaml",
            "run_manifest.json",
            "rebuild_tss_data_ready.py",
        },
    },
    "tss_signal_ready": {
        "path": "tss_signal_ready_artifacts.yaml",
        "stage_dir": "03_tss_signal_ready/author/formal",
        "artifacts": {
            "signal_manifest.yaml",
            "param_manifest.csv",
            "signal_panel.parquet",
            "signal_event_panel.parquet",
            "route_inheritance_contract.yaml",
            "run_manifest.json",
        },
    },
    "tss_train_freeze": {
        "path": "tss_train_freeze_artifacts.yaml",
        "stage_dir": "04_tss_train_freeze/author/formal",
        "artifacts": {
            "tss_train_freeze.yaml",
            "train_threshold_ledger.csv",
            "train_variant_ledger.csv",
            "train_variant_rejects.csv",
            "run_manifest.json",
        },
    },
    "tss_test_evidence": {
        "path": "tss_test_evidence_artifacts.yaml",
        "stage_dir": "05_tss_test_evidence/author/formal",
        "artifacts": {
            "event_forward_return.parquet",
            "signal_performance_summary.json",
            "tss_test_gate_table.csv",
            "tss_selected_variants_test.csv",
            "run_manifest.json",
        },
    },
    "tss_backtest_ready": {
        "path": "tss_backtest_ready_artifacts.yaml",
        "stage_dir": "06_tss_backtest_ready/author/formal",
        "artifacts": {
            "strategy_contract.yaml",
            "engine_compare.csv",
            "position_timeseries.parquet",
            "trade_ledger.csv",
            "tss_backtest_gate_table.csv",
            "run_manifest.json",
        },
    },
    "tss_holdout_validation": {
        "path": "tss_holdout_validation_artifacts.yaml",
        "stage_dir": "07_tss_holdout_validation/author/formal",
        "artifacts": {
            "tss_holdout_run_manifest.json",
            "holdout_signal_diagnostics.parquet",
            "holdout_event_compare.parquet",
            "holdout_backtest_compare.parquet",
            "rolling_holdout_stability.json",
        },
    },
}


def _load_contract(filename: str) -> dict:
    return yaml.safe_load((CONTRACT_DIR / filename).read_text(encoding="utf-8"))


def test_tss_artifact_contract_files_exist_and_declare_stage_shape() -> None:
    for stage, expected in EXPECTED.items():
        contract_path = CONTRACT_DIR / expected["path"]
        assert contract_path.exists(), f"{contract_path} missing"
        contract = _load_contract(expected["path"])
        assert contract["stage"] == stage
        assert contract["stage_dir"] == expected["stage_dir"]
        assert contract["unknown_machine_top_level_fields"] == "forbid"


def test_tss_artifact_contracts_lock_required_artifact_names() -> None:
    for stage, expected in EXPECTED.items():
        contract = _load_contract(expected["path"])
        artifacts = set(contract["artifacts"])
        assert artifacts == expected["artifacts"]


def test_tss_contracts_are_registered_in_artifact_runtime() -> None:
    for stage in EXPECTED:
        contract = load_artifact_contract(stage)
        assert contract["stage"] == stage
