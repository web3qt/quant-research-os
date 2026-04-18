from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REVIEW_CYCLE_TRACE_FILENAME = "review_cycle_trace.jsonl"


def append_review_cycle_event(
    stage_dir: Path,
    *,
    event_type: str,
    review_cycle_id: str,
    payload: dict[str, Any],
) -> None:
    trace_path = stage_dir / "review" / REVIEW_CYCLE_TRACE_FILENAME
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "review_cycle_id": review_cycle_id,
        **payload,
    }
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def load_review_cycle_trace(path: str | Path) -> list[dict[str, Any]]:
    trace_path = Path(path)
    if not trace_path.exists():
        raise ValueError(f"{trace_path}: {REVIEW_CYCLE_TRACE_FILENAME} is missing")
    events: list[dict[str, Any]] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{trace_path}: each line must decode to a mapping")
        events.append(payload)
    return events
