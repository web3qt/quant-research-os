from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

import yaml

MANDATE_STAGE_ID = "mandate"
CSF_DATA_READY_STAGE_ID = "csf_data_ready"
GENERIC_SUPPORTED_STAGE_DIRS: dict[str, str] = {
    "data_ready": "02_data_ready",
    "signal_ready": "03_signal_ready",
    "train_freeze": "04_train_freeze",
    "test_evidence": "05_test_evidence",
    "backtest_ready": "06_backtest",
    "holdout_validation": "07_holdout",
    "csf_signal_ready": "03_csf_signal_ready",
    "csf_train_freeze": "04_csf_train_freeze",
    "csf_test_evidence": "05_csf_test_evidence",
    "csf_backtest_ready": "06_csf_backtest_ready",
    "csf_holdout_validation": "07_csf_holdout_validation",
}
DISPLAY_REPORTS_DIR = Path("reports") / "stage_display"
STRUCTURED_SUMMARY_SCHEMA_VERSION = "1.0"
SUBAGENT_COMMAND_ENV = "QROS_STAGE_DISPLAY_SUBAGENT_CMD"
DISPLAY_REQUEST_STATUS = "awaiting_native_subagent_render"
DISPLAY_RESULT_COMPLETE = "complete"
DISPLAY_RESULT_FAILED = "failed"
GENERIC_REQUIRED_OUTPUTS = (
    "artifact_catalog.md",
    "field_dictionary.md",
    "program_execution_manifest.json",
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
)
GENERIC_SECTION_ORDER = (
    "Stage Metadata And Core Evidence",
    "Frozen Artifact Inventory",
    "Review Closure Evidence",
)

MANDATE_REQUIRED_OUTPUTS = (
    "mandate.md",
    "research_scope.md",
    "research_route.yaml",
    "time_split.json",
    "parameter_grid.yaml",
    "run_config.toml",
    "artifact_catalog.md",
    "field_dictionary.md",
    "program_execution_manifest.json",
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
)
MANDATE_SECTION_ORDER = (
    "Mandate Question And Route",
    "Scope And Data Contract",
    "Execution And Review Evidence",
)

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
    request_filename: str
    prompt_filename: str
    result_filename: str
    html_filename: str


def _config(stage_id: str, stage_dir_name: str) -> StageDisplayConfig:
    return StageDisplayConfig(
        stage_id=stage_id,
        stage_dir_name=stage_dir_name,
        summary_filename=f"{stage_id}.summary.json",
        request_filename=f"{stage_id}.display_request.json",
        prompt_filename=f"{stage_id}.display_prompt.txt",
        result_filename=f"{stage_id}.display_result.json",
        html_filename=f"{stage_id}.summary.html",
    )


SUPPORTED_STAGE_CONFIGS: dict[str, StageDisplayConfig] = {
    MANDATE_STAGE_ID: _config(MANDATE_STAGE_ID, "01_mandate"),
    CSF_DATA_READY_STAGE_ID: _config(CSF_DATA_READY_STAGE_ID, "02_csf_data_ready"),
    **{stage_id: _config(stage_id, stage_dir_name) for stage_id, stage_dir_name in GENERIC_SUPPORTED_STAGE_DIRS.items()},
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
    if config.stage_id == MANDATE_STAGE_ID:
        return _build_mandate_summary(lineage_root=lineage_root, config=config)
    if config.stage_id == CSF_DATA_READY_STAGE_ID:
        return _build_csf_data_ready_summary(lineage_root=lineage_root, config=config)
    return _build_generic_stage_summary(lineage_root=lineage_root, config=config)


# 这里保持 registry-thin：generic shell 只做路由，阶段语义仍由 repo-owned builder 决定。
def prepare_stage_display_handoff(
    *,
    lineage_root: Path,
    stage_id: str,
    output_dir: Path | None = None,
) -> dict[str, object]:
    config = resolve_stage_display_config(stage_id)
    summary = build_stage_display_summary(lineage_root=lineage_root, stage_id=stage_id)

    resolved_output_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR)).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    paths = _display_artifact_paths(resolved_output_dir, config)
    prompt = build_stage_display_render_prompt(summary)

    if paths["html_path"].exists():
        paths["html_path"].unlink()
    if paths["result_path"].exists():
        paths["result_path"].unlink()

    summary["artifacts"] = _artifact_strings(paths)
    summary["render_status"] = DISPLAY_REQUEST_STATUS
    _write_json(paths["summary_path"], summary)
    paths["prompt_path"].write_text(prompt.rstrip() + "\n", encoding="utf-8")

    request_payload = {
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": stage_id,
        "lineage_id": lineage_root.name,
        "lineage_root": str(lineage_root),
        "summary_path": str(paths["summary_path"]),
        "prompt_path": str(paths["prompt_path"]),
        "html_output_path": str(paths["html_path"]),
        "result_path": str(paths["result_path"]),
        "status": DISPLAY_REQUEST_STATUS,
        "required_subagent": True,
        "instructions": (
            "Use any Codex session to read prompt_path, natively spawn a visible subagent to render HTML "
            "to html_output_path, then write result_path with completion metadata."
        ),
    }
    _write_json(paths["request_path"], request_payload)
    return {
        "stage_id": stage_id,
        "lineage_root": str(lineage_root),
        "supported_stage_ids": list(supported_stage_ids()),
        "structured_summary_path": str(paths["summary_path"]),
        "request_path": str(paths["request_path"]),
        "prompt_path": str(paths["prompt_path"]),
        "html_path": str(paths["html_path"]),
        "result_path": str(paths["result_path"]),
        "render_status": DISPLAY_REQUEST_STATUS,
        "required_subagent": True,
    }


