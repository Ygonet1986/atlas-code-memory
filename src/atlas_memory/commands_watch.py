from __future__ import annotations

import argparse
import time
from pathlib import Path

from .commands_stale import mark_stale_touched, parse_graphify_index


def watch_project(project: Path, *, interval: float = 2.0, once: bool = False) -> None:
    """Poll scoped paths and mark graphify-index stale when sources change."""
    project = project.resolve()
    index = project / ".cursor" / "graphify-index.md"
    if not index.exists():
        print("atlas watch: no graphify-index")
        return
    entries = parse_graphify_index(index.read_text(encoding="utf-8", errors="replace"))
    mtimes: dict[str, float] = {}

    def snapshot() -> dict[str, float]:
        snap: dict[str, float] = {}
        for e in entries:
            scope_path = project / e["scope"]
            if not scope_path.exists():
                continue
            newest = 0.0
            for p in scope_path.rglob("*"):
                if not p.is_file():
                    continue
                if "graphify-out" in p.parts or ".git" in p.parts:
                    continue
                try:
                    newest = max(newest, p.stat().st_mtime)
                except OSError:
                    continue
            snap[e["name"]] = newest
        return snap

    mtimes = snapshot()
    print(f"atlas watch: tracking {len(mtimes)} scopes (interval={interval}s)")
    if once:
        return
    while True:
        time.sleep(interval)
        entries = parse_graphify_index(index.read_text(encoding="utf-8", errors="replace"))
        now = snapshot()
        changed_files: list[str] = []
        for name, mt in now.items():
            if name in mtimes and mt > mtimes[name] + 0.5:
                for e in entries:
                    if e["name"] == name:
                        changed_files.append(e["scope"] + "/.")
        if changed_files:
            updated = mark_stale_touched(project, changed_files)
            if updated:
                print("stale:", ", ".join(updated))
        mtimes = now
