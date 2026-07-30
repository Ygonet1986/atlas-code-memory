"""Access control for the local Atlas HTTP daemon.

The daemon reads personal memories, spends API credits and can trigger git
pushes, on a loopback port that every web page in the user's browser can reach.
Binding to 127.0.0.1 is not a boundary: only a shared token and a closed origin
policy keep those pages out.
"""

from __future__ import annotations

import os
import secrets
import stat
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

TOKEN_ENV = "ATLAS_DAEMON_TOKEN"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}

# Browsers may only talk to the daemon from the desktop app's own origin. Every
# other page gets no CORS headers at all, so it cannot read a single response.
DEFAULT_ALLOWED_ORIGINS = (
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
)

# Liveness probes run before a client knows the token, so this one path answers
# without it — and therefore must not disclose paths, versions or memory.
PUBLIC_PATHS = frozenset({"/api/health"})

CORS_HEADERS = "Content-Type, Authorization, X-Atlas-Token"


def token_path() -> Path:
    return Path.home() / ".atlas" / "daemon-token"


def _restrict(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def load_or_create_token() -> str:
    """Return the daemon token, generating and persisting one on first use."""
    env = os.environ.get(TOKEN_ENV, "").strip()
    if env:
        return env
    path = token_path()
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace").strip()
        if existing:
            _restrict(path)
            return existing
    token = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    _restrict(path)
    return token


def reset_token() -> str:
    """Discard the stored token and issue a new one."""
    path = token_path()
    if path.exists():
        path.unlink()
    os.environ.pop(TOKEN_ENV, None)
    return load_or_create_token()


def request_token(handler: BaseHTTPRequestHandler) -> str:
    auth = handler.headers.get("Authorization") or ""
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    header = handler.headers.get("X-Atlas-Token")
    if header:
        return header.strip()
    values = parse_qs(urlparse(handler.path).query).get("token") or []
    return values[0].strip() if values else ""


def host_is_loopback(handler: BaseHTTPRequestHandler) -> bool:
    """Reject DNS-rebinding: the Host header must name the loopback interface."""
    host = (handler.headers.get("Host") or "").strip()
    if not host:
        return False
    if host.startswith("["):
        name = host.partition("]")[0] + "]"
    else:
        name = host.rsplit(":", 1)[0] if ":" in host else host
    return name.lower() in LOOPBACK_HOSTS


def allowed_origin(handler: BaseHTTPRequestHandler, allowlist: tuple[str, ...]) -> str | None:
    origin = (handler.headers.get("Origin") or "").strip()
    return origin if origin and origin in allowlist else None


def token_matches(handler: BaseHTTPRequestHandler, expected: str) -> bool:
    """Whether the caller proved the token, regardless of the path's policy."""
    supplied = request_token(handler)
    return bool(supplied) and secrets.compare_digest(supplied, expected)


def authorize(
    handler: BaseHTTPRequestHandler,
    expected: str,
    *,
    require_token: bool = True,
) -> tuple[int, str]:
    """Return (0, "") when the request may proceed, else (status, reason)."""
    if not host_is_loopback(handler):
        return 403, "daemon accepts loopback Host headers only"
    path = urlparse(handler.path).path
    if not require_token or path in PUBLIC_PATHS:
        return 0, ""
    if not request_token(handler):
        return 401, (
            "missing daemon token — send 'Authorization: Bearer <token>', "
            f"the X-Atlas-Token header, or ?token=; token lives in {token_path()}"
        )
    if not token_matches(handler, expected):
        return 403, "invalid daemon token"
    return 0, ""
