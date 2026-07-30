"""Wire Atlas into an AI editor as its where-to-look / what-to-remember layer.

Each editor reads its rules and MCP config from different paths, so the writers
below are per-editor rather than a single Cursor-shaped template.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .paths import data_dir


SUPPORTED_EDITORS = (
    "cursor",
    "windsurf",
    "vscode",
    "copilot",
    "zed",
    "claude",
    "claude-code",
    "codex",
    "generic",
)

# Editors whose MCP config uses the `mcpServers` object.
MCP_SERVER_ENTRY = {"command": "atlas-mcp"}
CURSOR_MCP = {"mcpServers": {"atlas-memory": MCP_SERVER_ENTRY}}
CLAUDE_MCP = {"mcpServers": {"atlas-memory": MCP_SERVER_ENTRY}}
# VS Code / Copilot use `servers` in .vscode/mcp.json.
VSCODE_MCP = {"servers": {"atlas-memory": {**MCP_SERVER_ENTRY, "type": "stdio"}}}
# Zed calls them context servers.
ZED_CONTEXT_SERVER = {
    "context_servers": {
        "atlas-memory": {"command": {"path": "atlas-mcp", "args": []}, "settings": {}}
    }
}

GENERIC_RULE = """# Atlas Memory (token GPS)

Before grepping a monorepo, call Atlas:

1. `atlas_recall_route` (MCP) or `GET http://127.0.0.1:8765/api/route?q=...&project=...`
2. Open only the returned cache_hits / graph scopes
3. Persist durable decisions with `atlas_checkpoint` / life remember

Never invent memory hits. Missing layer → skip.
"""

CODEX_TOML_SNIPPET = """[mcp_servers.atlas-memory]
command = "atlas-mcp"
args = []
"""


def _atlas_rule_text() -> str:
    src = data_dir("cursor", "rules", "atlas.mdc")
    if src.exists():
        return src.read_text(encoding="utf-8")
    return (
        "---\ndescription: Atlas — where to look / what to remember\nalwaysApply: true\n---\n\n"
        + GENERIC_RULE
    )


def _rule_body(editor_label: str) -> str:
    """Rule text without Cursor's .mdc frontmatter, retargeted at another editor."""
    text = _atlas_rule_text()
    body = re.sub(r"\A---\n.*?\n---\n+", "", text, flags=re.S)
    # Keep the lowercase `--editor cursor` example intact; only retarget prose.
    return re.sub(r"\bCursor\b", editor_label, body)


