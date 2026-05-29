from __future__ import annotations

from pathlib import Path
import hashlib
import re
import shutil
from typing import Any

import yaml


class PaperToSpecError(RuntimeError):
    pass


_DETERMINISTIC_BRIDGE_CAPTURE_TIME = "not_captured_in_deterministic_bridge"


def normalize_requested_slug(value: str | None) -> str:
    if not isinstance(value, str):
        raise PaperToSpecError("requested_slug must be a string")
    if not value:
        raise PaperToSpecError("requested_slug must be a non-empty string")
    if value != value.strip():
        raise PaperToSpecError("requested_slug must not contain leading or trailing whitespace")
    if value in {".", ".."}:
        raise PaperToSpecError("requested_slug must be a safe path segment")
    if "/" in value or "\\" in value:
        raise PaperToSpecError("requested_slug must not contain path separators")
    if re.search(r"[\x00-\x1f\x7f]", value):
        raise PaperToSpecError("requested_slug must not contain control characters")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise PaperToSpecError(
            "requested_slug must contain only ASCII letters, digits, dot, underscore, or hyphen"
        )
    return value


def slugify_name(value: str | None) -> str:
    raw_value = (value or "").strip()
    text = raw_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if slug:
        return slug
    digest = hashlib.sha1(raw_value.encode("utf-8")).hexdigest()[:10]
    return f"strategy-spec-{digest}"


def validate_strategy_spec(spec_payload: dict[str, Any]) -> dict[str, Any]:
    contract = _load_strategy_spec_contract()
    payload = _ensure_mapping(spec_payload, "spec_payload")

    _require_fields(payload, contract["required_top_level_fields"], "spec_payload")

    if payload["spec_version"] != contract["spec_version"]:
        raise PaperToSpecError(
            f"spec_version must be {contract['spec_version']}, got {payload['spec_version']!r}"
        )

    strategy_identity = _ensure_mapping(payload["strategy_identity"], "strategy_identity")
    _require_fields(
        strategy_identity,
        contract["required_strategy_identity_fields"],
        "strategy_identity",
    )
    _require_non_empty_string(strategy_identity["title"], "strategy_identity.title")
    _require_non_empty_string(strategy_identity["summary"], "strategy_identity.summary")
    _require_non_empty_string(
        strategy_identity["strategy_type"],
        "strategy_identity.strategy_type",
    )
    strategy_type = strategy_identity["strategy_type"]
    if strategy_type not in contract["allowed_strategy_types"]:
        raise PaperToSpecError(
            f"strategy_identity.strategy_type must be one of {contract['allowed_strategy_types']}, "
            f"got {strategy_type!r}"
        )

    paper_stated = _ensure_mapping(payload["paper_stated"], "paper_stated")
    _require_fields(
        paper_stated,
        contract["required_paper_stated_fields"],
        "paper_stated",
    )
    for field_name in contract["required_paper_stated_fields"]:
        field_path = f"paper_stated.{field_name}"
        value = paper_stated[field_name]
        if field_name in contract["paper_stated_list_fields"]:
            _require_list(value, field_path)
        else:
            _ensure_mapping(value, field_path)

    agent_inferred = _ensure_mapping(payload["agent_inferred"], "agent_inferred")
    _require_fields(
        agent_inferred,
        contract["required_agent_inferred_fields"],
        "agent_inferred",
    )
    for field_name in contract["agent_inferred_list_fields"]:
        _require_list(agent_inferred[field_name], f"agent_inferred.{field_name}")
    for index, ambiguity in enumerate(agent_inferred["ambiguities"]):
        ambiguity_path = f"agent_inferred.ambiguities[{index}]"
        ambiguity_mapping = _ensure_mapping(ambiguity, ambiguity_path)
        _require_fields(
            ambiguity_mapping,
            contract["required_ambiguity_fields"],
            ambiguity_path,
        )
        for field_name in contract["required_ambiguity_fields"]:
            _require_non_empty_string(
                ambiguity_mapping[field_name],
                f"{ambiguity_path}.{field_name}",
            )
        severity = ambiguity_mapping["severity"]
        if severity not in contract["allowed_ambiguity_severities"]:
            raise PaperToSpecError(
                f"{ambiguity_path}.severity must be one of "
                f"{contract['allowed_ambiguity_severities']}, got {severity!r}"
            )
    for field_name in ["implementation_choices", "default_assumptions", "fallback_plan"]:
        _ensure_mapping(agent_inferred[field_name], f"agent_inferred.{field_name}")

    implementation_handoff = _ensure_mapping(
        payload["implementation_handoff"],
        "implementation_handoff",
    )
    _require_fields(
        implementation_handoff,
        contract["required_implementation_handoff_fields"],
        "implementation_handoff",
    )
    for field_name in contract["implementation_handoff_list_fields"]:
        _require_list(implementation_handoff[field_name], f"implementation_handoff.{field_name}")

    return payload


