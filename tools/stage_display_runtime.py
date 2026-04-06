from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

CSF_DATA_READY_STAGE_ID = "csf_data_ready"
DISPLAY_REPORTS_DIR = Path("reports") / "stage_display"
STRUCTURED_SUMMARY_SCHEMA_VERSION = "1.0"
SUBAGENT_COMMAND_ENV = "QROS_STAGE_DISPLAY_SUBAGENT_CMD"

CSF_REQUIRED_OUTPUTS = (
    "panel_manifest.json",
    "asset_universe_membership.parquet",
    "eligibility_base_mask.parquet",
    "cross_section_coverage.parquet",
    "shared_feature_base",
    "csf_data_contract.md",
    "run_manifest.json",
    "artifact_catalog.md",
    "field_dictionary.md",
    "rebuild_csf_data_ready.py",
)
CSF_OPTIONAL_OUTPUTS = (
    "asset_taxonomy_snapshot.parquet",
    "csf_data_ready_gate_decision.md",
)
CSF_SECTION_ORDER = (
    "Panel Contract And Core Evidence",
    "Coverage And Eligibility Evidence",
    "Delivery And Rebuild Evidence",
)


class StageDisplayError(RuntimeError):
    """Base error for stage-display workflow failures."""


class UnsupportedStageError(StageDisplayError):
    """Raised when the requested stage is not registered."""


class StageDisplayRenderError(StageDisplayError):
    """Raised when the required Codex subagent render step fails."""


@dataclass(frozen=True)
class StageDisplayConfig:
    stage_id: str
    stage_dir_name: str
    summary_filename: str
    html_filename: str


SUPPORTED_STAGE_CONFIGS: dict[str, StageDisplayConfig] = {
    CSF_DATA_READY_STAGE_ID: StageDisplayConfig(
        stage_id=CSF_DATA_READY_STAGE_ID,
        stage_dir_name="02_csf_data_ready",
        summary_filename="csf_data_ready.summary.json",
        html_filename="csf_data_ready.summary.html",
    ),
}


def supported_stage_ids() -> tuple[str, ...]:
    return tuple(SUPPORTED_STAGE_CONFIGS)


def resolve_stage_display_config(stage_id: str) -> StageDisplayConfig:
    try:
        return SUPPORTED_STAGE_CONFIGS[stage_id]
    except KeyError as exc:
        raise UnsupportedStageError(f"Unsupported stage for qros-stage-display: {stage_id}") from exc


def build_stage_display_summary(*, lineage_root: Path, stage_id: str) -> dict[str, object]:
    config = resolve_stage_display_config(stage_id)
    if config.stage_id == CSF_DATA_READY_STAGE_ID:
        return _build_csf_data_ready_summary(lineage_root=lineage_root, config=config)
    raise UnsupportedStageError(f"Unsupported stage for qros-stage-display: {stage_id}")


# 这里保持 registry-thin：generic shell 只做路由，阶段语义仍由 repo-owned builder 决定。
def write_stage_display_report(
    *,
    lineage_root: Path,
    stage_id: str,
    output_dir: Path | None = None,
    renderer_command: Sequence[str] | str | None = None,
) -> dict[str, object]:
    config = resolve_stage_display_config(stage_id)
    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id=stage_id)

    resolved_output_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR)).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = resolved_output_dir / config.summary_filename
    html_path = resolved_output_dir / config.html_filename

    summary["artifacts"] = {
        "structured_summary_path": str(summary_path),
        "html_path": str(html_path),
    }
    summary["render_status"] = "pending"
    _write_json(summary_path, summary)

    try:
        html = render_stage_display_html(
            summary=summary,
            lineage_root=lineage_root,
            renderer_command=renderer_command,
        )
    except StageDisplayRenderError as exc:
        summary["render_status"] = "incomplete_diagnostic"
        summary["render_error"] = str(exc)
        _write_json(summary_path, summary)
        if html_path.exists():
            html_path.unlink()
        raise

    html_path.write_text(html.rstrip() + "\n", encoding="utf-8")
    summary["render_status"] = "complete"
    _write_json(summary_path, summary)
    return {
        "stage_id": stage_id,
        "lineage_root": str(lineage_root),
        "supported_stage_ids": list(supported_stage_ids()),
        "structured_summary_path": str(summary_path),
        "html_path": str(html_path),
        "render_status": summary["render_status"],
        "required_subagent": True,
    }