def _write(path: Path, content: str, actions: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    path.write_text(content, encoding="utf-8")
    actions.append(f"{'updated' if existed else 'wrote'} {path}")


def _merge_json_config(path: Path, snippet: dict[str, Any], top_key: str) -> str:
    """Merge the atlas server into an existing JSON config, preserving siblings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    existing: dict[str, Any] = {}
    if existed:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Config may be JSONC (Zed, VS Code). Never clobber what we cannot parse.
            fallback = path.parent / f"atlas-{path.stem}.snippet.json"
            fallback.write_text(json.dumps(snippet, indent=2) + "\n", encoding="utf-8")
            return f"could not parse {path} — wrote snippet to merge manually: {fallback}"
    if not isinstance(existing, dict):
        existing = {}
    servers = existing.setdefault(top_key, {})
    if not isinstance(servers, dict):
        servers = {}
        existing[top_key] = servers
    servers["atlas-memory"] = snippet[top_key]["atlas-memory"]
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return f"{'updated' if existed else 'wrote'} {path}"


def _merge_mcp(path: Path, snippet: dict[str, Any]) -> str:
    return _merge_json_config(path, snippet, "mcpServers")


def _install_cursor_rule(dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    existed = dest.exists()
    dest.write_text(_atlas_rule_text(), encoding="utf-8")
    return f"{'updated' if existed else 'wrote'} {dest}"


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


def _append_section(path: Path, marker: str, section: str, actions: list[str]) -> None:
    """Append an Atlas section to an instructions file without duplicating it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="replace")
        if marker in text:
            actions.append(f"keep {path} (already wired)")
            return
        path.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")
        actions.append(f"appended {path}")
    else:
        path.write_text(section, encoding="utf-8")
        actions.append(f"wrote {path}")


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
    marker = "<!-- atlas-memory -->"

    if global_install is None:
        global_install = editor == "cursor"

    if editor == "cursor":
        mcp_dir = project / ".cursor"
        mcp_path = mcp_dir / "mcp.json"
        rule_path = mcp_dir / "rules" / "atlas.mdc"
        files[str(mcp_path)] = json.dumps(CURSOR_MCP, indent=2) + "\n"
        files[str(rule_path)] = _atlas_rule_text()

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

    elif editor == "windsurf":
        rule_path = project / ".windsurf" / "rules" / "atlas.md"
        rule_text = _rule_body("Windsurf")
        mcp_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
        files[str(rule_path)] = rule_text
        files[str(mcp_path)] = json.dumps(CURSOR_MCP, indent=2) + "\n"
        if write:
            _write(rule_path, rule_text, actions)
            if global_install:
                actions.append(_merge_mcp(mcp_path, CURSOR_MCP))
            else:
                actions.append(f"skipped {mcp_path} (--no-global)")

    elif editor in {"vscode", "copilot"}:
        mcp_path = project / ".vscode" / "mcp.json"
        instructions = project / ".github" / "copilot-instructions.md"
        section = marker + "\n" + _rule_body("VS Code")
        files[str(mcp_path)] = json.dumps(VSCODE_MCP, indent=2) + "\n"
        files[str(instructions)] = section
        if write:
            actions.append(_merge_json_config(mcp_path, VSCODE_MCP, "servers"))
            _append_section(instructions, marker, section, actions)

    elif editor == "zed":
        rule_path = project / ".rules"
        rule_text = _rule_body("Zed")
        settings = Path.home() / ".config" / "zed" / "settings.json"
        files[str(rule_path)] = rule_text
        files[str(settings)] = json.dumps(ZED_CONTEXT_SERVER, indent=2) + "\n"
        if write:
            _write(rule_path, rule_text, actions)
            if global_install:
                actions.append(_merge_json_config(settings, ZED_CONTEXT_SERVER, "context_servers"))
            else:
                actions.append(f"skipped {settings} (--no-global)")

    elif editor in {"claude", "claude-code"}:
        mcp_path = project / ".mcp.json"
        snippet = json.dumps(CLAUDE_MCP, indent=2) + "\n"
        agents = project / "CLAUDE.md"
        section = marker + "\n## Atlas Memory\n\n" + GENERIC_RULE
        files[str(mcp_path)] = snippet
        files[str(agents)] = section
        if write:
            actions.append(_merge_mcp(mcp_path, CLAUDE_MCP))
            _append_section(agents, marker, section, actions)

    elif editor == "codex":
        agents = project / "AGENTS.md"
        section = marker + "\n## Atlas Memory\n\n" + GENERIC_RULE
        toml_hint = project / ".atlas" / "codex-config.toml"
        files[str(agents)] = section
        files[str(toml_hint)] = CODEX_TOML_SNIPPET
        if write:
            _append_section(agents, marker, section, actions)
            _write(toml_hint, CODEX_TOML_SNIPPET, actions)
            actions.append("append .atlas/codex-config.toml into ~/.codex/config.toml")

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
            _write(out, content, actions)

    atlas_bin = shutil.which("atlas-mcp") or shutil.which("atlas") or "atlas-mcp"
    supports_global = editor in {"cursor", "windsurf", "zed"}
    return {
        "ok": True,
        "editor": editor,
        "project": str(project),
        "atlas_mcp": atlas_bin,
        "global_install": bool(global_install) if supports_global else False,
        "role": (
            "Cursor default where-to-look / what-to-remember layer"
            if editor == "cursor"
            else "editor integration"
        ),
        "actions": actions,
        "files": files if not write else None,
        "hint": "Reload the editor's MCP servers after install. Optional: atlas daemon",
    }
