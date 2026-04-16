from __future__ import annotations

from pathlib import Path
from typing import Any


STAGE_ALIASES = {
    "mandate": "mandate",
    "00_mandate": "mandate",
    "01_mandate": "mandate",
    "data_ready": "data_ready",
    "01_data_ready": "data_ready",
    "02_data_ready": "data_ready",
    "csf_data_ready": "csf_data_ready",
    "02_csf_data_ready": "csf_data_ready",
    "signal_ready": "signal_ready",
    "02_signal_ready": "signal_ready",
    "03_signal_ready": "signal_ready",
    "csf_signal_ready": "csf_signal_ready",
    "03_csf_signal_ready": "csf_signal_ready",
    "train_calibration": "train_calibration",
    "train_freeze": "train_calibration",
    "03_train_calibration": "train_calibration",
    "03_train_freeze": "train_calibration",
    "04_train_calibration": "train_calibration",
    "04_train_freeze": "train_calibration",
    "csf_train_freeze": "csf_train_freeze",
    "04_csf_train_freeze": "csf_train_freeze",
    "test_evidence": "test_evidence",
    "04_test_evidence": "test_evidence",
    "05_test_evidence": "test_evidence",
    "csf_test_evidence": "csf_test_evidence",
    "05_csf_test_evidence": "csf_test_evidence",
    "backtest": "backtest_ready",
    "backtest_ready": "backtest_ready",
    "05_backtest": "backtest_ready",
    "06_backtest": "backtest_ready",
    "csf_backtest_ready": "csf_backtest_ready",
    "06_csf_backtest_ready": "csf_backtest_ready",
    "holdout": "holdout_validation",
    "holdout_validation": "holdout_validation",
    "06_holdout": "holdout_validation",
    "07_holdout": "holdout_validation",
    "csf_holdout_validation": "csf_holdout_validation",
    "07_csf_holdout_validation": "csf_holdout_validation",
}

REVIEW_SUBDIRS = {"request", "result", "closure"}


def _normalize_stage_name(name: str) -> str | None:
    return STAGE_ALIASES.get(name)


def build_stage_context(stage_root: Path) -> dict[str, Any]:
    stage_root = stage_root.resolve()
    normalized_stage = _normalize_stage_name(stage_root.name)
    if normalized_stage is None:
        raise ValueError(f"Could not infer review context from stage root: {stage_root}")

    lineage_root = stage_root.parent
    author_root = stage_root / "author"
    review_root = stage_root / "review"
    return {
        "lineage_id": lineage_root.name,
        "stage": normalized_stage,
        "stage_dir": stage_root,
        "stage_root": stage_root,
        "lineage_root": lineage_root,
        "author_dir": author_root,
        "author_draft_dir": author_root / "draft",
        "author_formal_dir": author_root / "formal",
        "review_dir": review_root,
        "review_request_dir": review_root / "request",
        "review_result_dir": review_root / "result",
        "review_closure_dir": review_root / "closure",
    }


def infer_review_context(path: Path) -> dict[str, Any]:
    candidate = path.resolve()

    for current in (candidate, *candidate.parents):
        if current.name in REVIEW_SUBDIRS and current.parent.name == "review":
            stage_root = current.parent.parent
            if stage_root.parent.name != "outputs":
                continue
            return build_stage_context(stage_root)

        if current.parent.parent.name == "outputs":
            return build_stage_context(current)

    raise ValueError(f"Could not infer review context from path: {path}")
