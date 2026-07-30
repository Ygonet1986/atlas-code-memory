"""Atlas local daemon — HTTP API for any AI editor (+ optional life chat)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from . import __version__, life as life_mod
from .commands_bench import format_bench_markdown, run_bench
from .commands_cache import build_cache, cache_status
from .http_auth import DEFAULT_ALLOWED_ORIGINS, token_path
from .life_chat_server import (
    _json_response,
    _query_params,
    _read_json,
    _root_from_query,
    make_handler as make_life_handler,
)
from .routing import recall_route


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def config_dir() -> Path:
    return Path.home() / ".atlas"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {
            "host": DEFAULT_HOST,
            "port": DEFAULT_PORT,
            "life_root": None,
            "default_project": None,
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"host": DEFAULT_HOST, "port": DEFAULT_PORT}


def save_config(data: dict[str, Any]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = load_config()
    merged.update(data)
    path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return path


def make_daemon_handler(
    *,
    life_root: Path | None,
    default_project: Path | None,
    static_dir: Path | None,
    auth_token: str | None = None,
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS,
) -> type[BaseHTTPRequestHandler]:
    LifeHandler = make_life_handler(
        life_root, static_dir, auth_token=auth_token, allowed_origins=allowed_origins
    )

    class Handler(LifeHandler):  # type: ignore[valid-type,misc]
        def do_GET(self) -> None:  # noqa: N802
            if not self.guard():
                return
            path = urlparse(self.path).path
            params = _query_params(self.path)
            if path == "/api/health":
                # Reachable without a token, so it must stay free of local paths.
                if not self.authenticated():
                    _json_response(self, 200, {"ok": True, "service": "atlas-memory", "auth": "required"})
                    return
                cfg = load_config()
                _json_response(
                    self,
                    200,
                    {
                        "ok": True,
                        "service": "atlas-daemon",
                        "version": __version__,
                        "life_root": str(life_mod.life_root(life_root)),
                        "default_project": str(default_project) if default_project else cfg.get("default_project"),
                    },
                )
                return
            if path == "/api/route":
                q = unquote(params.get("q") or params.get("question") or "")
                proj = params.get("project") or (str(default_project) if default_project else ".")
                project = Path(unquote(proj)).expanduser().resolve()
                result = recall_route(project, q)
                _json_response(self, 200, result)
                return
            if path == "/api/bench":
                proj = params.get("project")
                project = Path(unquote(proj)).expanduser().resolve() if proj else None
                report = run_bench(project)
                _json_response(self, 200, report)
                return
            if path == "/api/cache":
                proj = params.get("project") or (str(default_project) if default_project else ".")
                project = Path(unquote(proj)).expanduser().resolve()
                _json_response(self, 200, cache_status(project))
                return
            # Fall through to life chat handler
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802
            if not self.guard():
                return
            path = urlparse(self.path).path
            body = _read_json(self)
            if path == "/api/route":
                q = body.get("question") or body.get("q") or ""
                proj = body.get("project") or (str(default_project) if default_project else ".")
                project = Path(proj).expanduser().resolve()
                _json_response(self, 200, recall_route(project, q))
                return
            if path == "/api/bench":
                proj = body.get("project")
                project = Path(proj).expanduser().resolve() if proj else None
                report = run_bench(project)
                if body.get("markdown"):
                    _json_response(self, 200, {"ok": report.get("ok"), "markdown": format_bench_markdown(report), "report": report})
                else:
                    _json_response(self, 200, report)
                return
            if path == "/api/cache":
                proj = body.get("project") or (str(default_project) if default_project else ".")
                project = Path(proj).expanduser().resolve()
                _json_response(
                    self,
                    200,
                    build_cache(
                        project,
                        force=bool(body.get("force")),
                        prune=bool(body.get("prune")),
                        dry_run=bool(body.get("dry_run")),
                    ),
                )
                return
            if path == "/api/config":
                path_written = save_config(body)
                _json_response(self, 200, {"ok": True, "path": str(path_written), "config": load_config()})
                return
            super().do_POST()

    return Handler


def serve_daemon(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    life_root: Path | None = None,
    default_project: Path | None = None,
    static_dir: Path | None = None,
    open_browser: bool = False,
    auth_token: str | None = None,
) -> None:
    cfg = load_config()
    host = host or cfg.get("host") or DEFAULT_HOST
    port = int(port or cfg.get("port") or DEFAULT_PORT)
    if life_root is None and cfg.get("life_root"):
        life_root = Path(cfg["life_root"]).expanduser()
    if default_project is None and cfg.get("default_project"):
        default_project = Path(cfg["default_project"]).expanduser()

    save_config(
        {
            "host": host,
            "port": port,
            "life_root": str(life_root) if life_root else cfg.get("life_root"),
            "default_project": str(default_project) if default_project else cfg.get("default_project"),
        }
    )

    handler = make_daemon_handler(
        life_root=life_root,
        default_project=default_project,
        static_dir=static_dir,
        auth_token=auth_token,
    )
    token = getattr(handler, "auth_token", "")
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"atlas daemon {url} version={__version__} life={life_mod.life_root(life_root)}")
    if token:
        print(f"  token: {token}   (also in {token_path()})")
        print(f"  usage: curl -H 'Authorization: Bearer {token}' '{url}api/route?q=...'")
    else:
        print("  WARNING: --no-auth — any page in your browser can read and write your memories")
    if open_browser:
        import webbrowser

        def _open() -> None:
            import time

            time.sleep(0.4)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()
    httpd.serve_forever()
