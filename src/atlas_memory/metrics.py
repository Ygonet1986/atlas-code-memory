from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def metrics_path(project: Path) -> Path:
    return project / ".cursor" / "atlas-metrics.json"


def record(project: Path, event: str, **extra: Any) -> None:
    """Opt-in local counters (no network)."""
    path = metrics_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any]
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"events": {}, "log": []}
    else:
        data = {"events": {}, "log": []}
    events = data.setdefault("events", {})
    events[event] = int(events.get(event, 0)) + 1
    log = data.setdefault("log", [])
    log.append({"ts": time.time(), "event": event, **extra})
    data["log"] = log[-200:]  # cap
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def summary(project: Path) -> dict[str, Any]:
    path = metrics_path(project)
    if not path.exists():
        return {"events": {}, "note": "no metrics yet (opt-in via atlas commands)"}
    return json.loads(path.read_text(encoding="utf-8"))
