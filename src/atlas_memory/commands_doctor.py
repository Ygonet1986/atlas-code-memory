from __future__ import annotations

import shutil
from pathlib import Path


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def doctor(project: Path) -> list[tuple[str, str, str]]:
    """Return list of (check, status ok|warn|fail, detail)."""
    project = project.resolve()
    rows: list[tuple[str, str, str]] = []

    def file_check(rel: str, required: bool = True) -> None:
        p = project / rel
        if p.exists():
            rows.append((rel, "ok", str(p)))
        else:
            rows.append((rel, "fail" if required else "warn", "missing — run atlas init"))

    file_check(".cursor/mempalace-index.md")
    file_check(".cursor/graphify-index.md")
    file_check(".cursor/project-cache.md")
    file_check(".cursor/rules/atlas.mdc", required=False)
    file_check(".cursor/skills/atlas/SKILL.md", required=False)
    file_check(".atlasignore", required=False)

    mp = which("mempalace")
    rows.append(("mempalace CLI", "ok" if mp else "warn", mp or "optional — MemoryBackend none"))
    gf = which("graphify")
    rows.append(("graphify CLI", "ok" if gf else "warn", gf or "optional GraphBackend"))

    # Conflicting graph backends: both rule files
    mind = (project / ".cursor" / "rules").glob("*mind*")
    graphify_rule = project / ".cursor" / "rules" / "graphify.mdc"
    if graphify_rule.exists() and any(mind):
        rows.append(("graph backend conflict", "fail", "Graphify rule + Mind Map rule both present"))
    else:
        rows.append(("graph backend conflict", "ok", "no dual Graphify/MindMap rules detected"))

    hooks = project / ".git" / "hooks" / "post-commit"
    if hooks.exists() and "atlas" in hooks.read_text(encoding="utf-8", errors="replace"):
        rows.append(("git post-commit atlas", "ok", str(hooks)))
    else:
        rows.append(("git post-commit atlas", "warn", "run: atlas hooks install"))

    global_rule = Path.home() / ".cursor" / "rules" / "atlas.mdc"
    rows.append(
        (
            "global Cursor rule",
            "ok" if global_rule.exists() else "warn",
            str(global_rule) if global_rule.exists() else "atlas init --global-rule",
        )
    )
    return rows