# 兼容旧测试入口：保留 export_stage_display 名称，但内部仍复用新的 registry-thin summary builder。
def export_stage_display(
    *,
    lineage_root: Path,
    stage_id: str,
    html_renderer: object | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    try:
        resolve_stage_display_config(stage_id)
    except UnsupportedStageError as exc:
        raise ValueError(str(exc)) from exc

    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id=stage_id)
    compat_summary = _build_compat_export_summary(summary)
    display_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR / stage_id)).resolve()
    display_dir.mkdir(parents=True, exist_ok=True)
    summary_path = display_dir / "stage_display_summary.json"
    html_path = display_dir / "stage_display_summary.html"
    compat_summary["structured_summary_path"] = str(summary_path)
    compat_summary["html_path"] = str(html_path)

    # 旧入口只需要稳定成功产物合同，不把 subagent 强依赖重新暴露给这一层兼容测试。
    _ = html_renderer
    html = _render_compat_stage_display_html(compat_summary)
    _write_json(summary_path, compat_summary)
    html_path.write_text(html.rstrip() + "\n", encoding="utf-8")
    return {
        "stage_id": stage_id,
        "structured_summary_path": str(summary_path),
        "html_path": str(html_path),
    }


# subagent 是强依赖：成功 artifact 必须来自 Codex render，而不是本地 deterministic fallback 伪装成功。
def render_stage_display_html(
    *,
    summary: Mapping[str, object],
    lineage_root: Path,
    renderer_command: Sequence[str] | str | None = None,
) -> str:
    prompt = build_stage_display_render_prompt(summary)
    command = _resolve_renderer_command(renderer_command, cwd=lineage_root)
    html = ""
    with tempfile.TemporaryDirectory(prefix="qros-stage-display-") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        last_message_path = tmp_dir / "last-message.html"
        full_command = [*command, "-o", str(last_message_path), "-"]
        result = subprocess.run(
            full_command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            cwd=lineage_root,
        )
        if last_message_path.exists():
            html = last_message_path.read_text(encoding="utf-8").strip()
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        message = stderr or stdout or "subagent renderer returned a non-zero exit code"
        raise StageDisplayRenderError(f"Codex subagent render failed: {message}")
    if not html:
        html = result.stdout.strip()
    if not html:
        raise StageDisplayRenderError("Codex subagent render failed: empty HTML response")
    if "<html" not in html.lower():
        raise StageDisplayRenderError("Codex subagent render failed: response was not an HTML document")
    return html


def build_stage_display_render_prompt(summary: Mapping[str, object]) -> str:
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "# QROS Stage Display HTML Renderer",
            "",
            "You are rendering a user-visible HTML summary page from a deterministic structured summary.",
            "",
            "Requirements:",
            "- Use ONLY the structured summary JSON below as the source of truth.",
            "- Preserve the section order exactly as provided.",
            "- Preserve every item's marker value (`available`, `missing`, `question`).",
            "- Output exactly one complete HTML document and nothing else.",
            "",
            "Forbidden behaviors:",
            "- Do not infer factor performance, alpha quality, or coverage interpretations beyond the summary.",
            "- Do not hide, soften, or rewrite missing/question markers.",
            "- Do not introduce unsupported stages, extra sections, or unstated remediation claims.",
            "",
            "Suggested layout:",
            "- Title and lineage metadata header",
            "- One section card per structured summary section",
            "- A compact visual treatment for marker states so missing/question items remain explicit",
            "",
            "Structured summary JSON:",
            "```json",
            summary_json,
            "```",
        ]
    )


def _build_compat_export_summary(summary: Mapping[str, object]) -> dict[str, object]:
    title_map = {
        "Panel Contract And Core Evidence": "Panel Contract And Coverage",
        "Coverage And Eligibility Evidence": "Eligibility / Universe Artifacts",
        "Delivery And Rebuild Evidence": "Shared Feature Base And Runtime",
    }
    sections: list[dict[str, object]] = []
    for section in summary["sections"]:
        sections.append(
            {
                "title": title_map.get(str(section["title"]), str(section["title"])),
                "lines": [str(item["text"]) for item in section["items"]],
            }
        )
    return {
        "title": "CSF Data Ready Display Summary",
        "stage_id": str(summary["stage_id"]),
        "lineage_id": str(summary["lineage_id"]),
        "lineage_root": str(summary["lineage_root"]),
        "stage_directory": str(summary["stage_directory"]),
        "artifact_status": "complete" if summary["status"] == "complete" else "incomplete",
        "sections": sections,
    }


