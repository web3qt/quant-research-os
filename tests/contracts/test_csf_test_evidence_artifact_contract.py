from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_test_evidence_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_csf_test_evidence_contract_locks_run_manifest_rank_ic_binding() -> None:
    contract = _load_contract()
    run_manifest = contract["artifacts"]["run_manifest.json"]

    assert run_manifest["type"] == "json"
    assert run_manifest["unknown_top_level_fields"] == "forbid"
    assert "rank_ic_input_binding" in _field_paths(run_manifest)
    binding_field = next(field for field in run_manifest["fields"] if field["path"] == "rank_ic_input_binding")
    assert binding_field["type"] == "map"
