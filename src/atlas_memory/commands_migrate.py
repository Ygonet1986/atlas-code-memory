from __future__ import annotations

import re
import shutil
from pathlib import Path

from .commands_init import init_project


def migrate_project(project: Path) -> list[str]:
    """Migrate loose Cursor memory files into Atlas layout."""
    project = project.resolve()
    actions: list[str] = []
    cursor = project / ".cursor"
    cursor.mkdir(exist_ok=True)

    # Old names → new
    renames = {
        "agent-memory-stack.mdc": "rules/atlas.mdc",
        "rules/agent-memory-stack.mdc": "rules/atlas.mdc",
    }
    for old, new in renames.items():
        src = cursor / old if not old.startswith("rules/") else project / ".cursor" / old
        # normalize
        src = project / ".cursor" / old.replace("rules/", "rules/")
        if old.startswith("rules/"):
            src = project / ".cursor" / old
        else:
            src = project / ".cursor" / old
        dest = project / ".cursor" / new
        if src.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            actions.append(f"moved {src.name} -> {new}")

    # Ensure atlas skeleton
    actions.extend(init_project(project, force=False))

    # Convert AGENTS.md atlas section marker if missing
    agents = project / "AGENTS.md"
    marker = "<!-- atlas-memory -->"
    blurb = (
        f"{marker}\n"
        "## Atlas\n\n"
        "Follow Atlas order: mempalace-index → MemPalace → graphify-index → "
        "Graphify|MindMap → project-cache. Run `atlas doctor`.\n"
    )
    if agents.exists():
        text = agents.read_text(encoding="utf-8", errors="replace")
        if marker not in text:
            agents.write_text(text.rstrip() + "\n\n" + blurb, encoding="utf-8")
            actions.append("append AGENTS.md Atlas section")
    else:
        # only create if other cursor rules exist (likely an agent project)
        if (cursor / "rules").exists():
            agents.write_text(f"# Agent instructions\n\n{blurb}", encoding="utf-8")
            actions.append("create AGENTS.md")

    # Legacy project-cache without header
    cache = cursor / "project-cache.md"
    if cache.exists():
        t = cache.read_text(encoding="utf-8", errors="replace")
        if not t.startswith("#"):
            cache.write_text("# Project Source Cache\n\n" + t, encoding="utf-8")
            actions.append("normalize project-cache header")

    if not actions:
        actions.append("nothing to migrate")
    return actions
