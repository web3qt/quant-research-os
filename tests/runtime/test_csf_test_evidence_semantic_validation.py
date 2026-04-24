from __future__ import annotations

import json
from pathlib import Path

import yaml

from runtime.tools.csf_test_evidence_runtime import build_csf_test_evidence_from_train_freeze
from tests.runtime.test_csf_test_evidence_runtime import (
    _csf_test_evidence_draft,
    _prepare_csf_train_stage,
    _write_yaml,
)


def _build_valid_formal_dir(lineage_root: Path) -> Path:
    _prepare_csf_train_stage(lineage_root)
    stage_dir = lineage_root / "05_csf_test_evidence"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml", _csf_test_evidence_draft(confirmed=True))
    build_csf_test_evidence_from_train_freeze(lineage_root)
    return stage_dir / "author" / "formal"


def test_csf_test_evidence_semantics_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_test_evidence_semantics_rejects_selected_variant_outside_train_kept_set(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    (formal_dir / "csf_selected_variants_test.csv").write_text(
        "variant_id,status\nleaked_variant,selected\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "csf_selected_variants_test.csv: selected variants must be a subset of train kept variants; outside=['leaked_variant']"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_rank_ic_summary_variant_drift(tmp_path: Path) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))
    payload["selected_variant_ids"] = ["leaked_variant"]
    (formal_dir / "rank_ic_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "rank_ic_summary.json: selected_variant_ids must match csf_selected_variants_test.csv; missing=['baseline_v1']; extra=['leaked_variant']"
        in result.errors
    )


def test_csf_test_evidence_semantics_rejects_non_positive_standalone_rank_ic(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))
    payload["mean_rank_ic"] = 0.0
    (formal_dir / "rank_ic_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert "rank_ic_summary.json: standalone_alpha mean_rank_ic must be > 0 before review" in result.errors


def test_csf_test_evidence_semantics_rejects_run_manifest_missing_train_binding(
    tmp_path: Path,
) -> None:
    from runtime.tools.csf_test_evidence_contract_runtime import validate_csf_test_evidence_semantics

    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    payload = json.loads((formal_dir / "run_manifest.json").read_text(encoding="utf-8"))
    payload["input_roots"] = ["author/draft/csf_test_evidence_draft.yaml"]
    (formal_dir / "run_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = validate_csf_test_evidence_semantics(formal_dir, lineage_root)

    assert (
        "run_manifest.json: input_roots must bind to ../04_csf_train_freeze/author/formal/csf_train_freeze.yaml"
        in result.errors
    )
