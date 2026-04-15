from __future__ import annotations

import json
from pathlib import Path
import subprocess
import textwrap
from typing import Any

import yaml

from runtime.tools.review_skillgen.context_inference import build_stage_context


DATA_READY_FREEZE_DRAFT_FILE = "data_ready_freeze_draft.yaml"
DATA_READY_REBUILD_SCRIPT = "rebuild_data_ready.py"
DATA_READY_FREEZE_GROUP_ORDER = [
    "extraction_contract",
    "quality_semantics",
    "universe_admission",
    "shared_derived_layer",
    "delivery_contract",
]


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git_revision(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _render_rebuild_script(
    *,
    stage_label: str,
    module_relpath: str,
    function_name: str,
    runtime_root_hint: str,
) -> str:
    return textwrap.dedent(
        """\
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import importlib.util
        import os
        from pathlib import Path
        import sys


        STAGE_LABEL = {stage_label}
        MODULE_REL_PATH = {module_relpath}
        FUNCTION_NAME = {function_name}
        RUNTIME_ROOT_HINT = {runtime_root_hint}


        def _candidate_runtime_roots(explicit_runtime_root: str | None) -> list[Path]:
            stage_dir = Path(__file__).resolve().parent
            lineage_root = stage_dir.parent
            project_root = lineage_root.parent.parent
            raw_candidates = [
                explicit_runtime_root,
                os.environ.get("QROS_RUNTIME_ROOT"),
                str(project_root / ".qros"),
                str(Path.home() / ".qros"),
                str(Path.home() / ".codex" / "qros"),
                RUNTIME_ROOT_HINT,
            ]
            candidates: list[Path] = []
            for raw in raw_candidates:
                if not raw:
                    continue
                candidate = Path(raw).expanduser()
                if candidate not in candidates:
                    candidates.append(candidate)
            return candidates


        def _resolve_module_path(explicit_runtime_root: str | None) -> Path:
            for runtime_root in _candidate_runtime_roots(explicit_runtime_root):
                module_path = runtime_root / MODULE_REL_PATH
                if module_path.exists():
                    return module_path
            raise SystemExit(
                "Unable to locate QROS runtime module for "
                + STAGE_LABEL
                + ". Pass --runtime-root or set QROS_RUNTIME_ROOT."
            )


        def _load_build_function(module_path: Path):
            spec = importlib.util.spec_from_file_location("_qros_stage_runtime", module_path)
            if spec is None or spec.loader is None:
                raise SystemExit("Unable to load runtime module: " + str(module_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, FUNCTION_NAME)


        def main() -> int:
            parser = argparse.ArgumentParser(
                description="Rebuild frozen " + STAGE_LABEL + " artifacts using the recorded QROS runtime."
            )
            parser.add_argument("--lineage-root", type=Path, default=Path(__file__).resolve().parent.parent)
            parser.add_argument("--runtime-root", type=Path, default=None)
            args = parser.parse_args()

            module_path = _resolve_module_path(str(args.runtime_root) if args.runtime_root else None)
            build_fn = _load_build_function(module_path)
            build_fn(args.lineage_root.resolve())
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """
    ).format(
        stage_label=repr(stage_label),
        module_relpath=repr(module_relpath),
        function_name=repr(function_name),
        runtime_root_hint=repr(runtime_root_hint),
    )


def _blank_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "extraction_contract": {
                "confirmed": False,
                "draft": {
                    "data_source": "",
                    "time_boundary": "",
                    "primary_time_key": "",
                    "bar_size": "",
                },
                "missing_items": [],
            },
            "quality_semantics": {
                "confirmed": False,
                "draft": {
                    "missing_policy": "",
                    "stale_policy": "",
                    "bad_price_policy": "",
                    "outlier_policy": "",
                    "dedupe_rule": "",
                },
                "missing_items": [],
            },
            "universe_admission": {
                "confirmed": False,
                "draft": {
                    "benchmark_symbol": "",
                    "coverage_floor": "",
                    "admission_rule": "",
                    "exclusion_reporting": "",
                },
                "missing_items": [],
            },
            "shared_derived_layer": {
                "confirmed": False,
                "draft": {
                    "shared_outputs": [],
                    "layer_boundary_note": "",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": False,
                "draft": {
                    "machine_artifacts": [],
                    "consumer_stage": "",
                    "frozen_inputs_note": "",
                },
                "missing_items": [],
            },
        }
    }


def scaffold_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    data_ready_dir = lineage_root / "02_data_ready"
    stage_context = build_stage_context(data_ready_dir)
    draft_dir = stage_context["author_draft_dir"]
    draft_dir.mkdir(parents=True, exist_ok=True)

    draft_path = draft_dir / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_data_ready_freeze_draft())
    return data_ready_dir


