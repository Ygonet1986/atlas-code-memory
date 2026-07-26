from __future__ import annotations

import re
from pathlib import Path

from . import metrics


def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60] or "imported"


def import_docs(project: Path) -> list[str]:
    """Seed project-cache + suggested decisions from README and docs/adr."""
    project = project.resolve()
    actions: list[str] = []
    cursor = project / ".cursor"
    cursor.mkdir(parents=True, exist_ok=True)

    cache = cursor / "project-cache.md"
    if not cache.exists():
        cache.write_text(
            "# Project Source Cache\n\nSearch this file; never read it end-to-end.\n\n",
            encoding="utf-8",
        )
        actions.append("create project-cache.md")

    existing = cache.read_text(encoding="utf-8", errors="replace")
    additions: list[str] = []

    candidates = []
    for p in [project / "README.md", project / "readme.md"]:
        if p.exists():
            candidates.append(p)
    adr_dirs = [project / "docs" / "adr", project / "adr", project / "docs" / "adrs"]
    for d in adr_dirs:
        if d.is_dir():
            candidates.extend(sorted(d.glob("*.md")))

    for path in candidates:
        rel = path.relative_to(project).as_posix()
        if f"**path:** `{rel}`" in existing or f"**endereço:** `{rel}`" in existing:
            continue
        first = ""
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                first = line[:160]
                break
            if line.startswith("# "):
                first = line[2:].strip()
                break
        name = path.name
        additions.append(
            f"### {name}\n- **path:** `{rel}`\n- **description:** {first or 'Imported by atlas import.'}\n"
        )

    if additions:
        with cache.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(additions) + "\n")
        actions.append(f"append {len(additions)} cache entries")

    # Suggested decision stubs under .cursor/atlas-import/
    out = cursor / "atlas-import"
    out.mkdir(exist_ok=True)
    for path in candidates:
        if path.name.lower().startswith("readme"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        title = path.stem
        for line in text.splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        stub = out / f"{_slug(title)}.drawer.md"
        if stub.exists():
            continue
        stub.write_text(
            "\n".join(
                [
                    "[type:decision] [status:active]",
                    f"summary: Imported candidate from {path.relative_to(project).as_posix()}: {title}",
                    "why: Review and edit before filing to MemPalace.",
                    "branch: -",
                    "commit: -",
                    "pr: -",
                    f"files: {path.relative_to(project).as_posix()}",
                    "room: architecture",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        actions.append(f"stub  {stub.relative_to(project)}")

    if not actions:
        actions.append("nothing new to import")
    metrics.record(project, "import", count=len(actions))
    return actions
