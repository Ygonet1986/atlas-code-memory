"""HTTP sidecar for Atlas Chat desktop (DeepSeek + life core)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import life as life_mod

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
SYSTEM_BASE = """You are Atlas Life, a personal memory assistant.
Follow Atlas protocol: use the Wake context; never invent memories.
After your reply, if the user shared durable facts, append a JSON block on its own line:
{"memories":[{"type":"memory|event|person|goal|preference|lesson|decision","summary":"...","why":"...","topics":["..."],"entities":["..."]}]}
If nothing durable, omit the JSON entirely. Never include API keys or secrets.
"""


def _json_response(handler: BaseHTTPRequestHandler, code: int, payload: Any) -> None:
    handler.send_response(code)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    if code == 204:
        handler.end_headers()
        return
    body = json.dumps(payload).encode("utf-8")
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def deepseek_chat(messages: list[dict[str, str]], *, model: str | None = None) -> dict[str, Any]:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "error": "DEEPSEEK_API_KEY not set"}
    model = model or os.environ.get("ATLAS_CHAT_MODEL", "deepseek-chat")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "error": f"HTTP {e.code}", "detail": err_body}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return {"ok": False, "error": "unexpected DeepSeek response", "raw": data}
    return {"ok": True, "content": content, "raw": data}


MEMORIES_RE = re.compile(r'\{\s*"memories"\s*:\s*', re.S)


def extract_memories(content: str) -> tuple[str, list[dict[str, Any]]]:
    memories: list[dict[str, Any]] = []
    clean = content
    for m in MEMORIES_RE.finditer(content):
        start = m.start()
        # decode JSON object starting at start
        decoder = json.JSONDecoder()
        try:
            obj, end = decoder.raw_decode(content[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "memories" in obj:
            memories.extend(obj.get("memories") or [])
            chunk = content[start : start + end]
            clean = clean.replace(chunk, "", 1)
    return clean.strip(), memories


def make_handler(life_root: Path | None, static_dir: Path | None) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            pass

        def do_OPTIONS(self) -> None:  # noqa: N802
            _json_response(self, 204, {})

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            qs = urlparse(self.path).query
            params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p) if qs else {}
            if path == "/api/health":
                _json_response(self, 200, {"ok": True, "service": "atlas-chat"})
                return
            if path == "/api/wake":
                _json_response(self, 200, life_mod.wake(life_root))
                return
            if path == "/api/mindmap":
                period = params.get("period") or "day"
                _json_response(self, 200, life_mod.mindmap_graph(life_root, period=period))
                return
            if path == "/api/session-init":
                data = life_mod.load_session_init(life_root)
                _json_response(self, 200, {"ok": True, "init": data})
                return
            if path == "/api/entities":
                _json_response(self, 200, life_mod.entity_list(life_root))
                return
            if path == "/api/entity":
                name = params.get("name") or ""
                _json_response(self, 200, life_mod.entity_detail(life_root, name=name))
                return
            if path == "/api/entity-relations":
                _json_response(self, 200, life_mod.entity_relations(life_root))
                return
            if path == "/api/entity-graph":
                name = params.get("name") or ""
                _json_response(self, 200, life_mod.entity_graph(life_root, name=name))
                return
            if static_dir and static_dir.exists():
                rel = path.lstrip("/") or "index.html"
                candidate = (static_dir / rel).resolve()
                if str(candidate).startswith(str(static_dir.resolve())) and candidate.is_file():
                    data = candidate.read_bytes()
                    ctype = "text/html"
                    if rel.endswith(".js"):
                        ctype = "application/javascript"
                    elif rel.endswith(".css"):
                        ctype = "text/css"
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                # SPA fallback
                index = static_dir / "index.html"
                if index.is_file() and not path.startswith("/api"):
                    data = index.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
            _json_response(self, 404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            body = _read_json(self)
            root = Path(body["life_root"]).expanduser() if body.get("life_root") else life_root
            auto_push = body.get("push", True)

            if path == "/api/pull":
                _json_response(self, 200, life_mod.life_pull(root))
                return
            if path == "/api/sync":
                _json_response(self, 200, life_mod.life_sync(root, message=body.get("message")))
                return
            if path == "/api/remember":
                if body.get("text"):
                    result = life_mod.remember(root, body["text"], push_after=bool(auto_push))
                else:
                    result = life_mod.remember(
                        root,
                        None,
                        type=body.get("type") or "memory",
                        summary=body.get("summary"),
                        why=body.get("why") or "",
                        topics=body.get("topics"),
                        entities=body.get("entities"),
                        room=body.get("room") or "day",
                        period=body.get("period") or "day",
                        when=body.get("when"),
                        push_after=bool(auto_push),
                    )
                _json_response(self, 200 if result.get("ok") else 400, result)
                return
            if path == "/api/chat":
                wake = life_mod.wake(root)
                history = body.get("messages") or []
                model = body.get("model")
                messages = [
                    {
                        "role": "system",
                        "content": SYSTEM_BASE + "\n\n## Wake\n\n" + wake.get("prompt", ""),
                    },
                    *history,
                ]
                ds = deepseek_chat(messages, model=model)
                if not ds.get("ok"):
                    _json_response(self, 502, ds)
                    return
                content, memories = extract_memories(ds["content"])
                saved = []
                for mem in memories:
                    r = life_mod.remember(
                        root,
                        None,
                        type=mem.get("type") or "memory",
                        summary=mem.get("summary"),
                        why=mem.get("why") or "",
                        topics=mem.get("topics"),
                        entities=mem.get("entities"),
                        push_after=False,
                    )
                    saved.append(r)
                git = None
                if auto_push and any(s.get("ok") for s in saved):
                    git = life_mod.life_sync(root, message=None)
                # Soft session init after each turn (resume next load)
                topics_acc: list[str] = []
                for mem in memories:
                    for t in mem.get("topics") or []:
                        if t and t not in topics_acc:
                            topics_acc.append(str(t))
                life_mod.prepare_session_init(
                    root,
                    summary="",
                    topics=topics_acc,
                    last_messages=history[-6:] + [{"role": "assistant", "content": content[:240]}],
                    push_after=False,
                )
                _json_response(
                    self,
                    200,
                    {
                        "ok": True,
                        "reply": content,
                        "memories": memories,
                        "saved": saved,
                        "git": git,
                        "wake_keys": wake.get("keys"),
                    },
                )
                return
            if path == "/api/session-end":
                result = life_mod.prepare_session_init(
                    root,
                    summary=body.get("summary") or "",
                    topics=body.get("topics"),
                    last_messages=body.get("messages"),
                    greeting=body.get("greeting"),
                    push_after=bool(auto_push),
                )
                _json_response(self, 200 if result.get("ok") else 400, result)
                return
            if path == "/api/mindmap":
                _json_response(
                    self,
                    200,
                    life_mod.mindmap_graph(root, period=body.get("period") or "day"),
                )
                return
            _json_response(self, 404, {"ok": False, "error": "not found"})

    return Handler


def serve(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    life_root: Path | None = None,
    static_dir: Path | None = None,
    open_browser: bool = False,
) -> None:
    handler = make_handler(life_root, static_dir)
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}/"
    print(f"atlas life serve {url} root={life_mod.life_root(life_root)}")
    if open_browser:
        import threading
        import webbrowser

        def _open() -> None:
            import time

            time.sleep(0.4)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()
    httpd.serve_forever()
