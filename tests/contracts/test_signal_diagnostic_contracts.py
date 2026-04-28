from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


METRIC_LIBRARY_PATH = Path("contracts/diagnostics/tss_metric_library.yaml")
STAGE_PROFILES_PATH = Path("contracts/diagnostics/tss_stage_diagnostic_profiles.yaml")
SUPPORTED_TSS_STAGES = {
    "tss_data_ready",
    "tss_signal_ready",
    "tss_train_freeze",
    "tss_test_evidence",
    "tss_backtest_ready",
    "tss_holdout_validation",
}
CORE_TSS_METRICS = {
    "mean_forward_return",
    "hit_rate",
    "base_rate_uplift",
    "signal_frequency",
    "mfe_mae",
}
REQUIRED_METRIC_FIELDS = {
    "display_name",
    "category",
    "meaning",
    "expected_direction",
    "required_inputs",
    "v1_observation_mode",
}
ALLOWED_OBSERVATION_MODES = {"read_existing", "derive_from_existing", "gap_detect_only"}


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_tss_metric_library_exists_and_has_core_metrics() -> None:
    assert METRIC_LIBRARY_PATH.exists()
    library = _load_yaml(METRIC_LIBRARY_PATH)

    assert library["schema_id"] == "tss-metric-library-v1"
    assert library["schema_version"] == "v1"
    metrics = library["metrics"]
    assert CORE_TSS_METRICS <= set(metrics)

    for metric_id, metric in metrics.items():
        assert isinstance(metric_id, str)
        assert REQUIRED_METRIC_FIELDS <= set(metric)
        assert metric["v1_observation_mode"] in ALLOWED_OBSERVATION_MODES
        assert isinstance(metric["required_inputs"], list)
        assert metric["meaning"].strip()


def test_tss_stage_diagnostic_profiles_cover_all_tss_stages() -> None:
    assert STAGE_PROFILES_PATH.exists()
    profiles_doc = _load_yaml(STAGE_PROFILES_PATH)

    assert profiles_doc["schema_id"] == "tss-stage-diagnostic-profiles-v1"
    assert profiles_doc["schema_version"] == "v1"
    profiles = profiles_doc["profiles"]
    assert set(profiles) == SUPPORTED_TSS_STAGES

    for stage, profile in profiles.items():
        dimensions = profile["health_dimensions"]
        assert isinstance(dimensions, dict), stage
        assert dimensions, stage
        for dimension_name, dimension in dimensions.items():
            assert isinstance(dimension_name, str)
            assert dimension.get("required_metrics") or dimension.get("recommended_metrics")


def test_tss_stage_profiles_only_reference_known_metrics() -> None:
    metrics = set(_load_yaml(METRIC_LIBRARY_PATH)["metrics"])
    profiles = _load_yaml(STAGE_PROFILES_PATH)["profiles"]

    for stage, profile in profiles.items():
        for dimension_name, dimension in profile["health_dimensions"].items():
            referenced = set(dimension.get("required_metrics", [])) | set(
                dimension.get("recommended_metrics", [])
            )
            unknown = sorted(referenced - metrics)
            assert not unknown, f"{stage}.{dimension_name} references unknown metrics: {unknown}"
