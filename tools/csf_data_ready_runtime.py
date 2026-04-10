from __future__ import annotations

import json
from pathlib import Path
import subprocess
import textwrap
from typing import Any

import yaml

from tools.review_skillgen.context_inference import build_stage_context


CSF_DATA_READY_FREEZE_DRAFT_FILE = "csf_data_ready_freeze_draft.yaml"
CSF_DATA_READY_REBUILD_SCRIPT = "rebuild_csf_data_ready.py"
CSF_DATA_READY_FREEZE_GROUP_ORDER = [
    "panel_contract",
    "taxonomy_contract",
    "eligibility_contract",
    "shared_feature_base",
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


def _blank_csf_data_ready_freeze_draft() -> dict[str, Any]:
    return {
        "groups": {
            "panel_contract": {
                "confirmed": False,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "cross_section_time_key": "",
                    "asset_key": "",
                    "universe_membership_rule": "",
                },
                "missing_items": [],
            },
            "taxonomy_contract": {
                "confirmed": False,
                "draft": {
                    "group_taxonomy_reference": "",
                    "group_mapping_rule": "",
                    "taxonomy_note": "",
                },
                "missing_items": [],
            },
            "eligibility_contract": {
                "confirmed": False,
                "draft": {
                    "eligibility_base_rule": "",
                    "coverage_floor_rule": "",
                    "mask_audit_note": "",
                },
                "missing_items": [],
            },
            "shared_feature_base": {
                "confirmed": False,
                "draft": {
                    "shared_feature_outputs": [],
                    "shared_feature_note": "",
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


def scaffold_csf_data_ready(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    stage_dir = lineage_root / "02_csf_data_ready"
    draft_dir = build_stage_context(stage_dir)["author_draft_dir"]
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / CSF_DATA_READY_FREEZE_DRAFT_FILE
    if not draft_path.exists():
        _dump_yaml(draft_path, _blank_csf_data_ready_freeze_draft())
    return stage_dir


def build_csf_data_ready_from_mandate(lineage_root: Path) -> Path:
    lineage_root = lineage_root.resolve()
    mandate_dir = lineage_root / "01_mandate"
    stage_dir = scaffold_csf_data_ready(lineage_root)
    mandate_formal_dir = build_stage_context(mandate_dir)["author_formal_dir"]
    stage_formal_dir = build_stage_context(stage_dir)["author_formal_dir"]
    stage_formal_dir.mkdir(parents=True, exist_ok=True)

    missing = [
        name
        for name in [
            "mandate.md",
            "research_scope.md",
            "research_route.yaml",
            "time_split.json",
            "parameter_grid.yaml",
            "run_config.toml",
            "artifact_catalog.md",
            "field_dictionary.md",
        ]
        if not (mandate_formal_dir / name).exists()
    ]
    if missing:
        raise ValueError(f"mandate artifacts missing before csf_data_ready build: {', '.join(missing)}")

    route_payload = yaml.safe_load((mandate_formal_dir / "research_route.yaml").read_text(encoding="utf-8")) or {}
    if str(route_payload.get("research_route", "")).strip() != "cross_sectional_factor":
        raise ValueError("research_route must be cross_sectional_factor before csf_data_ready build")

    groups = _require_confirmed_freeze_groups(stage_dir)
    panel_contract = groups["panel_contract"]["draft"]
    taxonomy_contract = groups["taxonomy_contract"]["draft"]
    eligibility_contract = groups["eligibility_contract"]["draft"]
    shared_feature_base = groups["shared_feature_base"]["draft"]
    delivery_contract = groups["delivery_contract"]["draft"]

    panel_primary_key = _string_list(panel_contract.get("panel_primary_key", []))
    cross_section_time_key = _required_draft_value(panel_contract, "cross_section_time_key")
    asset_key = _required_draft_value(panel_contract, "asset_key")
    universe_membership_rule = _required_draft_value(panel_contract, "universe_membership_rule")
    group_taxonomy_reference = str(
        taxonomy_contract.get("group_taxonomy_reference") or route_payload.get("group_taxonomy_reference", "")
    ).strip()
    group_mapping_rule = _required_draft_value(taxonomy_contract, "group_mapping_rule")
    taxonomy_note = _required_draft_value(taxonomy_contract, "taxonomy_note")
    eligibility_base_rule = _required_draft_value(eligibility_contract, "eligibility_base_rule")
    coverage_floor_rule = _required_draft_value(eligibility_contract, "coverage_floor_rule")
    mask_audit_note = _required_draft_value(eligibility_contract, "mask_audit_note")
    shared_feature_outputs = _string_list(shared_feature_base.get("shared_feature_outputs", []))
    shared_feature_note = _required_draft_value(shared_feature_base, "shared_feature_note")
    machine_artifacts = _string_list(delivery_contract.get("machine_artifacts", []))
    consumer_stage = _required_draft_value(delivery_contract, "consumer_stage")
    frozen_inputs_note = _required_draft_value(delivery_contract, "frozen_inputs_note")
    runtime_root = _runtime_root()
    runtime_git_revision = _git_revision(runtime_root)

    (stage_formal_dir / "panel_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_data_ready",
                "lineage_id": lineage_root.name,
                "panel_primary_key": panel_primary_key,
                "cross_section_time_key": cross_section_time_key,
                "asset_key": asset_key,
                "shared_feature_outputs": shared_feature_outputs,
                "machine_artifacts": machine_artifacts,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    for name in [
        "asset_universe_membership.parquet",
        "cross_section_coverage.parquet",
        "eligibility_base_mask.parquet",
    ]:
        (stage_formal_dir / name).write_text("占位 parquet 载荷\n", encoding="utf-8")
    (stage_formal_dir / "shared_feature_base").mkdir(exist_ok=True)
    if group_taxonomy_reference:
        (stage_formal_dir / "asset_taxonomy_snapshot.parquet").write_text(
            f"group_taxonomy_reference={group_taxonomy_reference}\n",
            encoding="utf-8",
        )
    (stage_formal_dir / "csf_data_contract.md").write_text(
        "\n".join(
            [
                "# CSF 数据合同",
                "",
                f"- 面板主键: {panel_primary_key}",
                f"- 截面时间键: {cross_section_time_key}",
                f"- 资产键: {asset_key}",
                f"- Universe membership 规则: {universe_membership_rule}",
                f"- Eligibility base 规则: {eligibility_base_rule}",
                f"- 覆盖率下限规则: {coverage_floor_rule}",
                f"- 共享特征输出: {', '.join(shared_feature_outputs)}",
                f"- 共享特征说明: {shared_feature_note}",
                f"- 分组体系引用: {group_taxonomy_reference}",
                f"- 分组映射规则: {group_mapping_rule}",
                f"- Taxonomy 说明: {taxonomy_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "csf_data_ready_gate_decision.md").write_text(
        "\n".join(
            [
                "# CSF Data Ready Gate Decision",
                "",
                "- 在 review closure 写出之前，formal gate 决策仍保持 pending。",
                f"- 下游消费阶段: {consumer_stage}",
                f"- 冻结输入说明: {frozen_inputs_note}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rebuild_script_path = stage_formal_dir / CSF_DATA_READY_REBUILD_SCRIPT
    rebuild_script_path.write_text(
        _render_rebuild_script(
            stage_label="csf_data_ready",
            module_relpath="tools/csf_data_ready_runtime.py",
            function_name="build_csf_data_ready_from_mandate",
            runtime_root_hint=str(runtime_root),
        ),
        encoding="utf-8",
    )
    rebuild_script_path.chmod(0o755)
    (stage_formal_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "stage": "csf_data_ready",
                "lineage_id": lineage_root.name,
                "source_stage": "mandate",
                "panel_primary_key": panel_primary_key,
                "cross_section_time_key": cross_section_time_key,
                "asset_key": asset_key,
                "universe_membership_rule": universe_membership_rule,
                "group_taxonomy_reference": group_taxonomy_reference,
                "eligibility_base_rule": eligibility_base_rule,
                "coverage_floor_rule": coverage_floor_rule,
                "shared_feature_outputs": shared_feature_outputs,
                "machine_artifacts": machine_artifacts,
                "consumer_stage": consumer_stage,
                "frozen_inputs_note": frozen_inputs_note,
                "runtime_root_hint": str(runtime_root),
                "runtime_module": "tools/csf_data_ready_runtime.py",
                "runtime_function": "build_csf_data_ready_from_mandate",
                "source_git_revision": runtime_git_revision,
                "program_artifacts": [CSF_DATA_READY_REBUILD_SCRIPT],
                "replay_working_directory": stage_dir.name,
                "replay_command": f"python3 {CSF_DATA_READY_REBUILD_SCRIPT}",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "artifact_catalog.md").write_text(
        "\n".join(
            [
                "# 产物清单",
                "",
                "- panel_manifest.json",
                "- asset_universe_membership.parquet",
                "- cross_section_coverage.parquet",
                "- eligibility_base_mask.parquet",
                "- shared_feature_base/",
                "- asset_taxonomy_snapshot.parquet",
                "- csf_data_contract.md",
                "- csf_data_ready_gate_decision.md",
                "- run_manifest.json",
                f"- {CSF_DATA_READY_REBUILD_SCRIPT}",
                "- field_dictionary.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (stage_formal_dir / "field_dictionary.md").write_text(
        "\n".join(
            [
                "# 字段字典",
                "",
                f"- `panel_primary_key`: 面板主键，当前为 {panel_primary_key}。",
                f"- `cross_section_time_key`: 截面时间键，当前为 {cross_section_time_key}。",
                f"- `asset_key`: 资产键，当前为 {asset_key}。",
                f"- `eligibility_base_rule`: {eligibility_base_rule}",
                f"- `coverage_floor_rule`: {coverage_floor_rule}",
                f"- `mask_audit_note`: {mask_audit_note}",
                f"- `shared_feature_outputs`: 共享特征输出集合，当前为 {shared_feature_outputs}。",
                f"- `group_taxonomy_reference`: 分组体系引用，当前为 {group_taxonomy_reference}。",
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
    return stage_dir


def _require_confirmed_freeze_groups(stage_dir: Path) -> dict[str, Any]:
    draft_path = build_stage_context(stage_dir)["author_draft_dir"] / CSF_DATA_READY_FREEZE_DRAFT_FILE
    payload = yaml.safe_load(draft_path.read_text(encoding="utf-8")) or {}
    groups = payload.get("groups", {})
    missing = [name for name in CSF_DATA_READY_FREEZE_GROUP_ORDER if not bool(groups.get(name, {}).get("confirmed"))]
    if missing:
        raise ValueError(f"csf_data_ready draft groups must be confirmed before build: {', '.join(missing)}")
    return groups


def _required_draft_value(draft: dict[str, Any], key: str) -> str:
    value = str(draft.get(key, "")).strip()
    if not value:
        raise ValueError(f"csf_data_ready draft missing required value: {key}")
    return value


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]
