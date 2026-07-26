from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from . import __version__
from .metrics import metrics_path, summary


def maybe_send_telemetry(project: Path) -> dict:
    """
    Opt-in anonymous telemetry. Requires ATLAS_TELEMETRY_URL and ATLAS_TELEMETRY=1.
    Sends only aggregate event counters + version — never file contents or paths.
    """
    if os.environ.get("ATLAS_TELEMETRY", "").strip() not in {"1", "true", "yes"}:
        return {"sent": False, "reason": "set ATLAS_TELEMETRY=1 to enable"}
    url = os.environ.get("ATLAS_TELEMETRY_URL", "").strip()
    if not url:
        return {"sent": False, "reason": "ATLAS_TELEMETRY_URL not set"}
    data = summary(project)
    payload = {
        "version": __version__,
        "events": data.get("events", {}),
        "project_id": "anonymous",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": f"atlas-memory/{__version__}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"sent": True, "status": resp.status}
    except Exception as e:
        return {"sent": False, "error": str(e)}
