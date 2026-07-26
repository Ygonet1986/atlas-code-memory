from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, metrics
from .commands_checkpoint import file_checkpoint
from .commands_doctor import doctor
from .commands_eval import run_eval
from .commands_graph import add_graph, list_graphs, set_graph_status
from .commands_hooks import install_git_hooks
from .commands_import import import_docs
from .commands_init import init_project
from .commands_migrate import migrate_project
from .commands_onboard import onboard
from .commands_stale import mark_stale_touched, stale_report
from .commands_sync import export_bundle, import_bundle
from .commands_watch import watch_project
from .drawer import parse_drawer_markdown, validate_drawer
from .routing import protocol_score, recall_route
from .telemetry import maybe_send_telemetry


def _project(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "project", ".") or ".").resolve()


def cmd_init(args: argparse.Namespace) -> int:
    actions = init_project(_project(args), force=args.force, global_rule=args.global_rule)
    for a in actions:
        print(a)
    print(f"atlas init: done ({_project(args)})")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = _project(args)
    print(f"Atlas status: {root}")
    for rel in (
        ".cursor/mempalace-index.md",
        ".cursor/graphify-index.md",
        ".cursor/project-cache.md",
        ".cursor/rules/atlas.mdc",
        ".cursor/skills/atlas/SKILL.md",
        ".atlasignore",
        "mempalace.yaml",
    ):
        p = root / rel
        print(f"  {'OK  ' if p.exists() else 'MISS'} {rel}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    rows = doctor(_project(args))
    worst = 0
    for name, status, detail in rows:
        mark = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}[status]
        print(f"  {mark} {name}: {detail}")
        if status == "fail":
            worst = 1
    metrics.record(_project(args), "doctor")
    return worst


def cmd_stale(args: argparse.Namespace) -> int:
    reports = stale_report(_project(args))
    if not reports:
        print("atlas stale: no graphify-index entries")
        return 0
    for r in reports:
        label = ", ".join(r.issues) if r.issues else "ok"
        print(f"{r.name}: {label} (status={r.status}, escopo={r.escopo})")
    metrics.record(_project(args), "stale")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    for a in import_docs(_project(args)):
        print(a)
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    if args.file == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.file).read_text(encoding="utf-8")
    root = _project(args)
    if args.write or args.mine:
        result = file_checkpoint(root, text, mine=args.mine)
        if args.json:
            print(json.dumps(result, indent=2))
        elif not result.get("ok"):
            print("FAIL validation:")
            for e in result.get("errors", []):
                print(f"  - {e}")
            return 1
        else:
            print("OK wrote", result.get("path"))
            if result.get("mine"):
                print("mine:", result["mine"])
        metrics.record(root, "checkpoint", ok=True, wrote=True)
        return 0

    try:
        drawer = parse_drawer_markdown(text)
    except ValueError as e:
        print(f"FAIL parse: {e}", file=sys.stderr)
        return 1
    errors = validate_drawer(drawer)
    if args.json:
        print(json.dumps({"drawer": drawer.to_dict(), "errors": errors}, indent=2))
    else:
        if errors:
            print("FAIL validation:")
            for e in errors:
                print(f"  - {e}")
        else:
            print("OK drawer")
            print(drawer.to_markdown())
    metrics.record(root, "checkpoint", ok=not errors)
    return 1 if errors else 0


def cmd_eval(args: argparse.Namespace) -> int:
    root = _project(args)
    if args.transcript:
        text = Path(args.transcript).read_text(encoding="utf-8") if args.transcript != "-" else sys.stdin.read()
        result = protocol_score(text)
        print(json.dumps(result, indent=2))
        metrics.record(root, "eval_protocol", score=result["score"])
        return 0 if result["pass"] else 1
    cases = Path(args.cases) if args.cases else None
    results = run_eval(root, cases)
    passed = sum(1 for r in results if r["pass"])
    for r in results:
        flag = "PASS" if r["pass"] else "FAIL"
        print(f"  {flag} {r['id']}: [{r['expect_layer']}] {r['question']}")
    print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