def _render_compat_stage_display_html(summary: Mapping[str, object]) -> str:
    title = str(summary["title"])
    lineage_id = str(summary["lineage_id"])
    stage_directory = str(summary["stage_directory"])
    artifact_status = str(summary["artifact_status"])
    section_html = []
    for section in summary["sections"]:
        lines = "\n".join(f"        <li>{line}</li>" for line in section["lines"])
        section_html.append(
            "\n".join(
                [
                    "    <section>",
                    f"      <h2>{section['title']}</h2>",
                    "      <ul>",
                    lines,
                    "      </ul>",
                    "    </section>",
                ]
            )
        )
    return "\n".join(
        [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "  <head>",
            "    <meta charset=\"utf-8\">",
            f"    <title>{title}</title>",
            "  </head>",
            "  <body>",
            f"    <h1>{title}</h1>",
            f"    <p>Lineage: {lineage_id}</p>",
            f"    <p>Stage directory: {stage_directory}</p>",
            f"    <p>Artifact status: {artifact_status}</p>",
            *section_html,
            "  </body>",
            "</html>",
        ]
    )


# 这里读取 stage-local contracts，只抽取已冻结事实；不解析 parquet 内容，也不推断 alpha 含义。
def _build_csf_data_ready_summary(*, lineage_root: Path, config: StageDisplayConfig) -> dict[str, object]:
    stage_dir = lineage_root / config.stage_dir_name
    if not stage_dir.exists():
        raise StageDisplayError(f"Missing stage directory for qros-stage-display: {stage_dir}")

    required_paths = {name: stage_dir / name for name in CSF_REQUIRED_OUTPUTS}
    missing_required = sorted(name for name, path in required_paths.items() if not path.exists())
    panel_manifest = _read_json_object(stage_dir / "panel_manifest.json")
    run_manifest = _read_json_object(stage_dir / "run_manifest.json")

    sections = [
        {
            "id": "panel_contract",
            "title": CSF_SECTION_ORDER[0],
            "items": _panel_contract_items(
                lineage_root=lineage_root,
                stage_dir=stage_dir,
                panel_manifest=panel_manifest,
            ),
        },
        {
            "id": "coverage_and_eligibility",
            "title": CSF_SECTION_ORDER[1],
            "items": _coverage_and_eligibility_items(stage_dir=stage_dir),
        },
        {
            "id": "delivery_and_rebuild",
            "title": CSF_SECTION_ORDER[2],
            "items": _delivery_and_rebuild_items(stage_dir=stage_dir, run_manifest=run_manifest),
        },
    ]

    return {
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": config.stage_id,
        "lineage_id": lineage_root.name,
        "lineage_root": str(lineage_root),
        "stage_directory": f"outputs/{lineage_root.name}/{config.stage_dir_name}",
        "supported_stage_ids": [CSF_DATA_READY_STAGE_ID],
        "required_subagent": True,
        "status": "complete" if not missing_required else "incomplete",
        "missing_required_inputs": missing_required,
        "section_order": list(CSF_SECTION_ORDER),
        "sections": sections,
    }


