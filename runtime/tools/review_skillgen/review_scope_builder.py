from __future__ import annotations

from typing import Any


# 当前 reviewer 只做 stage-local 内容审查；上游绑定验证单独走 deterministic validator。
def build_review_scope(
    *,
    stage: str,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> dict[str, list[str]]:
    required_artifacts = sorted(required_artifact_paths)
    required_provenance = sorted(required_provenance_paths)
    content_exclusions: set[str] = set()
    upstream_binding: set[str] = set()

    if "route_inheritance_contract.yaml" in required_artifacts:
        content_exclusions.add("route_inheritance_contract.yaml")
        upstream_binding.add("route_inheritance_contract.yaml")

    if "csf_train_freeze.yaml" in required_artifacts:
        upstream_binding.add("csf_train_freeze.yaml")

    stage_content_artifacts = sorted(
        artifact for artifact in required_artifacts if artifact not in content_exclusions
    )
    upstream_binding_artifacts = sorted(
        artifact for artifact in required_artifacts if artifact in upstream_binding
    )

    return {
        "required_artifact_paths": required_artifacts,
        "required_provenance_paths": required_provenance,
        "stage_content_artifact_paths": stage_content_artifacts,
        "stage_content_provenance_paths": required_provenance,
        "upstream_binding_artifact_paths": upstream_binding_artifacts,
        "upstream_binding_provenance_paths": [],
    }


def stage_content_artifact_paths_from_request(request_payload: dict[str, Any]) -> list[str]:
    value = request_payload.get("stage_content_artifact_paths")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return sorted(value)
    return sorted(request_payload["required_artifact_paths"])


def stage_content_provenance_paths_from_request(request_payload: dict[str, Any]) -> list[str]:
    value = request_payload.get("stage_content_provenance_paths")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return sorted(value)
    return sorted(request_payload["required_provenance_paths"])


def upstream_binding_artifact_paths_from_request(request_payload: dict[str, Any]) -> list[str]:
    value = request_payload.get("upstream_binding_artifact_paths")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return sorted(value)
    return []


def upstream_binding_provenance_paths_from_request(request_payload: dict[str, Any]) -> list[str]:
    value = request_payload.get("upstream_binding_provenance_paths")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return sorted(value)
    return []
