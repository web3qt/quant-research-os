from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Mapping, Sequence


REQUIRED_SECTION_ORDER = (
    "Data Coverage And Gaps",
    "QC / Anomaly Summary",
    "Artifact Directory And Key Files",
)


def validate_stage_summary_payload(payload: Mapping[str, object]) -> None:
    if payload.get("stage_id") != "data_ready":
        raise ValueError(f"Unsupported stage payload: {payload.get('stage_id')!r}")

    sections = payload.get("sections")
    if not isinstance(sections, Sequence):
        raise ValueError("payload['sections'] must be a sequence")

    titles = tuple(str(section.get("title")) for section in sections)
    if titles != REQUIRED_SECTION_ORDER:
        raise ValueError(f"Unexpected section order: {titles!r}")


# 这里的 deterministic renderer 是 repo-owned baseline，不依赖 Codex subagent。
def render_data_ready_summary_html(payload: Mapping[str, object], *, renderer_label: str = "deterministic-fallback") -> str:
    validate_stage_summary_payload(payload)
    title = escape(str(payload["title"]))
    lineage_id = escape(str(payload["lineage_id"]))
    session_stage = escape(str(payload["session_stage"]))
    current_route = escape(str(payload["current_route"] or "unknown"))
    stage_directory = escape(str(payload["stage_directory"]))

    sections_html: list[str] = []
    for section in payload["sections"]:
        lines_html = "\n".join(
            f"        <li>{escape(str(line))}</li>" for line in section["lines"]
        )
        sections_html.append(
            "\n".join(
                [
                    '    <section class="summary-section">',
                    f"      <h2>{escape(str(section['title']))}</h2>",
                    "      <ul>",
                    lines_html,
                    "      </ul>",
                    "    </section>",
                ]
            )
        )

    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "  <head>",
            '    <meta charset="utf-8">',
            f"    <title>{title}</title>",
            "    <style>",
            "      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 32px auto; padding: 0 24px; line-height: 1.6; color: #111827; }",
            "      h1, h2 { color: #0f172a; }",
            "      .meta { color: #475569; margin-bottom: 24px; }",
            "      .summary-section { border: 1px solid #d1d5db; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; background: #f8fafc; }",
            "      ul { margin: 0; padding-left: 20px; }",
            "      li { margin: 6px 0; }",
            "    </style>",
            "  </head>",
            "  <body>",
            f"    <h1>{title}</h1>",
            f'    <p class="meta">Lineage: {lineage_id} · Session stage: {session_stage} · Route: {current_route}</p>',
            f'    <p class="meta">Stage directory: {stage_directory} · Renderer: {escape(renderer_label)}</p>',
            *sections_html,
            "  </body>",
            "</html>",
        ]
    )


# 这里导出的 prompt 只用于 Codex-time orchestration，不属于普通 runtime 强依赖。
def build_subagent_render_prompt(payload: Mapping[str, object], *, output_html_path: Path) -> str:
    validate_stage_summary_payload(payload)
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            "# Data Ready HTML Renderer Task",
            "",
            "You are generating a user-visible HTML page from a normalized data_ready reflection payload.",
            "",
            "Requirements:",
            "- Use ONLY the payload below as the source of truth.",
            "- Preserve the three sections in the exact order provided.",
            "- Preserve `missing`, `available`, and `question:` lines explicitly.",
            "- Output a complete HTML document.",
            "",
            "Forbidden behaviors:",
            "- Do not infer parquet metrics or statistics beyond the payload.",
            "- Do not invent narrative explanations or review verdicts.",
            "- Do not hide, rewrite, or soften missing-evidence markers or question prompts.",
            "",
            f"Write the HTML artifact to: {output_html_path}",
            "",
            "Normalized payload:",
            "```json",
            payload_json,
            "```",
        ]
    )


def write_subagent_bundle(
    *,
    bundle_dir: Path,
    payload: Mapping[str, object],
    output_html_path: Path,
) -> dict[str, Path]:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    payload_path = bundle_dir / "payload.json"
    prompt_path = bundle_dir / "prompt.txt"
    output_path_file = bundle_dir / "output_path.txt"

    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prompt_path.write_text(
        build_subagent_render_prompt(payload, output_html_path=output_html_path) + "\n",
        encoding="utf-8",
    )
    output_path_file.write_text(str(output_html_path) + "\n", encoding="utf-8")

    return {
        "bundle_dir": bundle_dir,
        "payload": payload_path,
        "prompt": prompt_path,
        "output_path": output_path_file,
    }
