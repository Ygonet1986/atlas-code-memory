"""CLI handlers for `atlas life` subcommands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import life as life_mod
from .drawer import LIFE_DRAWER_TYPES, LIFE_ROOMS


def _root(args: argparse.Namespace) -> Path | None:
    if getattr(args, "life_root", None):
        return Path(args.life_root)
    return None


def cmd_life(args: argparse.Namespace) -> int:
    sub = args.life_cmd
    root = _root(args)

    if sub == "init":
        result = life_mod.life_init(
            root,
            repo=args.repo,
            private_check=not args.skip_private_check,
            force=args.force,
        )
        print(json.dumps(result, indent=2) if args.json else _fmt_init(result))
        return 0 if result.get("ok") else 1

    if sub == "wake":
        result = life_mod.wake(root)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result.get("prompt", ""))
        return 0

    if sub == "remember":
        text = None
        if args.file:
            text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
        topics = [t.strip() for t in (args.topics or "").split(",") if t.strip()] or None
        drawer_text = args.text if args.text and args.text.strip().startswith("[type:") else None
        if drawer_text:
            result = life_mod.remember(root, drawer_text, push_after=args.push)
        elif text:
            result = life_mod.remember(root, text, push_after=args.push)
        else:
            summary = args.summary or (args.text if args.text and not args.text.startswith("[type:") else None)
            entities = [e.strip() for e in (args.entities or "").split(",") if e.strip()] or None
            result = life_mod.remember(
                root,
                None,
                type=args.type,
                summary=summary,
                why=args.why or "",
                topics=topics,
                entities=entities,
                room=args.room,
                period=args.period,
                when=args.when,
                push_after=args.push,
            )
        print(json.dumps(result, indent=2) if args.json else _fmt_ok(result))
        return 0 if result.get("ok") else 1

    if sub == "recall":
        result = life_mod.recall(root, args.question, limit=args.limit)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "rollup":
        result = life_mod.rollup(root, args.period, when=args.when, push_after=args.push)
        print(json.dumps(result, indent=2) if args.json else _fmt_ok(result))
        return 0 if result.get("ok") else 1

    if sub == "pull":
        result = life_mod.life_pull(root)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "push":
        result = life_mod.life_push(root, message=args.message)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "sync":
        result = life_mod.life_sync(root, message=args.message)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "serve":
        from .life_chat_server import serve
        from .paths import repo_root_from_pkg

        static = Path(args.static).resolve() if args.static else None
        if static is None and getattr(args, "with_ui", False):
            candidate = repo_root_from_pkg() / "apps" / "atlas-chat" / "dist"
            if candidate.is_dir():
                static = candidate
        serve(
            host=args.host,
            port=args.port,
            life_root=root,
            static_dir=static,
            open_browser=bool(getattr(args, "open", False)),
        )
        return 0

    if sub == "session-end":
        result = life_mod.prepare_session_init(
            root,
            summary=args.summary or "",
            topics=[t.strip() for t in (args.topics or "").split(",") if t.strip()] or None,
            greeting=args.greeting,
            push_after=args.push,
        )
        print(json.dumps(result, indent=2) if args.json else _fmt_ok(result))
        return 0 if result.get("ok") else 1

    if sub == "mindmap":
        result = life_mod.mindmap_graph(root, period=args.period)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "entities":
        result = life_mod.entity_list(root)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "entity":
        result = life_mod.entity_detail(root, name=args.entity_name)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "entity-graph":
        result = life_mod.entity_graph(root, name=args.entity_name)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "entity-relations":
        result = life_mod.entity_relations(root)
        print(json.dumps(result, indent=2))
        return 0

    if sub == "entity-merge":
        result = life_mod.entity_merge(root, args.source, args.target)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "entity-alias":
        result = life_mod.entity_add_alias(root, args.entity_name, args.alias)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "pin":
        result = life_mod.pin_drawer(args.drawer_path)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "unpin":
        result = life_mod.unpin_drawer(args.drawer_path)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if sub == "autostart":
        from . import life_autostart

        if args.autostart_cmd == "install":
            result = life_autostart.install_autostart(url=args.url)
        else:
            result = life_autostart.uninstall_autostart()
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    print(f"unknown life command: {sub}", file=sys.stderr)
    return 1


def _fmt_init(result: dict) -> str:
    if not result.get("ok"):
        return f"FAIL: {result.get('error')}"
    lines = [f"OK life root: {result.get('root')}"]
    for a in result.get("actions") or []:
        lines.append(f"  {a}")
    return "\n".join(lines)


def _fmt_ok(result: dict) -> str:
    if not result.get("ok"):
        errs = result.get("errors") or [result.get("error")]
        return "FAIL:\n" + "\n".join(f"  - {e}" for e in errs)
    return f"OK {result.get('path')}"


def register_life_parser(sub: argparse._SubParsersAction) -> None:
    life = sub.add_parser("life", help="personal conversation memory (GitHub private + temporal drawers)")
    ls = life.add_subparsers(dest="life_cmd", required=True)

    def add_root(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--life-root",
            "-C",
            dest="life_root",
            default=None,
            help="atlas-life root (default: $ATLAS_LIFE_ROOT or ~/atlas-life)",
        )
        sp.add_argument("--json", action="store_true")

    p = ls.add_parser("init", help="create/clone private life palace")
    add_root(p)
    p.add_argument("--repo", help="OWNER/atlas-life GitHub repo")
    p.add_argument("--force", action="store_true")
    p.add_argument(
        "--skip-private-check",
        action="store_true",
        help="skip gh isPrivate check (not recommended)",
    )
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("wake", help="L0 hot set for today")
    add_root(p)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("remember", help="write a life drawer for today")
    add_root(p)
    p.add_argument("--text", help="summary sentence OR full drawer markdown starting with [type:")
    p.add_argument("--summary", help="summary when not using drawer markdown")
    p.add_argument("--file", help="drawer file or - for stdin")
    p.add_argument("--type", default="memory", choices=sorted(LIFE_DRAWER_TYPES))
    p.add_argument("--why", default="")
    p.add_argument("--topics", default="")
    p.add_argument(
        "--entities",
        default="",
        help="comma-separated entity names (people, places, concepts)",
    )
    p.add_argument("--room", default="day", choices=list(LIFE_ROOMS))
    p.add_argument("--period", default="day", choices=["day", "week", "month", "year"])
    p.add_argument("--when", default=None)
    p.add_argument("--push", action="store_true", help="commit+push after write")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("recall", help="route a question to temporal drawers")
    add_root(p)
    p.add_argument("question")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("rollup", help="consolidate period into a summary drawer")
    add_root(p)
    p.add_argument("period", choices=["day", "week", "month", "year"])
    p.add_argument("--when", default=None)
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("pull", help="git pull --rebase")
    add_root(p)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("push", help="commit dirty life files and push")
    add_root(p)
    p.add_argument("-m", "--message", default=None)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("sync", help="pull, commit if dirty, push")
    add_root(p)
    p.add_argument("-m", "--message", default=None)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("serve", help="HTTP sidecar for Atlas Chat (DeepSeek + life API)")
    add_root(p)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--static", default=None, help="optional static UI directory")
    p.add_argument("--with-ui", action="store_true", help="serve apps/atlas-chat/dist if present")
    p.add_argument("--open", action="store_true", help="open browser when ready")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("session-end", help="write session init for next wake")
    add_root(p)
    p.add_argument("--summary", default="")
    p.add_argument("--topics", default="")
    p.add_argument("--greeting", default=None)
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("mindmap", help="JSON graph for Mind Map tab")
    add_root(p)
    p.add_argument("--period", default="day", choices=["day", "week", "month", "year", "people"])
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entities", help="list all known entities")
    add_root(p)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entity", help="detail for a named entity")
    add_root(p)
    p.add_argument("entity_name", help="entity name")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entity-graph", help="Mind Map graph for a named entity")
    add_root(p)
    p.add_argument("entity_name", help="entity name")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entity-relations", help="co-occurrence graph between entities")
    add_root(p)
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entity-merge", help="merge source entity into target")
    add_root(p)
    p.add_argument("source", help="source entity name")
    p.add_argument("target", help="target entity name")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("entity-alias", help="add an alias to an entity")
    add_root(p)
    p.add_argument("entity_name", help="entity name")
    p.add_argument("alias", help="alias to add")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("pin", help="pin a drawer to always appear in hot set")
    p.add_argument("drawer_path", help="path to .drawer.md file")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("unpin", help="unpin a drawer from hot set")
    p.add_argument("drawer_path", help="path to .drawer.md file")
    p.set_defaults(func=cmd_life)

    p = ls.add_parser("autostart", help="install/uninstall Windows Startup shortcut")
    asub = p.add_subparsers(dest="autostart_cmd", required=True)
    i = asub.add_parser("install")
    i.add_argument("--url", default="http://127.0.0.1:8765/")
    i.set_defaults(func=cmd_life)
    u = asub.add_parser("uninstall")
    u.set_defaults(func=cmd_life)