def build_data_ready_from_mandate(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    mandate_dir = lineage_root / "01_mandate"
    data_ready_dir = scaffold_data_ready(lineage_root)
    mandate_formal_dir = build_stage_context(mandate_dir)["author_formal_dir"]
    data_ready_context = build_stage_context(data_ready_dir)
    data_ready_formal_dir = data_ready_context["author_formal_dir"]
    data_ready_formal_dir.mkdir(parents=True, exist_ok=True)

    missing_mandate = [
        name
        for name in [
            "mandate.md",
            "research_scope.md",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (mandate_formal_dir / name).exists()
    ]
    if missing_mandate:
        raise ValueError(f"mandate artifacts missing before data_ready build: {', '.join(missing_mandate)}")

    freeze_groups = _require_confirmed_freeze_groups(data_ready_dir)
    extraction_contract = freeze_groups["extraction_contract"]["draft"]
    quality_semantics = freeze_groups["quality_semantics"]["draft"]
    universe_admission = freeze_groups["universe_admission"]["draft"]
    shared_derived_layer = freeze_groups["shared_derived_layer"]["draft"]
    delivery_contract = freeze_groups["delivery_contract"]["draft"]

    data_source = _required_draft_value(extraction_contract, "data_source")
    time_boundary = _required_draft_value(extraction_contract, "time_boundary")
    primary_time_key = _required_draft_value(extraction_contract, "primary_time_key")
    bar_size = _required_draft_value(extraction_contract, "bar_size")
    missing_policy = _required_draft_value(quality_semantics, "missing_policy")
    stale_policy = _required_draft_value(quality_semantics, "stale_policy")
    bad_price_policy = _required_draft_value(quality_semantics, "bad_price_policy")
    outlier_policy = _required_draft_value(quality_semantics, "outlier_policy")
    dedupe_rule = _required_draft_value(quality_semantics, "dedupe_rule")
    benchmark_symbol = _required_draft_value(universe_admission, "benchmark_symbol")
    coverage_floor = _required_draft_value(universe_admission, "coverage_floor")
    admission_rule = _required_draft_value(universe_admission, "admission_rule")
    exclusion_reporting = _required_draft_value(universe_admission, "exclusion_reporting")
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_inputs_note = _required_draft_value(delivery_contract, "frozen_inputs_note")

    shared_outputs = _string_list(shared_derived_layer.get("shared_outputs", []))
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    layer_boundary_note = _required_draft_value(shared_derived_layer, "layer_boundary_note")
    runtime_root = _runtime_root()
    runtime_git_revision = _git_revision(runtime_root)

    for name in [
        "aligned_bars",
        "rolling_stats",
        "pair_stats",
        "benchmark_residual",
        "topic_basket_state",
    ]:
        (data_ready_formal_dir / name).mkdir(exist_ok=True)

    (data_ready_formal_dir / "qc_report.parquet").write_text(
        "first-wave data_ready 骨架的占位 qc 产物\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "stage": "data_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "mandate",
                "data_source": data_source,
                "time_boundary": time_boundary,
                "primary_time_key": primary_time_key,
                "bar_size": bar_size,
                "shared_outputs": shared_outputs,
                "machine_artifacts": machine_artifacts,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "validation_report.md").write_text(
        "\n".join(
            [
                "# 验证报告",
                "",
                "- 第一版产物先冻结 data_ready 合同与阶段骨架。",
                f"- 基准覆盖锚定在 `{benchmark_symbol}`。",
                f"- 覆盖率下限: {coverage_floor}",
                f"- 准入规则: {admission_rule}",
                "",
                "## 质量语义",
                "",
                f"- 缺失: {missing_policy}",
                f"- Stale: {stale_policy}",
                f"- 坏价: {bad_price_policy}",
                f"- 异常值: {outlier_policy}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "data_contract.md").write_text(
        "\n".join(
            [
                "# 数据合同",
                "",
                f"- 数据来源: {data_source}",
                f"- 时间边界: {time_boundary}",
                f"- 主时间键: {primary_time_key}",
                f"- Bar 粒度: {bar_size}",
                f"- 基准符号: {benchmark_symbol}",
                f"- 共享派生输出: {', '.join(shared_outputs)}",
                f"- 分层边界: {layer_boundary_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "dedupe_rule.md").write_text(
        f"# 去重规则\n\n- {dedupe_rule}\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "universe_summary.md").write_text(
        "\n".join(
            [
                "# Universe 摘要",
                "",
                f"- 基准符号: {benchmark_symbol}",
                f"- 覆盖率下限: {coverage_floor}",
                f"- 准入规则: {admission_rule}",
                f"- 排除项记录规则: {exclusion_reporting}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "universe_exclusions.csv").write_text(
        "symbol,reason\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "universe_exclusions.md").write_text(
        "\n".join(
            [
                "# Universe 排除项",
                "",
                "- 第一版骨架暂未记录具体排除项。",
                f"- 记录规则: {exclusion_reporting}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "data_ready_gate_decision.md").write_text(
        "\n".join(
            [
                "# Data Ready Gate Decision",
                "",
                "- 在 review findings 和 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结输入说明: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rebuild_script_path = data_ready_formal_dir / DATA_READY_REBUILD_SCRIPT
    rebuild_script_path.write_text(
        _render_rebuild_script(
            stage_label="data_ready",
            module_relpath="tools/data_ready_runtime.py",
            function_name="build_data_ready_from_mandate",
            runtime_root_hint=str(runtime_root),
        ),
        encoding="utf-8",
    )
    rebuild_script_path.chmod(0o755)
    (data_ready_formal_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "data_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "mandate",
                "data_source": data_source,
                "time_boundary": time_boundary,
                "primary_time_key": primary_time_key,
                "bar_size": bar_size,
                "benchmark_symbol": benchmark_symbol,
                "coverage_floor": coverage_floor,
                "machine_artifacts": machine_artifacts,
                "shared_outputs": shared_outputs,
                "consumer_stage": consumer_stage,
                "frozen_inputs_note": frozen_inputs_note,
                "runtime_root_hint": str(runtime_root),
                "runtime_module": "tools/data_ready_runtime.py",
                "runtime_function": "build_data_ready_from_mandate",
                "source_git_revision": runtime_git_revision,
                "program_artifacts": [DATA_READY_REBUILD_SCRIPT],
                "replay_working_directory": data_ready_dir.name,
                "replay_command": f"python3 {DATA_READY_REBUILD_SCRIPT}",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- aligned_bars/",
                "- rolling_stats/",
                "- pair_stats/",
                "- benchmark_residual/",
                "- topic_basket_state/",
                "- qc_report.parquet",
                "- dataset_manifest.json",
                "- validation_report.md",
                "- data_contract.md",
                "- dedupe_rule.md",
                "- universe_summary.md",
                "- universe_exclusions.csv",
                "- universe_exclusions.md",
                "- data_ready_gate_decision.md",
                "- run_manifest.json",
                f"- {DATA_READY_REBUILD_SCRIPT}",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (data_ready_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `data_source`: 冻结到 data_ready 的上游数据来源，当前为 `{data_source}`。",
                f"- `primary_time_key`: 冻结的主时间键，当前为 `{primary_time_key}`。",
                f"- `bar_size`: 继承到 data_ready 的固定粒度，当前为 `{bar_size}`。",
                f"- `missing_policy`: {missing_policy}",
                f"- `stale_policy`: {stale_policy}",
                f"- `bad_price_policy`: {bad_price_policy}",
                f"- `outlier_policy`: {outlier_policy}",
                f"- `benchmark_symbol`: 基准符号，当前为 `{benchmark_symbol}`。",
                f"- `shared_outputs`: 共享派生输出集合，当前为 `{shared_outputs}`。",
                f"- `frozen_inputs_note`: {frozen_inputs_note}",
                "- `runtime_root_hint`: `run_manifest.json` 中记录的 runtime 根目录提示。",
                "- `runtime_module`: `run_manifest.json` 中记录的正式构建模块路径。",
                "- `runtime_function`: `run_manifest.json` 中记录的正式构建函数名。",
                "- `program_artifacts`: `run_manifest.json` 中登记的 stage-local 程序快照。",
                "- `replay_command`: `run_manifest.json` 中登记的重放命令。",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return data_ready_dir


def _require_confirmed_freeze_groups(data_ready_dir: Path) -> dict[str, Any]:
    draft_path = build_stage_context(data_ready_dir)["author_draft_dir"] / DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        raise ValueError(f"{DATA_READY_FREEZE_DRAFT_FILE} is required before data_ready build")

    draft_payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = draft_payload.get("groups", {})
    missing_groups = [
        name for name in DATA_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))
    ]
    if missing_groups:
        raise ValueError(
            f"{DATA_READY_FREEZE_DRAFT_FILE} has unconfirmed groups: {', '.join(missing_groups)}"
        )
    return groups


def _required_draft_value(group_payload: dict[str, Any], key: str) -> str:
    value = group_payload.get(key, "")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"confirmed data_ready inputs missing: {key}")
    return normalized


def _string_list(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, list):
        return []
    return [str(item) for item in raw_value if str(item).strip()]
