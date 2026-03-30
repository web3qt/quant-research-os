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
    "promotion": "promotion_decision",
    "promotion_decision": "promotion_decision",
    "07_promotion": "promotion_decision",
    "08_promotion": "promotion_decision",
    "shadow": "shadow_admission",
    "shadow_admission": "shadow_admission",
    "08_shadow": "shadow_admission",
    "09_shadow": "shadow_admission",
    "canary_prod": "canary_production",
    "canary_production": "canary_production",
    "09_canary_prod": "canary_production",
    "10_canary_prod": "canary_production",
}


def _normalize_stage_name(name: str) -> str | None:
    return STAGE_ALIASES.get(name)


def infer_review_context(path: Path) -> dict[str, Any]:
    candidate = path.resolve()

    for current in (candidate, *candidate.parents):
        if current.parent.parent.name == "outputs":
            normalized_stage = _normalize_stage_name(current.name)
            if normalized_stage is None:
                raise ValueError(f"Could not infer review context from path: {path}")
            return {
                "lineage_id": current.parent.name,
                "stage": normalized_stage,
                "stage_dir": current,
                "lineage_root": current.parent,
            }

    raise ValueError(f"Could not infer review context from path: {path}")
