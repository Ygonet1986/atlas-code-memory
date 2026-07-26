from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .commands_stale import parse_graphify_index, stale_report
from .drawer import parse_drawer_markdown, validate_drawer
from .routing import protocol_score, recall_route


def run_mcp() -> None:
    """Minimal stdio MCP server (JSON-RPC style subset for Cursor)."""
    # Lazy import-free loop: Cursor MCP expects JSON-RPC over stdin/stdout.
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
                    "serverInfo": {"name": "atlas-memory", "version": "0.2.0"},
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
                        {"name": r.name, "escopo": r.escopo, "status": r.status, "issues": r.issues}
                        for r in stale_report(project)
                    ]
                elif name == "atlas_protocol_score":
                    result = protocol_score(args.get("transcript", ""))
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