def write_stage_display_report(
    *,
    lineage_root: Path,
    stage_id: str,
    output_dir: Path | None = None,
    renderer_command: Sequence[str] | str | None = None,
) -> dict[str, object]:
    result = prepare_stage_display_handoff(
        lineage_root=lineage_root,
        stage_id=stage_id,
        output_dir=output_dir,
    )
    if renderer_command is None:
        return result

    summary = _read_json_required(Path(result["structured_summary_path"]))
    try:
        html = render_stage_display_html(
            summary=summary,
            lineage_root=lineage_root,
            renderer_command=renderer_command,
        )
    except StageDisplayRenderError as exc:
        write_stage_display_result(
            lineage_root=lineage_root,
            stage_id=stage_id,
            error=str(exc),
            output_dir=output_dir,
        )
        raise

    write_stage_display_result(
        lineage_root=lineage_root,
        stage_id=stage_id,
        html=html,
        rendered_by="runtime_renderer_override",
        output_dir=output_dir,
    )
    result["render_status"] = DISPLAY_RESULT_COMPLETE
    return result


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


def load_stage_display_request(
    *,
    lineage_root: Path,
    stage_id: str,
    output_dir: Path | None = None,
) -> dict[str, object] | None:
    config = resolve_stage_display_config(stage_id)
    display_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR)).resolve()
    request_path = display_dir / config.request_filename
    return _read_json_object(request_path)


def load_stage_display_result(
    *,
    lineage_root: Path,
    stage_id: str,
    output_dir: Path | None = None,
) -> dict[str, object] | None:
    config = resolve_stage_display_config(stage_id)
    display_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR)).resolve()
    result_path = display_dir / config.result_filename
    return _read_json_object(result_path)


