from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TIME_SERIES_SIGNAL_ROUTE = "time_series_signal"
SIGNAL_READY_CONFIRMATION_STAGE = "signal_ready_confirmation_pending"

DATA_READY_CORE_DIRS = (
    "aligned_bars",
    "rolling_stats",
    "pair_stats",
    "benchmark_residual",
    "topic_basket_state",
)
DATA_READY_SUPPORTING_FILES = (
    "dataset_manifest.json",
    "data_contract.md",
    "dedupe_rule.md",
    "artifact_catalog.md",
    "field_dictionary.md",
)
DATA_READY_QC_FILES = (
    "qc_report.parquet",
    "validation_report.md",
    "universe_exclusions.csv",
    "universe_exclusions.md",
    "data_ready_gate_decision.md",
)
DATA_READY_KEY_FILES = (
    "dataset_manifest.json",
    "validation_report.md",
    "data_contract.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "rebuild_data_ready.py",
)


@dataclass(frozen=True)
class ReflectionSection:
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class DataReadyReflection:
    title: str
    sections: tuple[ReflectionSection, ...]

    def to_payload(
        self,
        *,
        lineage_root: Path,
        current_stage: str,
        current_route: str | None,
    ) -> dict[str, object]:
        return {
            "stage_id": "data_ready",
            "lineage_id": lineage_root.name,
            "lineage_root": str(lineage_root),
            "stage_directory": f"outputs/{lineage_root.name}/02_data_ready",
            "session_stage": current_stage,
            "current_route": current_route,
            "title": self.title,
            "sections": [
                {
                    "title": section.title,
                    "lines": list(section.lines),
                }
                for section in self.sections
            ],
        }


def build_data_ready_reflection(
    *,
    lineage_root: Path,
    current_stage: str,
    current_route: str | None,
) -> DataReadyReflection | None:
    if current_stage != SIGNAL_READY_CONFIRMATION_STAGE:
        return None
    if current_route != TIME_SERIES_SIGNAL_ROUTE:
        return None

    stage_dir = lineage_root / "02_data_ready"
    if not stage_dir.exists():
        return None

    return _build_data_ready_reflection_from_stage_dir(lineage_root=lineage_root, stage_dir=stage_dir)


# HTML proof-of-concept 仍然沿用当前 reflection 的生命周期与 route 边界。
def build_data_ready_reflection_payload(
    *,
    lineage_root: Path,
    current_stage: str = SIGNAL_READY_CONFIRMATION_STAGE,
    current_route: str | None = TIME_SERIES_SIGNAL_ROUTE,
) -> dict[str, object] | None:
    reflection = build_data_ready_reflection(
        lineage_root=lineage_root,
        current_stage=current_stage,
        current_route=current_route,
    )
    if reflection is None:
        return None
    return reflection.to_payload(
        lineage_root=lineage_root,
        current_stage=current_stage,
        current_route=current_route,
    )


def reflection_payload_to_dict(payload: dict[str, object]) -> dict[str, object]:
    # 明确复制一份稳定结构，避免 exporter 直接依赖调用侧对象引用或未来 dataclass 形状漂移。
    return {
        "stage_id": payload["stage_id"],
        "lineage_id": payload["lineage_id"],
        "lineage_root": payload["lineage_root"],
        "stage_directory": payload["stage_directory"],
        "session_stage": payload["session_stage"],
        "current_route": payload["current_route"],
        "title": payload["title"],
        "sections": [
            {
                "title": section["title"],
                "lines": list(section["lines"]),
            }
            for section in payload["sections"]
        ],
    }


def render_reflection_lines(reflection: DataReadyReflection) -> list[str]:
    lines = [f"{reflection.title}:"]
    for section in reflection.sections:
        lines.append(f"- {section.title}:")
        for item in section.lines:
            lines.append(f"  - {item}")
    return lines


def _build_data_ready_reflection_from_stage_dir(*, lineage_root: Path, stage_dir: Path) -> DataReadyReflection:
    coverage_section = ReflectionSection(
        title="Data Coverage And Gaps",
        lines=_coverage_lines(stage_dir),
    )
    qc_section = ReflectionSection(
        title="QC / Anomaly Summary",
        lines=_qc_lines(stage_dir),
    )
    artifact_section = ReflectionSection(
        title="Artifact Directory And Key Files",
        lines=_artifact_lines(lineage_root, stage_dir),
    )
    return DataReadyReflection(
        title="Data Ready Reflection",
        sections=(coverage_section, qc_section, artifact_section),
    )


def _coverage_lines(stage_dir: Path) -> tuple[str, ...]:
    present_core, missing_core = _present_and_missing(stage_dir, DATA_READY_CORE_DIRS)
    present_supporting, missing_supporting = _present_and_missing(stage_dir, DATA_READY_SUPPORTING_FILES)

    lines = [
        f"core data layers present: {len(present_core)}/{len(DATA_READY_CORE_DIRS)}",
        f"missing core data layers: {_format_names(missing_core)}",
        f"supporting contract files present: {len(present_supporting)}/{len(DATA_READY_SUPPORTING_FILES)}",
        f"missing supporting contract files: {_format_names(missing_supporting)}",
    ]
    if missing_core or missing_supporting:
        lines.append(
            "question: what justifies moving into signal work before the missing coverage artifacts are explained?"
        )
    else:
        lines.append(
            "question: do the available coverage artifacts support the stated admission rule and coverage floor?"
        )
    return tuple(lines)


def _qc_lines(stage_dir: Path) -> tuple[str, ...]:
    lines = []
    for artifact in DATA_READY_QC_FILES:
        state = "available" if (stage_dir / artifact).exists() else "missing"
        lines.append(f"{artifact}: {state}")

    _, missing_qc = _present_and_missing(stage_dir, DATA_READY_QC_FILES)
    if missing_qc:
        lines.append(
            "question: which missing QC artifacts must be reviewed before the stage can be trusted?"
        )
    else:
        lines.append(
            "question: do the QC evidence and exclusion artifacts explain any symbols removed before signal work continues?"
        )
    return tuple(lines)


def _artifact_lines(lineage_root: Path, stage_dir: Path) -> tuple[str, ...]:
    present_key, missing_key = _present_and_missing(stage_dir, DATA_READY_KEY_FILES)
    stage_dir_label = f"outputs/{lineage_root.name}/02_data_ready"
    return (
        f"stage directory: {stage_dir_label}",
        f"key files present: {_format_names(present_key)}",
        f"missing key files: {_format_names(missing_key)}",
    )


def _present_and_missing(stage_dir: Path, names: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    present: list[str] = []
    missing: list[str] = []
    for name in names:
        if (stage_dir / name).exists():
            present.append(name)
        else:
            missing.append(name)
    return tuple(present), tuple(missing)


def _format_names(names: tuple[str, ...]) -> str:
    if not names:
        return "none"
    return ", ".join(names)
