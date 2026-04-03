from __future__ import annotations

import json
from pathlib import Path
import textwrap

import yaml


STAGE_PROGRAM_SPECS: dict[str, dict[str, object]] = {
    "mandate": {
        "stage_id": "mandate",
        "route": "route_neutral",
        "program_dir": Path("program/mandate"),
        "module": "tools.idea_runtime",
        "function": "build_mandate_from_intake",
        "stage_dir": Path("01_mandate"),
        "inputs": ["00_idea_intake/idea_gate_decision.yaml", "00_idea_intake/mandate_freeze_draft.yaml"],
        "outputs": [
            "01_mandate/mandate.md",
            "01_mandate/research_scope.md",
            "01_mandate/research_route.yaml",
            "01_mandate/time_split.json",
            "01_mandate/parameter_grid.yaml",
            "01_mandate/run_config.toml",
            "01_mandate/artifact_catalog.md",
            "01_mandate/field_dictionary.md",
        ],
    },
    "data_ready": {
        "stage_id": "data_ready",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/data_ready"),
        "module": "tools.data_ready_runtime",
        "function": "build_data_ready_from_mandate",
        "stage_dir": Path("02_data_ready"),
        "inputs": ["01_mandate/mandate.md", "02_data_ready/data_ready_freeze_draft.yaml"],
        "outputs": ["02_data_ready/dataset_manifest.json", "02_data_ready/run_manifest.json"],
    },
    "signal_ready": {
        "stage_id": "signal_ready",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/signal_ready"),
        "module": "tools.signal_ready_runtime",
        "function": "build_signal_ready_from_data_ready",
        "stage_dir": Path("03_signal_ready"),
        "inputs": ["02_data_ready/dataset_manifest.json", "03_signal_ready/signal_ready_freeze_draft.yaml"],
        "outputs": ["03_signal_ready/param_manifest.csv", "03_signal_ready/signal_gate_decision.md"],
    },
    "train_freeze": {
        "stage_id": "train_freeze",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/train_freeze"),
        "module": "tools.train_runtime",
        "function": "build_train_freeze_from_signal_ready",
        "stage_dir": Path("04_train_freeze"),
        "inputs": ["03_signal_ready/param_manifest.csv", "04_train_freeze/train_freeze_draft.yaml"],
        "outputs": ["04_train_freeze/train_thresholds.json", "04_train_freeze/train_gate_decision.md"],
    },
    "test_evidence": {
        "stage_id": "test_evidence",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/test_evidence"),
        "module": "tools.test_evidence_runtime",
        "function": "build_test_evidence_from_train_freeze",
        "stage_dir": Path("05_test_evidence"),
        "inputs": ["04_train_freeze/train_thresholds.json", "05_test_evidence/test_evidence_draft.yaml"],
        "outputs": ["05_test_evidence/test_gate_table.csv", "05_test_evidence/test_gate_decision.md"],
    },
    "backtest_ready": {
        "stage_id": "backtest_ready",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/backtest_ready"),
        "module": "tools.backtest_runtime",
        "function": "build_backtest_ready_from_test_evidence",
        "stage_dir": Path("06_backtest"),
        "inputs": ["05_test_evidence/test_gate_table.csv", "06_backtest/backtest_ready_draft.yaml"],
        "outputs": ["06_backtest/engine_compare.csv", "06_backtest/backtest_gate_decision.md"],
    },
    "holdout_validation": {
        "stage_id": "holdout_validation",
        "route": "time_series_signal",
        "program_dir": Path("program/time_series/holdout_validation"),
        "module": "tools.holdout_runtime",
        "function": "build_holdout_validation_from_backtest",
        "stage_dir": Path("07_holdout"),
        "inputs": ["06_backtest/engine_compare.csv", "07_holdout/holdout_validation_draft.yaml"],
        "outputs": ["07_holdout/holdout_run_manifest.json", "07_holdout/holdout_gate_decision.md"],
    },
    "csf_data_ready": {
        "stage_id": "data_ready",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/data_ready"),
        "module": "tools.csf_data_ready_runtime",
        "function": "build_csf_data_ready_from_mandate",
        "stage_dir": Path("02_csf_data_ready"),
        "inputs": ["01_mandate/mandate.md", "02_csf_data_ready/csf_data_ready_freeze_draft.yaml"],
        "outputs": ["02_csf_data_ready/panel_manifest.json", "02_csf_data_ready/run_manifest.json"],
    },
    "csf_signal_ready": {
        "stage_id": "signal_ready",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/signal_ready"),
        "module": "tools.csf_signal_ready_runtime",
        "function": "build_csf_signal_ready_from_data_ready",
        "stage_dir": Path("03_csf_signal_ready"),
        "inputs": ["02_csf_data_ready/panel_manifest.json", "03_csf_signal_ready/csf_signal_ready_freeze_draft.yaml"],
        "outputs": ["03_csf_signal_ready/factor_panel.parquet", "03_csf_signal_ready/csf_signal_ready_gate_decision.md"],
    },
    "csf_train_freeze": {
        "stage_id": "train_freeze",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/train_freeze"),
        "module": "tools.csf_train_runtime",
        "function": "build_csf_train_freeze_from_signal_ready",
        "stage_dir": Path("04_csf_train_freeze"),
        "inputs": ["03_csf_signal_ready/factor_panel.parquet", "04_csf_train_freeze/csf_train_freeze_draft.yaml"],
        "outputs": ["04_csf_train_freeze/csf_train_freeze.yaml", "04_csf_train_freeze/csf_train_contract.md"],
    },
    "csf_test_evidence": {
        "stage_id": "test_evidence",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/test_evidence"),
        "module": "tools.csf_test_evidence_runtime",
        "function": "build_csf_test_evidence_from_train_freeze",
        "stage_dir": Path("05_csf_test_evidence"),
        "inputs": ["04_csf_train_freeze/csf_train_freeze.yaml", "05_csf_test_evidence/csf_test_evidence_draft.yaml"],
        "outputs": ["05_csf_test_evidence/csf_test_gate_table.csv", "05_csf_test_evidence/csf_test_contract.md"],
    },
    "csf_backtest_ready": {
        "stage_id": "backtest_ready",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/backtest_ready"),
        "module": "tools.csf_backtest_runtime",
        "function": "build_csf_backtest_ready_from_test_evidence",
        "stage_dir": Path("06_csf_backtest_ready"),
        "inputs": ["05_csf_test_evidence/csf_test_gate_table.csv", "06_csf_backtest_ready/csf_backtest_ready_draft.yaml"],
        "outputs": ["06_csf_backtest_ready/csf_backtest_gate_table.csv", "06_csf_backtest_ready/csf_backtest_contract.md"],
    },
    "csf_holdout_validation": {
        "stage_id": "holdout_validation",
        "route": "cross_sectional_factor",
        "program_dir": Path("program/cross_sectional_factor/holdout_validation"),
        "module": "tools.csf_holdout_runtime",
        "function": "build_csf_holdout_validation_from_backtest",
        "stage_dir": Path("07_csf_holdout_validation"),
        "inputs": ["06_csf_backtest_ready/csf_backtest_gate_table.csv", "07_csf_holdout_validation/csf_holdout_validation_draft.yaml"],
        "outputs": ["07_csf_holdout_validation/csf_holdout_run_manifest.json", "07_csf_holdout_validation/csf_holdout_gate_decision.md"],
    },
}


