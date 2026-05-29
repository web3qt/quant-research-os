from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from tests.helpers.freeze_draft_support import with_freeze_digests
from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from runtime.tools.tss_backtest_runtime import build_tss_backtest_ready_from_test_evidence
from runtime.tools.tss_data_ready_runtime import build_tss_data_ready_from_mandate
from runtime.tools.tss_holdout_runtime import build_tss_holdout_validation_from_backtest_ready
from runtime.tools.tss_signal_ready_runtime import build_tss_signal_ready_from_data_ready
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from runtime.tools.tss_train_runtime import build_tss_train_freeze_from_signal_ready
from tests.helpers.skill_test_utils import skill_text
from tests.helpers.lineage_program_support import ensure_stage_program
from tests.runtime.test_tss_backtest_runtime import (
    _prepare_tss_test_evidence_stage,
    _tss_backtest_ready_draft,
)
from tests.runtime.test_tss_data_ready_runtime import (
    _prepare_tss_mandate_stage,
    _tss_data_ready_draft,
)
from tests.runtime.test_tss_holdout_runtime import (
    _prepare_tss_backtest_ready_stage,
    _tss_holdout_validation_draft,
)
from tests.runtime.test_tss_signal_ready_runtime import (
    _prepare_tss_data_ready_stage,
    _tss_signal_ready_draft,
)
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
)
from tests.runtime.test_tss_train_runtime import (
    _prepare_tss_signal_ready_stage,
    _tss_train_freeze_draft,
)


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = with_freeze_digests(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _build_tss_data_ready(lineage_root: Path) -> Path:
    _prepare_tss_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_tss_data_ready"
    _write_yaml(stage_dir / "author" / "draft" / "tss_data_ready_freeze_draft.yaml", _tss_data_ready_draft(confirmed=True))
    build_tss_data_ready_from_mandate(lineage_root)
    return stage_dir / "author" / "formal"


def _build_tss_signal_ready(lineage_root: Path) -> Path:
    _prepare_tss_data_ready_stage(lineage_root)
    stage_dir = lineage_root / "03_tss_signal_ready"
    _write_yaml(stage_dir / "author" / "draft" / "tss_signal_ready_freeze_draft.yaml", _tss_signal_ready_draft(confirmed=True))
    build_tss_signal_ready_from_data_ready(lineage_root)
    return stage_dir / "author" / "formal"


def _build_tss_train_freeze(lineage_root: Path) -> Path:
    _prepare_tss_signal_ready_stage(lineage_root)
    stage_dir = lineage_root / "04_tss_train_freeze"
    _write_yaml(stage_dir / "author" / "draft" / "tss_train_freeze_draft.yaml", _tss_train_freeze_draft(confirmed=True))
    build_tss_train_freeze_from_signal_ready(lineage_root)
    return stage_dir / "author" / "formal"


def _build_tss_test_evidence(lineage_root: Path) -> Path:
    _prepare_tss_train_freeze_stage(lineage_root)
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )
    build_tss_test_evidence_from_train_freeze(lineage_root)
    return stage_dir / "author" / "formal"


def _build_tss_backtest_ready(lineage_root: Path) -> Path:
    _prepare_tss_test_evidence_stage(lineage_root)
    stage_dir = lineage_root / "06_tss_backtest_ready"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_backtest_ready_freeze_draft.yaml",
        _tss_backtest_ready_draft(confirmed=True),
    )
    build_tss_backtest_ready_from_test_evidence(lineage_root)
    return stage_dir / "author" / "formal"


def _build_tss_holdout_validation(lineage_root: Path) -> Path:
    _prepare_tss_backtest_ready_stage(lineage_root)
    stage_dir = lineage_root / "07_tss_holdout_validation"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_holdout_validation_freeze_draft.yaml",
        _tss_holdout_validation_draft(confirmed=True),
    )
    build_tss_holdout_validation_from_backtest_ready(lineage_root)
    return stage_dir / "author" / "formal"


