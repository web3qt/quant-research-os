from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from tools.review_skillgen.context_inference import build_stage_context
from tools.review_skillgen.governance_signal import build_governance_signal_bundle, load_review_governance_policy


def governance_root_for_lineage(lineage_root: Path) -> Path:
    return lineage_root.resolve().parents[1] / "governance"


def _ensure_dirs(governance_root: Path) -> tuple[Path, Path, Path]:
    candidates = governance_root / "candidates"
    decisions = governance_root / "decisions"
    governance_root.mkdir(parents=True, exist_ok=True)
    candidates.mkdir(parents=True, exist_ok=True)
    decisions.mkdir(parents=True, exist_ok=True)
    return governance_root / "review_findings_ledger.jsonl", candidates, decisions


def _load_existing_ledger(ledger_path: Path) -> list[dict[str, Any]]:
    if not ledger_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _append_ledger_entries(ledger_path: Path, entries: list[dict[str, Any]]) -> None:
    if not entries:
        return
    with ledger_path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _candidate_id(fingerprint: str) -> str:
    return f"review-{fingerprint}"


def _load_decisions(decisions_dir: Path) -> dict[str, dict[str, str]]:
    decisions: dict[str, dict[str, str]] = {}
    for path in sorted(decisions_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        _, frontmatter, *_ = text.split("---", 2)
        payload = yaml.safe_load(frontmatter) or {}
        if not isinstance(payload, dict):
            continue
        candidate_id = payload.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            continue
        decision_outcome = str(payload.get("decision_outcome") or payload.get("decision") or "").lower()
        normalized = {
            "approve": "approved",
            "approved": "approved",
            "reject": "rejected",
            "rejected": "rejected",
            "defer": "deferred",
            "deferred": "deferred",
        }.get(decision_outcome)
        if normalized is None:
            continue
        decisions[candidate_id] = {
            "status": normalized,
            "path": str(path),
        }
    return decisions


def update_governance_candidates(*, governance_root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    ledger_path, candidates_dir, decisions_dir = _ensure_dirs(governance_root)
    records = _load_existing_ledger(ledger_path)
    by_fingerprint: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record.get("finding_class") == "review_cycle_observation":
            continue
        by_fingerprint.setdefault(record["finding_fingerprint"], []).append(record)
    decisions = _load_decisions(decisions_dir)
    updated: list[str] = []
    min_cycles = policy["thresholds"]["min_distinct_review_cycles"]
    min_contexts_for_hard_gate = policy["thresholds"]["min_distinct_contexts_for_hard_gate"]
    for fingerprint, fingerprint_records in by_fingerprint.items():
        distinct_cycles = {record["review_cycle_id"] for record in fingerprint_records}
        if len(distinct_cycles) < min_cycles:
            continue
        distinct_contexts = {f"{record['lineage_id']}::{record['review_stage']}" for record in fingerprint_records}
        candidate_class = "hard_gate" if len(distinct_contexts) >= min_contexts_for_hard_gate else "template_constraint"
        candidate_id = _candidate_id(fingerprint)
        decision = decisions.get(candidate_id)
        payload = {
            "candidate_id": candidate_id,
            "candidate_class": candidate_class,
            "candidate_priority_order": policy["candidate_priority_order"],
            "policy_activation_state": "inactive",
            "status": decision["status"] if decision else "awaiting_governance_decision",
            "distinct_review_cycles": len(distinct_cycles),
            "distinct_contexts": sorted(distinct_contexts),
            "evidence_records": [
                {
                    "review_cycle_id": record["review_cycle_id"],
                    "lineage_id": record["lineage_id"],
                    "review_stage": record["review_stage"],
                    "review_loop_outcome": record["review_loop_outcome"],
                    "finding_summary": record["finding_summary"],
                }
                for record in fingerprint_records
            ],
            "decision_ref": decision["path"] if decision else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        path = candidates_dir / f"{candidate_id}.yaml"
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
        updated.append(str(path))
    return {"candidates_updated": updated}


def record_review_governance(
    *,
    stage_dir: Path,
    lineage_root: Path,
    stage: str,
    request_payload: dict[str, Any],
    review_result: dict[str, Any],
    review_loop_outcome: str,
    final_verdict: str | None,
    blocking_findings: list[str],
    reservation_findings: list[str],
    info_findings: list[str],
) -> dict[str, Any]:
    policy = load_review_governance_policy()
    stage_context = build_stage_context(stage_dir)
    bundle = build_governance_signal_bundle(
        stage_dir=stage_context["review_governance_dir"],
        lineage_root=lineage_root,
        stage=stage,
        request_payload=request_payload,
        review_result=review_result,
        review_loop_outcome=review_loop_outcome,
        final_verdict=final_verdict,
        blocking_findings=blocking_findings,
        reservation_findings=reservation_findings,
        info_findings=info_findings,
        policy=policy,
    )
    governance_root = governance_root_for_lineage(lineage_root)
    ledger_path, _, _ = _ensure_dirs(governance_root)
    ledger_entries_written = 0
    if bundle["post_rollout_only"]:
        existing = _load_existing_ledger(ledger_path)
        seen = {(entry["review_cycle_id"], entry["finding_fingerprint"]) for entry in existing}
        new_entries: list[dict[str, Any]] = []
        for signal in bundle["signals"]:
            key = (bundle["review_cycle_id"], signal["finding_fingerprint"])
            if key in seen:
                continue
            entry = {
                "lineage_id": bundle["lineage_id"],
                "review_stage": bundle["review_stage"],
                "review_cycle_id": bundle["review_cycle_id"],
                "review_loop_outcome": bundle["review_loop_outcome"],
                "signal_basis": bundle["signal_basis"],
                "review_cycle_started_at": bundle["review_cycle_started_at"],
                "emitted_at": bundle["emitted_at"],
                **signal,
            }
            new_entries.append(entry)
            seen.add(key)
        _append_ledger_entries(ledger_path, new_entries)
        ledger_entries_written = len(new_entries)
    update_result = update_governance_candidates(governance_root=governance_root, policy=policy)
    return {
        "bundle": bundle,
        "ledger_entries_written": ledger_entries_written,
        "appended_entries": ledger_entries_written,
        **update_result,
    }


def sync_review_governance_from_stage(*, stage_dir: Path, lineage_root: Path) -> dict[str, Any]:
    signal_path = build_stage_context(stage_dir)["review_governance_dir"] / "governance_signal.json"
    if not signal_path.exists():
        raise FileNotFoundError(signal_path)
    bundle = json.loads(signal_path.read_text(encoding="utf-8"))
    governance_root = governance_root_for_lineage(lineage_root)
    ledger_path, _, _ = _ensure_dirs(governance_root)
    existing = _load_existing_ledger(ledger_path)
    seen = {(entry["review_cycle_id"], entry["finding_fingerprint"]) for entry in existing}
    new_entries: list[dict[str, Any]] = []
    for signal in bundle.get("signals", []):
        key = (bundle["review_cycle_id"], signal["finding_fingerprint"])
        if key in seen:
            continue
        new_entries.append(
            {
                "lineage_id": bundle["lineage_id"],
                "review_stage": bundle["review_stage"],
                "review_cycle_id": bundle["review_cycle_id"],
                "review_loop_outcome": bundle["review_loop_outcome"],
                "signal_basis": bundle["signal_basis"],
                "review_cycle_started_at": bundle["review_cycle_started_at"],
                "emitted_at": bundle["emitted_at"],
                **signal,
            }
        )
    _append_ledger_entries(ledger_path, new_entries)
    update_result = update_governance_candidates(governance_root=governance_root, policy=load_review_governance_policy())
    return {
        "ledger_appended": len(new_entries),
        "candidates_updated": update_result["candidates_updated"],
        "post_rollout": bundle.get("post_rollout_only", False),
    }