def cmd_hooks(args: argparse.Namespace) -> int:
    root = _project(args)
    if args.hooks_cmd == "install":
        for a in install_git_hooks(root):
            print(a)
        return 0
    if args.hooks_cmd == "mark-stale":
        files: list[str] = []
        if args.stdin:
            files = [ln.strip() for ln in sys.stdin if ln.strip()]
        else:
            import subprocess

            try:
                out = subprocess.check_output(
                    ["git", "-C", str(root), "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                    text=True,
                )
                files = [ln.strip() for ln in out.splitlines() if ln.strip()]
            except Exception:
                files = []
        updated = mark_stale_touched(root, files)
        if updated:
            print("marked stale:", ", ".join(updated))
            metrics.record(root, "mark_stale", names=updated)
        else:
            print("no index entries to mark stale")
        return 0
    return 1


def cmd_metrics(args: argparse.Namespace) -> int:
    data = metrics.summary(_project(args))
    print(json.dumps(data.get("events", data), indent=2))
    if args.send:
        print(json.dumps(maybe_send_telemetry(_project(args)), indent=2))
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    root = _project(args)
    if args.graph_cmd == "list":
        for e in list_graphs(root):
            print(f"{e['name']}\t{e['status']}\t{e['escopo']}")
        return 0
    if args.graph_cmd == "add":
        print(add_graph(root, args.name, args.escopo, args.description or "", args.status))
        metrics.record(root, "graph_add", name=args.name)
        return 0
    if args.graph_cmd == "ready":
        print(set_graph_status(root, args.name, "ready"))
        return 0
    if args.graph_cmd == "stale":
        print(set_graph_status(root, args.name, "stale"))
        return 0
    return 1


def cmd_migrate(args: argparse.Namespace) -> int:
    for a in migrate_project(_project(args)):
        print(a)
    return 0


def cmd_onboard(args: argparse.Namespace) -> int:
    for a in onboard(_project(args)):
        print(a)
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    root = _project(args)
    if args.sync_cmd == "export":
        path = export_bundle(root, Path(args.output) if args.output else None)
        print(path)
        metrics.record(root, "sync_export")
        return 0
    if args.sync_cmd == "import":
        for a in import_bundle(root, Path(args.bundle), merge_cache=not args.replace_cache):
            print(a)
        metrics.record(root, "sync_import")
        return 0
    return 1


def cmd_watch(args: argparse.Namespace) -> int:
    watch_project(_project(args), interval=args.interval, once=args.once)
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    result = recall_route(_project(args), args.question)
    print(json.dumps(result, indent=2))
    metrics.record(_project(args), "route")
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import run_mcp

    run_mcp()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="atlas", description="Atlas Memory — AI coding memory router")
    p.add_argument("--version", action="version", version=f"atlas-memory {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_project(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("-C", "--project", default=".", help="project root (default: .)")

    s = sub.add_parser("init", help="create missing Atlas files")
    add_project(s)
    s.add_argument("--force", action="store_true")
    s.add_argument("--global-rule", action="store_true")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("status", help="show which Atlas files exist")
    add_project(s)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("doctor", help="diagnose adapters and indexes")
    add_project(s)
    s.set_defaults(func=cmd_doctor)

    s = sub.add_parser("stale", help="report stale/missing scoped graphs")
    add_project(s)
    s.set_defaults(func=cmd_stale)

    s = sub.add_parser("import", help="seed cache/drawers from README and ADRs")
    add_project(s)
    s.set_defaults(func=cmd_import)

    s = sub.add_parser("checkpoint", help="validate drawer; optional --write/--mine")
    add_project(s)
    s.add_argument("file", help="path or - for stdin")
    s.add_argument("--json", action="store_true")
    s.add_argument("--write", action="store_true", help="write under .cursor/atlas-drawers/<room>/")
    s.add_argument("--mine", action="store_true", help="write + mempalace mine that room folder")
    s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("eval", help="index harness or --transcript protocol score")
    add_project(s)
    s.add_argument("--cases", help="directory of JSON cases")
    s.add_argument("--transcript", help="path or - for protocol scoring")
    s.set_defaults(func=cmd_eval)

    s = sub.add_parser("hooks", help="git hook helpers")
    add_project(s)
    s.add_argument("hooks_cmd", choices=["install", "mark-stale"])
    s.add_argument("--stdin", action="store_true")
    s.set_defaults(func=cmd_hooks)

    s = sub.add_parser("metrics", help="local counters; --send for opt-in telemetry")
    add_project(s)
    s.add_argument("--send", action="store_true")
    s.set_defaults(func=cmd_metrics)

    s = sub.add_parser("graph", help="manage graphify-index entries")
    gs = s.add_subparsers(dest="graph_cmd", required=True)
    g = gs.add_parser("list")
    add_project(g)
    g.set_defaults(func=cmd_graph)
    g = gs.add_parser("add")
    add_project(g)
    g.add_argument("name")
    g.add_argument("--escopo", required=True)
    g.add_argument("--description", default="")
    g.add_argument("--status", default="missing", choices=["ready", "missing", "stale"])
    g.set_defaults(func=cmd_graph)
    g = gs.add_parser("ready")
    add_project(g)
    g.add_argument("name")
    g.set_defaults(func=cmd_graph)
    g = gs.add_parser("stale")
    add_project(g)
    g.add_argument("name")
    g.set_defaults(func=cmd_graph)

    s = sub.add_parser("migrate", help="migrate legacy cursor memory files to Atlas")
    add_project(s)
    s.set_defaults(func=cmd_migrate)

    s = sub.add_parser("onboard", help="bootstrap + brief + onboard skill")
    add_project(s)
    s.set_defaults(func=cmd_onboard)

    s = sub.add_parser("sync", help="export/import Atlas bundles for teams")
    ss = s.add_subparsers(dest="sync_cmd", required=True)
    e = ss.add_parser("export")
    add_project(e)
    e.add_argument("-o", "--output")
    e.set_defaults(func=cmd_sync)
    i = ss.add_parser("import")
    add_project(i)
    i.add_argument("bundle")
    i.add_argument("--replace-cache", action="store_true")
    i.set_defaults(func=cmd_sync)

    s = sub.add_parser("watch", help="poll scopes and mark stale on change")
    add_project(s)
    s.add_argument("--interval", type=float, default=2.0)
    s.add_argument("--once", action="store_true")
    s.set_defaults(func=cmd_watch)

    s = sub.add_parser("route", help="JSON recall route for a question")
    add_project(s)
    s.add_argument("question")
    s.set_defaults(func=cmd_route)

    s = sub.add_parser("mcp", help="run Atlas MCP server on stdio")
    s.set_defaults(func=cmd_mcp)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