TSS_STAGE_META: dict[str, dict[str, Any]] = {
    "tss_data_ready": {
        "stage_dir": "02_tss_data_ready/author/formal",
        "primary_artifact": "time_index_manifest.json",
        "author_skill": "qros-tss-data-ready-author",
        "review_skill": "qros-tss-data-ready-review",
        "sop_path": Path("docs/sop/main-flow/02_tss_data_ready_sop_cn.md"),
        "builder": _build_tss_data_ready,
    },
    "tss_signal_ready": {
        "stage_dir": "03_tss_signal_ready/author/formal",
        "primary_artifact": "signal_manifest.yaml",
        "author_skill": "qros-tss-signal-ready-author",
        "review_skill": "qros-tss-signal-ready-review",
        "sop_path": Path("docs/sop/main-flow/03_tss_signal_ready_sop_cn.md"),
        "builder": _build_tss_signal_ready,
    },
    "tss_train_freeze": {
        "stage_dir": "04_tss_train_freeze/author/formal",
        "primary_artifact": "tss_train_freeze.yaml",
        "author_skill": "qros-tss-train-freeze-author",
        "review_skill": "qros-tss-train-freeze-review",
        "sop_path": Path("docs/sop/main-flow/04_tss_train_freeze_sop_cn.md"),
        "builder": _build_tss_train_freeze,
    },
    "tss_test_evidence": {
        "stage_dir": "05_tss_test_evidence/author/formal",
        "primary_artifact": "signal_performance_summary.json",
        "author_skill": "qros-tss-test-evidence-author",
        "review_skill": "qros-tss-test-evidence-review",
        "sop_path": Path("docs/sop/main-flow/05_tss_test_evidence_sop_cn.md"),
        "builder": _build_tss_test_evidence,
    },
    "tss_backtest_ready": {
        "stage_dir": "06_tss_backtest_ready/author/formal",
        "primary_artifact": "strategy_contract.yaml",
        "author_skill": "qros-tss-backtest-ready-author",
        "review_skill": "qros-tss-backtest-ready-review",
        "sop_path": Path("docs/sop/main-flow/06_tss_backtest_ready_sop_cn.md"),
        "builder": _build_tss_backtest_ready,
    },
    "tss_holdout_validation": {
        "stage_dir": "07_tss_holdout_validation/author/formal",
        "primary_artifact": "tss_holdout_run_manifest.json",
        "author_skill": "qros-tss-holdout-validation-author",
        "review_skill": "qros-tss-holdout-validation-review",
        "sop_path": Path("docs/sop/main-flow/07_tss_holdout_validation_sop_cn.md"),
        "builder": _build_tss_holdout_validation,
    },
}

TSS_TEST_EVIDENCE_PREFLIGHT_TERMS = (
    "split_threshold_attestation.yaml",
    "selected_variant_membership_proof.csv",
    "upstream_binding_digest_ledger.yaml",
    "TSS-TEST-SEMANTIC-001",
)


def _valid_data_implementation_declaration() -> dict[str, Any]:
    return {
        "engine": "polars",
        "input_strategy": "parquet_lazy_scan",
        "compute_strategy": "expression_vectorized",
        "output_strategy": "parquet_columnar",
        "disallowed_main_path": [
            "pandas",
            "row_wise_loop",
            "per_symbol_full_scan_loop",
            "repeated_full_scan_without_shared_intermediate",
        ],
    }


def _add_data_implementation_declaration(program_dir: Path) -> None:
    manifest_path = program_dir / "stage_program.yaml"
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    payload["data_implementation_contract"] = _valid_data_implementation_declaration()
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def assert_tss_artifact_contract_is_stage_specific(stage: str) -> None:
    meta = TSS_STAGE_META[stage]
    contract = load_artifact_contract(stage)

    assert contract["stage"] == stage
    assert contract["stage_dir"] == meta["stage_dir"]
    assert contract["unknown_machine_top_level_fields"] == "forbid"
    assert meta["primary_artifact"] in contract["artifacts"]