def _panel_contract_items(
    *,
    lineage_root: Path,
    stage_dir: Path,
    panel_manifest: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    items = [
        _info_item(
            label="stage_directory",
            text=f"stage directory: outputs/{lineage_root.name}/{stage_dir.name}",
        ),
        _artifact_item("panel_manifest.json", stage_dir / "panel_manifest.json"),
        _artifact_item("shared_feature_base/", stage_dir / "shared_feature_base", is_directory=True),
    ]
    if panel_manifest is None:
        items.append(
            _question_item(
                "panel_manifest.json must expose date_key, asset_key, panel_frequency, and coverage_rule for an auditable date x asset panel.",
            )
        )
        return items

    for field_name in ("date_key", "asset_key", "panel_frequency", "coverage_rule"):
        value = panel_manifest.get(field_name)
        if value in (None, ""):
            items.append(_missing_item(field_name, f"{field_name}: missing from panel manifest"))
        else:
            items.append(_info_item(field_name, f"{field_name}: {value}"))
    items.append(
        _question_item(
            "Does the declared panel contract fully explain how reviewers can reconstruct the frozen date x asset panel?",
        )
    )
    return items


def _coverage_and_eligibility_items(*, stage_dir: Path) -> list[dict[str, str]]:
    items = [
        _artifact_item("asset_universe_membership.parquet", stage_dir / "asset_universe_membership.parquet"),
        _artifact_item("eligibility_base_mask.parquet", stage_dir / "eligibility_base_mask.parquet"),
        _artifact_item("cross_section_coverage.parquet", stage_dir / "cross_section_coverage.parquet"),
        _artifact_item("csf_data_contract.md", stage_dir / "csf_data_contract.md"),
    ]

    taxonomy_path = stage_dir / "asset_taxonomy_snapshot.parquet"
    if taxonomy_path.exists():
        items.append(_artifact_item("asset_taxonomy_snapshot.parquet", taxonomy_path))
    else:
        items.append(
            _question_item(
                "If group_neutral is allowed for this lineage, where is the versioned asset taxonomy snapshot?",
            )
        )
    items.append(
        _question_item(
            "Do the frozen coverage and eligibility artifacts explain missing assets or coverage drift without mixing in downstream factor logic?",
        )
    )
    return items


def _delivery_and_rebuild_items(
    *,
    stage_dir: Path,
    run_manifest: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    items = [
        _artifact_item("run_manifest.json", stage_dir / "run_manifest.json"),
        _artifact_item("artifact_catalog.md", stage_dir / "artifact_catalog.md"),
        _artifact_item("field_dictionary.md", stage_dir / "field_dictionary.md"),
        _artifact_item("rebuild_csf_data_ready.py", stage_dir / "rebuild_csf_data_ready.py"),
        _artifact_item("csf_data_ready_gate_decision.md", stage_dir / "csf_data_ready_gate_decision.md"),
    ]
    if run_manifest is None:
        items.append(
            _question_item(
                "run_manifest.json should record runtime version, replay_command, and program_artifacts for reproducible display review.",
            )
        )
        return items

    replay_command = run_manifest.get("replay_command")
    if replay_command:
        items.append(_info_item("replay_command", f"replay_command: {replay_command}"))
    else:
        items.append(_missing_item("replay_command", "replay_command: missing from run manifest"))

    program_artifacts = run_manifest.get("program_artifacts")
    if isinstance(program_artifacts, list) and program_artifacts:
        items.append(
            _info_item(
                "program_artifacts",
                "program_artifacts: " + ", ".join(str(value) for value in program_artifacts),
            )
        )
    else:
        items.append(
            _question_item(
                "Which stage-local program artifacts prove the frozen panel can be rebuilt from the declared inputs?",
            )
        )
    return items


def _resolve_renderer_command(renderer_command: Sequence[str] | str | None, *, cwd: Path) -> list[str]:
    command_value: Sequence[str] | str | None = renderer_command
    if command_value is None:
        env_value = os.environ.get(SUBAGENT_COMMAND_ENV)
        if env_value:
            command_value = env_value
    if isinstance(command_value, str):
        parsed = shlex.split(command_value)
        if not parsed:
            raise StageDisplayRenderError("Codex subagent render failed: empty renderer command override")
        return parsed
    if command_value is not None:
        parsed = [str(part) for part in command_value]
        if not parsed:
            raise StageDisplayRenderError("Codex subagent render failed: empty renderer command override")
        return parsed
    return [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--color",
        "never",
        "-C",
        str(cwd),
    ]


def _read_json_object(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _artifact_item(label: str, path: Path, *, is_directory: bool = False) -> dict[str, str]:
    exists = path.is_dir() if is_directory else path.exists()
    marker = "available" if exists else "missing"
    suffix = "directory present" if is_directory and exists else ("present" if exists else "missing")
    return {
        "marker": marker,
        "label": label,
        "text": f"{label}: {suffix}",
    }


def _info_item(label: str, text: str) -> dict[str, str]:
    return {
        "marker": "available",
        "label": label,
        "text": text,
    }


def _missing_item(label: str, text: str) -> dict[str, str]:
    return {
        "marker": "missing",
        "label": label,
        "text": text,
    }


def _question_item(text: str) -> dict[str, str]:
    return {
        "marker": "question",
        "label": "question",
        "text": text,
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
