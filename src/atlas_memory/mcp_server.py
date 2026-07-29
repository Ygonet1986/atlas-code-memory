from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .commands_stale import stale_report
from .drawer import parse_drawer_markdown, validate_drawer
from . import life as life_mod
from .routing import protocol_score, recall_route


def run_mcp() -> None:
    """Minimal stdio MCP server (JSON-RPC style subset for Cursor)."""
    import sys

    def reply(msg_id: Any, result: Any) -> None:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": result}) + "\n")
        sys.stdout.flush()

    def fail(msg_id: Any, code: int, message: str) -> None:
        sys.stdout.write(
            json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}})
            + "\n"
        )
        sys.stdout.flush()

    tools = [
        {
            "name": "atlas_recall_route",
            "description": "Route a question through Atlas indexes (wing/room, graphs, cache hits).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project root path"},
                    "question": {"type": "string"},
                },
                "required": ["question"],
            },
        },
        {
            "name": "atlas_checkpoint",
            "description": "Validate an Atlas drawer markdown (schema + secrets).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "write_path": {
                        "type": "string",
                        "description": "Optional path to write validated drawer under project",
                    },
                    "project": {"type": "string"},
                },
                "required": ["text"],
            },
        },
        {
            "name": "atlas_stale",
            "description": "Report stale/missing Graphify scopes for a project.",
            "inputSchema": {
                "type": "object",
                "properties": {"project": {"type": "string"}},
            },
        },
        {
            "name": "atlas_protocol_score",
            "description": "Score an agent transcript for Atlas protocol compliance (heuristic).",
            "inputSchema": {
                "type": "object",
                "properties": {"transcript": {"type": "string"}},
                "required": ["transcript"],
            },
        },
        {
            "name": "atlas_life_wake",
            "description": "Life palace L0 wake: today hot drawers + week/people snippets.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string", "description": "atlas-life root (optional)"},
                },
            },
        },
        {
            "name": "atlas_life_remember",
            "description": "Write a validated life drawer (day by default); optional git push.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "text": {"type": "string", "description": "Full drawer markdown"},
                    "type": {"type": "string"},
                    "summary": {"type": "string"},
                    "why": {"type": "string"},
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "entities": {"type": "array", "items": {"type": "string"}, "description": "Named entities (people, objects, places) to link this drawer to"},
                    "room": {"type": "string"},
                    "period": {"type": "string"},
                    "when": {"type": "string"},
                    "push": {"type": "boolean"},
                },
            },
        },
        {
            "name": "atlas_life_recall",
            "description": "Route a life question to temporal drawers (day/week/month/year/people).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "question": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["question"],
            },
        },
        {
            "name": "atlas_life_entity_list",
            "description": "List all known entities with drawer ref counts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                },
            },
        },
        {
            "name": "atlas_life_entity_detail",
            "description": "Get all drawers linked to a named entity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "name": {"type": "string", "description": "Entity name"},
                },
                "required": ["name"],
            },
        },
        {
            "name": "atlas_life_entity_graph",
            "description": "Build a Mind Map graph for a single entity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "name": {"type": "string", "description": "Entity name"},
                },
                "required": ["name"],
            },
        },
        {
            "name": "atlas_life_entity_relations",
            "description": "Co-occurrence graph between entities (entities appearing in the same drawers).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                },
            },
        },
        {
            "name": "atlas_life_entity_merge",
            "description": "Merge source entity into target (move refs, add as alias).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "source": {"type": "string", "description": "Source entity name"},
                    "target": {"type": "string", "description": "Target entity name"},
                },
                "required": ["source", "target"],
            },
        },
        {
            "name": "atlas_life_entity_alias",
            "description": "Add an alias to an existing entity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "name": {"type": "string", "description": "Entity name"},
                    "alias": {"type": "string", "description": "Alias to add"},
                },
                "required": ["name", "alias"],
            },
        },
        {
            "name": "atlas_life_rollup",
            "description": "Consolidate a life period into a summary drawer.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "life_root": {"type": "string"},
                    "period": {"type": "string", "enum": ["day", "week", "month", "year"]},
                    "when": {"type": "string"},
                    "push": {"type": "boolean"},
                },
                "required": ["period"],
            },
        },
    ]

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        msg_id = req.get("id")
        params = req.get("params") or {}

        if method == "initialize":
            reply(
                msg_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "atlas-memory", "version": "0.3.0"},
                },
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            reply(msg_id, {"tools": tools})
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            project = Path(args.get("project") or ".").resolve()
            life_root = Path(args["life_root"]).expanduser() if args.get("life_root") else None
            try:
                if name == "atlas_recall_route":
                    result = recall_route(project, args.get("question", ""))
                elif name == "atlas_checkpoint":
                    text = args.get("text", "")
                    drawer = parse_drawer_markdown(text)
                    errors = validate_drawer(drawer)
                    written = None
                    if not errors and args.get("write_path"):
                        dest = project / args["write_path"]
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(drawer.to_markdown(), encoding="utf-8")
                        written = str(dest)
                    result = {"ok": not errors, "errors": errors, "drawer": drawer.to_dict(), "written": written}
                elif name == "atlas_stale":
                    result = [
                        {
                            "name": r.name,
                            "scope": r.scope,
                            "status": r.status,
                            "issues": r.issues,
                        }
                        for r in stale_report(project)
                    ]
                elif name == "atlas_protocol_score":
                    result = protocol_score(args.get("transcript", ""))
                elif name == "atlas_life_wake":
                    result = life_mod.wake(life_root)
                elif name == "atlas_life_remember":
                    if args.get("text"):
                        result = life_mod.remember(
                            life_root, args["text"], push_after=bool(args.get("push"))
                        )
                    else:
                        result = life_mod.remember(
                            life_root,
                            None,
                            type=args.get("type") or "memory",
                            summary=args.get("summary"),
                            why=args.get("why") or "",
                            topics=args.get("topics"),
                            entities=args.get("entities"),
                            room=args.get("room") or "day",
                            period=args.get("period") or "day",
                            when=args.get("when"),
                            push_after=bool(args.get("push")),
                        )
                elif name == "atlas_life_recall":
                    result = life_mod.recall(
                        life_root, args.get("question", ""), limit=int(args.get("limit") or 10)
                    )
                elif name == "atlas_life_entity_list":
                    result = life_mod.entity_list(life_root)
                elif name == "atlas_life_entity_detail":
                    result = life_mod.entity_detail(life_root, name=args.get("name", ""))
                elif name == "atlas_life_entity_graph":
                    result = life_mod.entity_graph(life_root, name=args.get("name", ""))
                elif name == "atlas_life_entity_relations":
                    result = life_mod.entity_relations(life_root)
                elif name == "atlas_life_entity_merge":
                    result = life_mod.entity_merge(life_root, args.get("source", ""), args.get("target", ""))
                elif name == "atlas_life_entity_alias":
                    result = life_mod.entity_add_alias(life_root, args.get("name", ""), args.get("alias", ""))
                elif name == "atlas_life_rollup":
                    result = life_mod.rollup(
                        life_root,
                        args.get("period", "day"),
                        when=args.get("when"),
                        push_after=bool(args.get("push")),
                    )
                else:
                    fail(msg_id, -32601, f"unknown tool {name}")
                    continue
                reply(
                    msg_id,
                    {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
                )
            except Exception as e:
                fail(msg_id, -32000, str(e))
        elif method == "ping":
            reply(msg_id, {})
        else:
            if msg_id is not None:
                fail(msg_id, -32601, f"method not found: {method}")


def main() -> None:
    run_mcp()


if __name__ == "__main__":
    main()