def write_stage_display_result(
    *,
    lineage_root: Path,
    stage_id: str,
    html: str | None = None,
    error: str | None = None,
    rendered_by: str = "codex-native-subagent",
    rendered_at: str | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    if (html is None) == (error is None):
        raise StageDisplayError("write_stage_display_result requires exactly one of html or error")

    config = resolve_stage_display_config(stage_id)
    display_dir = (output_dir or (lineage_root / DISPLAY_REPORTS_DIR)).resolve()
    display_dir.mkdir(parents=True, exist_ok=True)
    paths = _display_artifact_paths(display_dir, config)
    request_payload = _read_json_required(paths["request_path"])
    summary_payload = _read_json_required(paths["summary_path"])

    if request_payload.get("stage_id") != stage_id or request_payload.get("lineage_id") != lineage_root.name:
        raise StageDisplayError("display request artifact does not match stage/lineage")
    if str(request_payload.get("summary_path")) != str(paths["summary_path"]):
        raise StageDisplayError("display request artifact summary_path does not match expected summary path")

    timestamp = rendered_at or _utc_now()
    result_payload = {
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": stage_id,
        "lineage_id": lineage_root.name,
        "summary_path": str(paths["summary_path"]),
        "html_path": str(paths["html_path"]),
        "request_path": str(paths["request_path"]),
        "status": DISPLAY_RESULT_COMPLETE if html is not None else DISPLAY_RESULT_FAILED,
        "rendered_by": rendered_by,
        "rendered_at": timestamp,
        "render_error": error,
    }

    if html is not None:
        if "<html" not in html.lower():
            raise StageDisplayError("completion HTML must be a complete HTML document")
        paths["html_path"].write_text(html.rstrip() + "\n", encoding="utf-8")
        summary_payload["render_status"] = DISPLAY_RESULT_COMPLETE
        summary_payload.pop("render_error", None)
    else:
        if paths["html_path"].exists():
            paths["html_path"].unlink()
        summary_payload["render_status"] = DISPLAY_RESULT_FAILED
        summary_payload["render_error"] = error

    _write_json(paths["summary_path"], summary_payload)
    _write_json(paths["result_path"], result_payload)
    return result_payload


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
        "title": str(summary.get("title", "Stage Display Summary")),
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


def _build_mandate_summary(*, lineage_root: Path, config: StageDisplayConfig) -> dict[str, object]:
    stage_dir = lineage_root / config.stage_dir_name
    if not stage_dir.exists():
        raise StageDisplayError(f"Missing stage directory for qros-stage-display: {stage_dir}")

    required_paths = {name: stage_dir / name for name in MANDATE_REQUIRED_OUTPUTS}
    missing_required = sorted(name for name, path in required_paths.items() if not path.exists())
    route_contract = _read_yaml_object(stage_dir / "research_route.yaml")
    review_certificate = _read_yaml_object(stage_dir / "stage_completion_certificate.yaml")

    sections = [
        {
            "id": "mandate_question_and_route",
            "title": MANDATE_SECTION_ORDER[0],
            "items": _mandate_question_and_route_items(
                lineage_root=lineage_root,
                stage_dir=stage_dir,
                route_contract=route_contract,
            ),
        },
        {
            "id": "scope_and_data_contract",
            "title": MANDATE_SECTION_ORDER[1],
            "items": _mandate_scope_and_data_items(stage_dir=stage_dir),
        },
        {
            "id": "execution_and_review_evidence",
            "title": MANDATE_SECTION_ORDER[2],
            "items": _mandate_execution_and_review_items(
                stage_dir=stage_dir,
                route_contract=route_contract,
                review_certificate=review_certificate,
            ),
        },
    ]

    return {
        "title": "Mandate Display Summary",
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": config.stage_id,
        "lineage_id": lineage_root.name,
        "lineage_root": str(lineage_root),
        "stage_directory": f"outputs/{lineage_root.name}/{config.stage_dir_name}",
        "supported_stage_ids": list(supported_stage_ids()),
        "required_subagent": True,
        "status": "complete" if not missing_required else "incomplete",
        "missing_required_inputs": missing_required,
        "section_order": list(MANDATE_SECTION_ORDER),
        "sections": sections,
    }


def _build_generic_stage_summary(*, lineage_root: Path, config: StageDisplayConfig) -> dict[str, object]:
    stage_dir = lineage_root / config.stage_dir_name
    if not stage_dir.exists():
        raise StageDisplayError(f"Missing stage directory for qros-stage-display: {stage_dir}")

    required_paths = {name: stage_dir / name for name in GENERIC_REQUIRED_OUTPUTS}
    missing_required = sorted(name for name, path in required_paths.items() if not path.exists())
    review_certificate = _read_yaml_object(stage_dir / "stage_completion_certificate.yaml")
    sections = [
        {
            "id": "stage_metadata",
            "title": GENERIC_SECTION_ORDER[0],
            "items": _generic_stage_metadata_items(
                lineage_root=lineage_root,
                stage_dir=stage_dir,
                config=config,
                review_certificate=review_certificate,
            ),
        },
        {
            "id": "artifact_inventory",
            "title": GENERIC_SECTION_ORDER[1],
            "items": _generic_artifact_inventory_items(stage_dir=stage_dir),
        },
        {
            "id": "review_closure",
            "title": GENERIC_SECTION_ORDER[2],
            "items": _generic_review_closure_items(stage_dir=stage_dir, review_certificate=review_certificate),
        },
    ]
    return {
        "title": _generic_stage_title(config.stage_id),
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": config.stage_id,
        "lineage_id": lineage_root.name,
        "lineage_root": str(lineage_root),
        "stage_directory": f"outputs/{lineage_root.name}/{config.stage_dir_name}",
        "supported_stage_ids": list(supported_stage_ids()),
        "required_subagent": True,
        "status": "complete" if not missing_required else "incomplete",
        "missing_required_inputs": missing_required,
        "section_order": list(GENERIC_SECTION_ORDER),
        "sections": sections,
    }


def _generic_stage_title(stage_id: str) -> str:
    return stage_id.replace("_", " ").title() + " Display Summary"


def _generic_stage_metadata_items(
    *,
    lineage_root: Path,
    stage_dir: Path,
    config: StageDisplayConfig,
    review_certificate: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    items = [
        _info_item("stage_directory", f"stage directory: outputs/{lineage_root.name}/{stage_dir.name}"),
        _info_item("stage_id", f"stage_id: {config.stage_id}"),
        _artifact_item("artifact_catalog.md", stage_dir / "artifact_catalog.md"),
        _artifact_item("field_dictionary.md", stage_dir / "field_dictionary.md"),
        _artifact_item("program_execution_manifest.json", stage_dir / "program_execution_manifest.json"),
    ]
    verdict = None if review_certificate is None else review_certificate.get("stage_status") or review_certificate.get("final_verdict")
    if verdict:
        items.append(_info_item("review_verdict", f"review_verdict: {verdict}"))
    else:
        items.append(_question_item("Which explicit review closure verdict governs this frozen stage?"))
    return items


def _generic_artifact_inventory_items(*, stage_dir: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path in sorted(stage_dir.iterdir(), key=lambda p: p.name):
        if path.name in {"adversarial_review_request.yaml", "adversarial_review_result.yaml", "review_findings.yaml"}:
            continue
        label = path.name + ("/" if path.is_dir() else "")
        items.append(_artifact_item(label, path, is_directory=path.is_dir()))
    if not items:
        items.append(_question_item("Which frozen stage-local artifacts should be visible to reviewers here?"))
    return items


def _generic_review_closure_items(
    *,
    stage_dir: Path,
    review_certificate: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    items = [
        _artifact_item("latest_review_pack.yaml", stage_dir / "latest_review_pack.yaml"),
        _artifact_item("stage_gate_review.yaml", stage_dir / "stage_gate_review.yaml"),
        _artifact_item("stage_completion_certificate.yaml", stage_dir / "stage_completion_certificate.yaml"),
    ]
    if review_certificate is None:
        items.append(_question_item("Which review closure artifacts prove this stage may advance?"))
    else:
        verdict = review_certificate.get("stage_status") or review_certificate.get("final_verdict")
        if verdict:
            items.append(_info_item("closure_verdict", f"closure_verdict: {verdict}"))
    return items


def _mandate_question_and_route_items(
    *,
    lineage_root: Path,
    stage_dir: Path,
    route_contract: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    mandate_text = _safe_read_text(stage_dir / "mandate.md")
    items = [
        _info_item(
            label="stage_directory",
            text=f"stage directory: outputs/{lineage_root.name}/{stage_dir.name}",
        ),
        _artifact_item("mandate.md", stage_dir / "mandate.md"),
        _artifact_item("research_route.yaml", stage_dir / "research_route.yaml"),
    ]
    research_question = _extract_line_value(mandate_text, "- 研究问题:")
    primary_hypothesis = _extract_line_value(mandate_text, "- 主假设:")
    counter_hypothesis = _extract_line_value(mandate_text, "- 对立假设:")
    if research_question:
        items.append(_info_item("research_question", f"research_question: {research_question}"))
    else:
        items.append(_missing_item("research_question", "research_question: missing from mandate.md"))
    if primary_hypothesis:
        items.append(_info_item("primary_hypothesis", f"primary_hypothesis: {primary_hypothesis}"))
    else:
        items.append(_question_item("Which frozen line in mandate.md states the primary hypothesis?"))
    if counter_hypothesis:
        items.append(_info_item("counter_hypothesis", f"counter_hypothesis: {counter_hypothesis}"))
    else:
        items.append(_question_item("Which frozen line in mandate.md states the counter hypothesis?"))
    if route_contract is None:
        items.append(_missing_item("research_route", "research_route: missing from research_route.yaml"))
    else:
        for field_name in (
            "research_route",
            "factor_role",
            "factor_structure",
            "portfolio_expression",
            "neutralization_policy",
        ):
            value = route_contract.get(field_name)
            if value in (None, ""):
                items.append(_missing_item(field_name, f"{field_name}: missing from research_route.yaml"))
            else:
                items.append(_info_item(field_name, f"{field_name}: {value}"))
    items.append(
        _question_item(
            "Does the frozen mandate question still match the declared route and factor identity without reinterpreting alpha quality?",
        )
    )
    return items


def _mandate_scope_and_data_items(*, stage_dir: Path) -> list[dict[str, str]]:
    scope_text = _safe_read_text(stage_dir / "research_scope.md")
    run_config_text = _safe_read_text(stage_dir / "run_config.toml")
    time_split_text = _safe_read_text(stage_dir / "time_split.json")
    items = [
        _artifact_item("research_scope.md", stage_dir / "research_scope.md"),
        _artifact_item("time_split.json", stage_dir / "time_split.json"),
        _artifact_item("parameter_grid.yaml", stage_dir / "parameter_grid.yaml"),
        _artifact_item("run_config.toml", stage_dir / "run_config.toml"),
    ]
    for label, prefix in (
        ("market", "- 市场:"),
        ("data_source", "- 数据来源:"),
        ("universe", "- Universe:"),
        ("bar_size", "- Bar 粒度:"),
        ("target_task", "- 研究任务:"),
    ):
        value = _extract_line_value(scope_text, prefix)
        if value:
            items.append(_info_item(label, f"{label}: {value}"))
        else:
            items.append(_question_item(f"Which frozen scope line records {label}?"))
    if "\"holdout\"" in time_split_text or "\"test\"" in time_split_text:
        items.append(_info_item("time_split", "time_split.json: present with frozen split keys"))
    else:
        items.append(_question_item("Does time_split.json freeze the downstream train/test/holdout boundaries?"))
    if "lookahead" in run_config_text.lower() or "no_lookahead" in run_config_text.lower():
        items.append(_info_item("lookahead_guardrail", "run_config.toml: lookahead guardrail recorded"))
    else:
        items.append(_question_item("Where is the no-lookahead guardrail frozen for downstream consumers?"))
    return items


def _mandate_execution_and_review_items(
    *,
    stage_dir: Path,
    route_contract: Mapping[str, object] | None,
    review_certificate: Mapping[str, object] | None,
) -> list[dict[str, str]]:
    items = [
        _artifact_item("artifact_catalog.md", stage_dir / "artifact_catalog.md"),
        _artifact_item("field_dictionary.md", stage_dir / "field_dictionary.md"),
        _artifact_item("program_execution_manifest.json", stage_dir / "program_execution_manifest.json"),
        _artifact_item("latest_review_pack.yaml", stage_dir / "latest_review_pack.yaml"),
        _artifact_item("stage_gate_review.yaml", stage_dir / "stage_gate_review.yaml"),
        _artifact_item("stage_completion_certificate.yaml", stage_dir / "stage_completion_certificate.yaml"),
    ]
    if route_contract is not None:
        for field_name in ("target_strategy_reference", "group_taxonomy_reference"):
            value = route_contract.get(field_name)
            if value:
                items.append(_info_item(field_name, f"{field_name}: {value}"))
    if review_certificate is None:
        items.append(_missing_item("review_verdict", "review_verdict: missing from stage_completion_certificate.yaml"))
    else:
        verdict = review_certificate.get("stage_status") or review_certificate.get("final_verdict")
        if verdict:
            items.append(_info_item("review_verdict", f"review_verdict: {verdict}"))
        else:
            items.append(_question_item("Which explicit review closure verdict governs this frozen mandate stage?"))
    items.append(
        _question_item(
            "Do the closure artifacts fully explain what was approved and what remains reserved without adding new interpretation?",
        )
    )
    return items


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
        "title": "CSF Data Ready Display Summary",
        "schema_version": STRUCTURED_SUMMARY_SCHEMA_VERSION,
        "stage_id": config.stage_id,
        "lineage_id": lineage_root.name,
        "lineage_root": str(lineage_root),
        "stage_directory": f"outputs/{lineage_root.name}/{config.stage_dir_name}",
        "supported_stage_ids": list(supported_stage_ids()),
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


def _display_artifact_paths(display_dir: Path, config: StageDisplayConfig) -> dict[str, Path]:
    return {
        "summary_path": display_dir / config.summary_filename,
        "request_path": display_dir / config.request_filename,
        "prompt_path": display_dir / config.prompt_filename,
        "result_path": display_dir / config.result_filename,
        "html_path": display_dir / config.html_filename,
    }


def _artifact_strings(paths: Mapping[str, Path]) -> dict[str, str]:
    return {key: str(value) for key, value in paths.items()}


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


def _read_json_required(path: Path) -> dict[str, object]:
    loaded = _read_json_object(path)
    if loaded is None:
        raise StageDisplayError(f"Expected machine-readable JSON artifact is missing or invalid: {path}")
    return loaded


def _read_yaml_object(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else None


def _safe_read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_line_value(text: str, prefix: str) -> str | None:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


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


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
