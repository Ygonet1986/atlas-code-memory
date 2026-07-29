"""Generate editor connection snippets — Cursor: Atlas as default where/remember layer."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .paths import data_dir


CURSOR_MCP = {
    "mcpServers": {
        "atlas-memory": {
            "command": "atlas-mcp",
        }
    }
}

CLAUDE_MCP = {
    "mcpServers": {
        "atlas-memory": {
            "command": "atlas-mcp",
        }
    }
}

GENERIC_RULE = """# Atlas Memory (token GPS)

Before grepping a monorepo, call Atlas:

1. `atlas_recall_route` (MCP) or `GET http://127.0.0.1:8765/api/route?q=...&project=...`
2. Open only the returned cache_hits / graph scopes
3. Persist durable decisions with `atlas_checkpoint` / life remember

Never invent memory hits. Missing layer → skip.
"""


def _atlas_rule_text() -> str:
    src = data_dir("cursor", "rules", "atlas.mdc")
    if src.exists():
        return src.read_text(encoding="utf-8")
    return (
        "---\ndescription: Atlas — where to look / what to remember\nalwaysApply: true\n---\n\n"
        + GENERIC_RULE
    )


def _merge_mcp(path: Path, snippet: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if existed:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}
    servers = existing.setdefault("mcpServers", {})
    servers["atlas-memory"] = snippet["mcpServers"]["atlas-memory"]
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return f"{'updated' if existed else 'wrote'} {path}"


def _install_cursor_rule(dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(_atlas_rule_text(), encoding="utf-8")
    return f"wrote {dest}"


def _install_cursor_skill(dest_dir: Path) -> list[str]:
    actions: list[str] = []
    skill_src = data_dir("cursor", "skills", "atlas")
    dest_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("SKILL.md", "reference.md"):
        s = skill_src / fname
        if s.exists():
            shutil.copy2(s, dest_dir / fname)
            actions.append(f"wrote {dest_dir / fname}")
    return actions


def connect_editor(
    editor: str,
    *,
    project: Path | None = None,
    write: bool = True,
    global_install: bool | None = None,
) -> dict[str, Any]:
    """Wire Atlas as the editor's where-to-look / what-to-remember layer.

    For ``cursor``, ``global_install`` defaults to True: installs
    ``~/.cursor/rules/atlas.mdc``, user ``mcp.json``, and the atlas skill so
    Atlas becomes Cursor's general orientation + memory layer.
    """
    editor = (editor or "cursor").lower().strip()
    project = (project or Path(".")).resolve()
    actions: list[str] = []
    files: dict[str, str] = {}

    if global_install is None:
        global_install = editor == "cursor"

    if editor in {"cursor", "windsurf"}:
        mcp_dir = project / ".cursor"
        mcp_path = mcp_dir / "mcp.json"
        rule_path = mcp_dir / "rules" / "atlas.mdc"
        rule_text = _atlas_rule_text()
        files[str(mcp_path)] = json.dumps(CURSOR_MCP, indent=2) + "\n"
        files[str(rule_path)] = rule_text

        if write:
            actions.append(_merge_mcp(mcp_path, CURSOR_MCP))
            actions.append(_install_cursor_rule(rule_path))
            actions.extend(_install_cursor_skill(mcp_dir / "skills" / "atlas"))

            if global_install:
                home_cursor = Path.home() / ".cursor"
                actions.append(_install_cursor_rule(home_cursor / "rules" / "atlas.mdc"))
                actions.append(_merge_mcp(home_cursor / "mcp.json", CURSOR_MCP))
                actions.extend(_install_cursor_skill(home_cursor / "skills" / "atlas"))
                note = home_cursor / "atlas-DEFAULT.md"
                note.write_text(
                    "# Atlas is Cursor's default where-to-look / what-to-remember layer\n\n"
                    "Installed by `atlas connect --editor cursor`.\n\n"
                    "- Rule: ~/.cursor/rules/atlas.mdc (alwaysApply)\n"
                    "- MCP: ~/.cursor/mcp.json → atlas-mcp\n"
                    "- Skill: ~/.cursor/skills/atlas/\n"
                    "- Project copies under .cursor/ as well\n\n"
                    "Reload MCP or restart Cursor after install.\n",
                    encoding="utf-8",
                )
                actions.append(f"wrote {note}")

    elif editor in {"claude", "claude-code"}:
        mcp_path = project / ".mcp.json"
        snippet = json.dumps(CLAUDE_MCP, indent=2) + "\n"
        files[str(mcp_path)] = snippet
        agents = project / "CLAUDE.md"
        pointer = "\n\n## Atlas Memory\n\n" + GENERIC_RULE
        if write:
            mcp_path.write_text(snippet, encoding="utf-8")
            actions.append(f"wrote {mcp_path}")
            if agents.exists():
                text = agents.read_text(encoding="utf-8")
                if "Atlas Memory" not in text:
                    agents.write_text(text.rstrip() + pointer, encoding="utf-8")
                    actions.append(f"appended {agents}")
            else:
                agents.write_text("# Project\n" + pointer, encoding="utf-8")
                actions.append(f"wrote {agents}")

    else:
        out = project / ".atlas" / "CONNECT.md"
        http_note = (
            "HTTP daemon: `atlas daemon` then\n"
            "  GET http://127.0.0.1:8765/api/route?q=QUESTION&project=ROOT\n"
            "  GET http://127.0.0.1:8765/api/health\n"
            "MCP: configure your editor to run `atlas-mcp` on stdio.\n\n"
        )
        content = http_note + GENERIC_RULE
        files[str(out)] = content
        if write:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding="utf-8")
            actions.append(f"wrote {out}")

    atlas_bin = shutil.which("atlas-mcp") or shutil.which("atlas") or "atlas-mcp"
    return {
        "ok": True,
        "editor": editor,
        "project": str(project),
        "atlas_mcp": atlas_bin,
        "global_install": bool(global_install) if editor in {"cursor", "windsurf"} else False,
        "role": (
            "Cursor default where-to-look / what-to-remember layer"
            if editor == "cursor"
            else "editor integration"
        ),
        "actions": actions,
        "files": files if not write else None,
        "hint": "Reload Cursor MCP (or restart Cursor). Optional: atlas daemon",
    }
