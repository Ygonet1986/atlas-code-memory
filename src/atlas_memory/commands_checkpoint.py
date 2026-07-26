from __future__ import annotations

import subprocess
from pathlib import Path

from .drawer import Drawer, parse_drawer_markdown, validate_drawer


MEMPALACE_YAML = """# Atlas → MemPalace room map for this project
wing: {wing}
rooms:
  architecture: architecture
  debugging: debugging
  conventions: conventions
  build: build
  general: general
"""


def ensure_mempalace_yaml(project: Path, wing: str) -> Path:
    path = project / "mempalace.yaml"
    if not path.exists():
        path.write_text(MEMPALACE_YAML.format(wing=wing), encoding="utf-8")
    return path


def drawers_root(project: Path) -> Path:
    return project / ".cursor" / "atlas-drawers"


def write_drawer_file(project: Path, drawer: Drawer) -> Path:
    """Write validated drawer under .cursor/atlas-drawers/<room>/ for MemPalace mine."""
    room = drawer.room or "general"
    root = drawers_root(project) / room
    root.mkdir(parents=True, exist_ok=True)
    # slug from summary
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", drawer.summary.lower()).strip("-")[:50] or "drawer"
    dest = root / f"{slug}.md"
    dest.write_text(drawer.to_markdown(), encoding="utf-8")
    return dest


def file_checkpoint(
    project: Path,
    text: str,
    *,
    wing: str | None = None,
    mine: bool = False,
) -> dict:
    project = project.resolve()
    drawer = parse_drawer_markdown(text)
    errors = validate_drawer(drawer)
    if errors:
        return {"ok": False, "errors": errors}

    # detect wing from mempalace-index
    if not wing:
        mpi = project / ".cursor" / "mempalace-index.md"
        if mpi.exists():
            import re

            m = re.search(r"\*\*wing:\*\* `([^`]+)`", mpi.read_text(encoding="utf-8", errors="replace"))
            wing = m.group(1) if m else project.name
        else:
            wing = project.name
    ensure_mempalace_yaml(project, wing or "project")
    path = write_drawer_file(project, drawer)
    mined = None
    if mine:
        cmd = ["mempalace", "mine", str(path.parent), "--wing", wing or "project"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            mined = {"returncode": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-1000:]}
        except FileNotFoundError:
            mined = {"returncode": 127, "error": "mempalace not on PATH"}
    return {"ok": True, "path": str(path), "drawer": drawer.to_dict(), "wing": wing, "mine": mined}