def ensure_stage_program(lineage_root: Path, stage_key: str) -> Path:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    repo_root = Path(__file__).resolve().parents[1]
    program_dir = lineage_root / spec["program_dir"]
    program_dir.mkdir(parents=True, exist_ok=True)
    (program_dir / "README.md").write_text(
        f"# {stage_key} stage program\n\nGenerated for tests.\n",
        encoding="utf-8",
    )
    entrypoint = program_dir / "run_stage.py"
    entrypoint.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            from __future__ import annotations

            import argparse
            from pathlib import Path
            import sys

            ROOT = Path({repr(str(repo_root))})
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))

            from {spec['module']} import {spec['function']}


            def main() -> int:
                parser = argparse.ArgumentParser()
                parser.add_argument('--lineage-root', type=Path, required=True)
                args = parser.parse_args()
                {spec['function']}(args.lineage_root.resolve())
                return 0


            if __name__ == '__main__':
                raise SystemExit(main())
            """
        ),
        encoding="utf-8",
    )
    manifest = {
        "stage_id": spec["stage_id"],
        "route": spec["route"],
        "lineage_id": lineage_root.name,
        "entrypoint": "run_stage.py",
        "entry_type": "python",
        "inputs": [{"kind": "artifact", "path": path, "required": True} for path in spec["inputs"]],
        "outputs": [{"kind": "machine", "path": path, "required": True} for path in spec["outputs"]],
        "depends_on_programs": ["mandate"] if stage_key != "mandate" else [],
        "shared_libs": [],
        "authored_by": {
            "agent_id": "test-agent",
            "agent_role": "executor",
            "session_id": "test-session",
        },
    }
    (program_dir / "stage_program.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return program_dir



def write_fake_stage_provenance(lineage_root: Path, stage_key: str) -> Path:
    spec = STAGE_PROGRAM_SPECS[stage_key]
    stage_dir = lineage_root / spec["stage_dir"]
    stage_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage_id": spec["stage_id"],
        "route": spec["route"],
        "lineage_id": lineage_root.name,
        "stage_status": "awaiting_review_closure",
        "program_dir": str(spec["program_dir"]),
        "stage_program_manifest_path": str(Path(spec["program_dir"]) / "stage_program.yaml"),
        "entrypoint": "run_stage.py",
        "entry_type": "python",
        "program_hash": "test-hash",
        "framework_revision": "test-revision",
        "invoked_at": "2026-04-03T00:00:00+00:00",
        "input_refs": [],
        "output_refs": [],
        "authored_by_agent_id": "test-agent",
        "authored_by_agent_role": "executor",
        "authoring_session_id": "test-session",
        "status": "success",
    }
    path = stage_dir / "program_execution_manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
