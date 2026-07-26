from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import metrics
from .drawer import DEFAULT_ROOMS
from .paths import data_dir


def _wing_id(project: Path) -> str:
    name = project.name.lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_-]", "", name) or "project"


def init_project(project: Path, *, force: bool = False, global_rule: bool = False) -> list[str]:
    """Create missing Atlas files. Never overwrite unless force=True."""
    actions: list[str] = []
    project = project.resolve()
    cursor = project / ".cursor"
    cursor.mkdir(parents=True, exist_ok=True)
    (cursor / "rules").mkdir(exist_ok=True)
    (cursor / "skills" / "atlas").mkdir(parents=True, exist_ok=True)

    templates = data_dir("templates")
    for name in ("mempalace-index.md", "graphify-index.md", "project-cache.md"):
        src = templates / name
        dest = cursor / name
        if dest.exists() and not force:
            actions.append(f"keep  {dest}")
            continue
        if not src.exists():
            actions.append(f"miss  template {name}")
            continue
        shutil.copy2(src, dest)
        actions.append(f"create {dest}")

    # Seed rooms if template placeholder remains
    mpi = cursor / "mempalace-index.md"
    if mpi.exists():
        body = mpi.read_text(encoding="utf-8")
        needs_seed = "<!-- atlas:seed -->" in body or force
        if needs_seed:
            wing = _wing_id(project)
            header = body.split("## Wings / rooms")[0].rstrip()
            seed = [header, "", "## Wings / rooms", ""]
            for room in DEFAULT_ROOMS:
                label = wing if room == "general" else f"{wing}-{room}"
                seed.append(f"### {label}")
                seed.append(f"- **wing:** `{wing}`")
                seed.append(f"- **room:** `{room}`")
                seed.append(f"- **workspace:** `{project}`")
                seed.append(f"- **description:** Atlas room `{room}` for this project.")
                seed.append("- **status:** active")
                seed.append("")
            seed.append("### atlas_shared")
            seed.append("- **wing:** `atlas_shared`")
            seed.append("- **room:** `conventions`")
            seed.append("- **workspace:** `(cross-project)`")
            seed.append("- **description:** Shared hallway for reusable patterns across projects.")
            seed.append("- **status:** active")
            seed.append("")
            mpi.write_text("\n".join(seed), encoding="utf-8")
            actions.append(f"seed  mempalace-index wing={wing}")

    # Rule + skill
    rule_src = data_dir("cursor", "rules", "atlas.mdc")
    rule_dest = cursor / "rules" / "atlas.mdc"
    if rule_src.exists() and (force or not rule_dest.exists()):
        shutil.copy2(rule_src, rule_dest)
        actions.append(f"create {rule_dest}")
    else:
        actions.append(f"keep  {rule_dest}")

    skill_dir = data_dir("cursor", "skills", "atlas")
    for fname in ("SKILL.md", "reference.md"):
        s = skill_dir / fname
        d = cursor / "skills" / "atlas" / fname
        if s.exists() and (force or not d.exists()):
            shutil.copy2(s, d)
            actions.append(f"create {d}")

    # .atlasignore
    ignore_src = data_dir(".atlasignore.example")
    if not ignore_src.exists():
        ignore_src = data_dir("atlasignore.example")
    ignore_dest = project / ".atlasignore"
    if ignore_src.exists() and (force or not ignore_dest.exists()):
        shutil.copy2(ignore_src, ignore_dest)
        actions.append(f"create {ignore_dest}")

    if global_rule:
        home_rule = Path.home() / ".cursor" / "rules" / "atlas.mdc"
        home_rule.parent.mkdir(parents=True, exist_ok=True)
        if rule_src.exists():
            shutil.copy2(rule_src, home_rule)
            actions.append(f"create {home_rule} (global)")
        home_skill = Path.home() / ".cursor" / "skills" / "atlas"
        home_skill.mkdir(parents=True, exist_ok=True)
        for fname in ("SKILL.md", "reference.md"):
            s = skill_dir / fname
            if s.exists():
                shutil.copy2(s, home_skill / fname)
                actions.append(f"create {home_skill / fname}")

    metrics.record(project, "init")
    return actions