def assert_tss_generated_artifacts_match_contract(stage: str, tmp_path: Path) -> None:
    formal_dir = _build_formal_dir(stage, tmp_path)
    contract = load_artifact_contract(stage)

    assert {item.name for item in formal_dir.iterdir()} == set(contract["artifacts"])
    result = validate_stage_artifacts(formal_dir, contract)
    assert result.valid is True, result.errors


def assert_tss_review_preflight_is_contract_wired(stage: str, tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "tss_case"
    stage_dir = lineage_root / str(TSS_STAGE_META[stage]["stage_dir"]).split("/", 1)[0]
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    if stage == "tss_data_ready":
        _add_data_implementation_declaration(ensure_stage_program(lineage_root, "tss_data_ready"))

    payload = run_review_preflight(
        explicit_context={
            "stage": stage,
            "stage_dir": str(stage_dir),
            "lineage_root": str(lineage_root),
            "author_formal_dir": str(formal_dir),
            "lineage_id": lineage_root.name,
        }
    )

    findings = payload["content_findings"] + payload["upstream_binding_findings"]
    assert payload["stage"] == stage
    assert payload["status"] == "FAIL"
    assert any("ARTIFACT-CONTRACT-001" in item or "Missing required output" in item for item in findings)


def assert_tss_skill_guidance_is_contract_first(stage: str) -> None:
    meta = TSS_STAGE_META[stage]
    author = skill_text(str(meta["author_skill"]))
    review = skill_text(str(meta["review_skill"]))
    contract_path = f"contracts/artifacts/{stage}_artifacts.yaml"

    assert contract_path in author
    assert contract_path in review
    assert f"qros-validate-stage --stage {stage}" in author
    assert f"qros-validate-stage --stage {stage}" in review
    assert "research_route = time_series_signal" in author
    assert "不是横截面排序" in author
    assert "qros-review-cycle prepare" in review
    assert "qros-factor-diagnostics" not in author + review
    if stage == "tss_data_ready":
        for term in (
            "data_implementation_contract",
            "Polars",
            "pl.scan_parquet",
            "pandas",
            "逐行循环",
            "逐 symbol",
            "不得询问用户技术实现细节",
            "time index",
            "quality flags",
            "split adequacy",
            "as-of feature base",
            "时间轴主路径计算",
            "stage_program.yaml",
            "门禁不通过时停在 author lane 修复程序，不得进入 review",
            "门禁通过后才生成正式 `02_tss_data_ready/author/formal` 下的 required outputs",
            "Python loop 只能用于 manifest、artifact catalog、field dictionary、输出文件枚举和小型 metadata/report 控制流，不能承担时间轴主路径计算。",
            "manifest",
            "artifact catalog",
            "field dictionary",
            "输出文件枚举",
            "metadata/report",
        ):
            assert term in author
    if stage == "tss_test_evidence":
        for term in TSS_TEST_EVIDENCE_PREFLIGHT_TERMS:
            assert term in author
            assert term in review


def assert_tss_sop_documents_contract_first_usage(stage: str) -> None:
    meta = TSS_STAGE_META[stage]
    content = Path(meta["sop_path"]).read_text(encoding="utf-8")

    assert f"contracts/artifacts/{stage}_artifacts.yaml" in content
    assert f"qros-validate-stage --stage {stage}" in content
    assert "research_route = time_series_signal" in content
    assert "单个资产用自己的历史预测自己的未来路径/方向" in content
    assert "不是横截面排序" in content
    if stage == "tss_test_evidence":
        for term in TSS_TEST_EVIDENCE_PREFLIGHT_TERMS:
            assert term in content


def _build_formal_dir(stage: str, tmp_path: Path) -> Path:
    builder = TSS_STAGE_META[stage]["builder"]
    assert isinstance(builder, Callable)
    return builder(tmp_path / "outputs" / "tss_case")


def load_machine_payload(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8"))
