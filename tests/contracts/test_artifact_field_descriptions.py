from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_DIR = Path("contracts/artifacts")


def test_artifact_contract_fields_have_runtime_facing_descriptions() -> None:
    for contract_path in sorted(CONTRACT_DIR.glob("*_artifacts.yaml")):
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        for artifact_name, artifact in contract["artifacts"].items():
            for field in artifact.get("fields", []):
                assert isinstance(field.get("description"), str), (
                    f"{contract_path}:{artifact_name}:{field['path']} missing description"
                )
                assert field["description"].strip(), (
                    f"{contract_path}:{artifact_name}:{field['path']} has empty description"
                )