def render_strategy_spec_markdown(spec_payload: dict[str, Any]) -> str:
    strategy_identity = spec_payload["strategy_identity"]
    return "\n".join(
        [
            "# Strategy Spec",
            "",
            f"- spec_version: {spec_payload['spec_version']}",
            f"- title: {strategy_identity['title']}",
            f"- summary: {strategy_identity['summary']}",
            f"- strategy_type: {strategy_identity['strategy_type']}",
            "",
            "## strategy_identity",
            "```yaml",
            yaml.safe_dump(strategy_identity, sort_keys=False, allow_unicode=True).rstrip(),
            "```",
            "",
            "## paper_stated",
            "```yaml",
            yaml.safe_dump(spec_payload["paper_stated"], sort_keys=False, allow_unicode=True).rstrip(),
            "```",
            "",
            "## agent_inferred",
            "```yaml",
            yaml.safe_dump(
                spec_payload["agent_inferred"], sort_keys=False, allow_unicode=True
            ).rstrip(),
            "```",
            "",
            "## implementation_handoff",
            "```yaml",
            yaml.safe_dump(
                spec_payload["implementation_handoff"],
                sort_keys=False,
                allow_unicode=True,
            ).rstrip(),
            "```",
            "",
        ]
    )


def materialize_strategy_spec_bundle(
    outputs_root: str | Path,
    source_locator: str,
    source_kind: str,
    source_title: str,
    spec_payload: dict[str, Any],
    requested_slug: str | None = None,
) -> dict[str, str]:
    contract = _load_strategy_spec_contract()
    if source_kind not in contract["allowed_source_kinds"]:
        raise PaperToSpecError(
            f"source_kind must be one of {contract['allowed_source_kinds']}, got {source_kind!r}"
        )

    validated_spec = validate_strategy_spec(spec_payload)
    if requested_slug is not None:
        slug = normalize_requested_slug(requested_slug)
    else:
        slug_source = source_title or validated_spec["strategy_identity"]["title"]
        slug = slugify_name(slug_source)

    bundle_parent = Path(outputs_root) / "paper_to_spec"
    try:
        bundle_parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PaperToSpecError(
            f"failed to create strategy spec bundle parent directory {bundle_parent}: {exc}"
        ) from exc
    bundle_root = bundle_parent / slug
    # 最终 bundle 目录必须原子创建；若竞争窗口内目标被别处创建，也统一翻译成稳定错误。
    try:
        bundle_root.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise PaperToSpecError(f"target already exists: {bundle_root}") from exc

    source_manifest = {
        "schema_id": "qros-paper-to-spec-source-manifest-v1",
        "source": {
            "kind": source_kind,
            "locator": source_locator,
            "title": source_title,
            # 低层 deterministic bridge 不在运行时注入真实时钟，避免破坏可复现性。
            "capture_time": _DETERMINISTIC_BRIDGE_CAPTURE_TIME,
        },
    }

    strategy_spec_path = bundle_root / "strategy_spec.yaml"
    source_manifest_path = bundle_root / "source_manifest.yaml"
    strategy_markdown_path = bundle_root / "strategy_spec.md"

    try:
        _write_yaml_file(strategy_spec_path, validated_spec)
        _write_yaml_file(source_manifest_path, source_manifest)
        _write_text_file(
            strategy_markdown_path,
            render_strategy_spec_markdown(validated_spec),
        )
    except OSError as exc:
        _cleanup_partial_bundle(bundle_root)
        raise PaperToSpecError(
            f"failed to materialize strategy spec bundle {bundle_root}: {exc}"
        ) from exc

    return {
        "bundle_root": str(bundle_root),
        "slug": slug,
        "source_manifest_path": str(source_manifest_path),
        "strategy_spec_path": str(strategy_spec_path),
        "strategy_markdown_path": str(strategy_markdown_path),
    }


def _contract_path() -> Path:
    return Path(__file__).resolve().parents[2] / "contracts" / "paper_to_spec" / "strategy_spec_contract.yaml"


def _load_strategy_spec_contract() -> dict[str, Any]:
    contract = _load_yaml_file(_contract_path())
    return _ensure_mapping(contract, "strategy_spec_contract")


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PaperToSpecError(f"required yaml file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return _ensure_mapping(data, str(path))


def _write_yaml_file(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)


def _write_text_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _cleanup_partial_bundle(bundle_root: Path) -> None:
    try:
        shutil.rmtree(bundle_root)
    except FileNotFoundError:
        return
    except OSError:
        return


def _ensure_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PaperToSpecError(f"{field_name} must be a mapping")
    return value


def _require_fields(payload: dict[str, Any], required_fields: list[str], field_name: str) -> None:
    missing_fields = [field for field in required_fields if field not in payload]
    if missing_fields:
        joined_fields = ", ".join(missing_fields)
        raise PaperToSpecError(f"{field_name} is missing required fields: {joined_fields}")


def _require_non_empty_string(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise PaperToSpecError(f"{field_name} must be a non-empty string")


def _require_list(value: Any, field_name: str) -> None:
    if not isinstance(value, list):
        raise PaperToSpecError(f"{field_name} must be a list")
