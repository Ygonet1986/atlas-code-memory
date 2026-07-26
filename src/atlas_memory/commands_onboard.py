from __future__ import annotations

import re
from pathlib import Path

from .commands_import import import_docs
from .commands_init import init_project
from .routing import recall_route


ONBOARD_SKILL = """---
name: atlas-onboard
description: >-
  Explain and bootstrap a repository using only the Atlas memory stack.
  Use when onboarding to a new codebase or when the user asks to set up Atlas.
---

# Atlas onboard

1. Run `atlas init` if indexes are missing.
2. Run `atlas import` to seed cache from README/ADRs.
3. Run `atlas doctor`.
4. Search `mempalace-index`, then `graphify-index`, then `project-cache` — never whole-repo grep first.
5. Write a short onboarding brief: stack, entrypoints, risks, suggested first graph scopes.
6. Optionally draft 1–3 `decision` drawers under `.cursor/atlas-drawers/` via `atlas checkpoint --write`.
"""


def onboard(project: Path) -> list[str]:
    project = project.resolve()
    actions = []
    actions.extend(init_project(project))
    actions.extend(import_docs(project))

    # Write onboard skill into project
    skill_dir = project / ".cursor" / "skills" / "atlas-onboard"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        skill_path.write_text(ONBOARD_SKILL, encoding="utf-8")
        actions.append(f"create {skill_path}")

    # Brief
    route = recall_route(project, "architecture entrypoints overview modules")
    brief = project / ".cursor" / "atlas-onboard-brief.md"
    lines = [
        "# Atlas onboard brief",
        "",
        f"Project: `{project}`",
        "",
        "## Suggested recall route",
        f"- wing: `{route['mempalace'].get('wing')}`",
        f"- room: `{route['mempalace'].get('room')}`",
        "",
        "## Top cache hits (heuristic)",
    ]
    for h in route.get("cache_hits") or []:
        lines.append(f"- `{h.get('endereco') or h.get('name')}` (score={h['score']})")
    lines.append("")
    lines.append("## Graphs")
    graphs = route.get("graphs") or []
    if not graphs:
        lines.append("- none registered — suggest `atlas graph add <name> --escopo <dir>`")
    else:
        for g in graphs[:5]:
            lines.append(f"- {g['name']}: `{g['escopo']}` ({g.get('status')})")
    lines.append("")
    lines.append("## Next")
    lines.append("1. `atlas doctor`")
    lines.append("2. Register first graph scope if codebase is large")
    lines.append("3. File architecture decisions with `atlas checkpoint --write --mine`")
    lines.append("")
    brief.write_text("\n".join(lines), encoding="utf-8")
    actions.append(f"create {brief}")
    return actions
