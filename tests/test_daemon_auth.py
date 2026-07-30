import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from atlas_memory.daemon import make_daemon_handler
from atlas_memory.http_auth import load_or_create_token, reset_token, token_path

TOKEN = "test-token-abc123"


@pytest.fixture()
def server(tmp_path: Path):
    handler = make_daemon_handler(
        life_root=tmp_path,
        default_project=tmp_path,
        static_dir=None,
        auth_token=TOKEN,
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def get(url: str, *, headers: dict[str, str] | None = None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8")), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8")), dict(e.headers)


def test_request_without_token_is_rejected(server: str):
    status, body, _ = get(f"{server}/api/route?q=login")
    assert status == 401
    assert "token" in body["error"].lower()


def test_wrong_token_is_rejected(server: str):
    status, body, _ = get(
        f"{server}/api/route?q=login", headers={"Authorization": "Bearer wrong"}
    )
    assert status == 403
    assert body["ok"] is False


def test_bearer_header_is_accepted(server: str):
    status, body, _ = get(
        f"{server}/api/route?q=login", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert status == 200
    assert "cache_hits" in body


def test_custom_header_and_query_param_are_accepted(server: str):
    status, _, _ = get(f"{server}/api/route?q=login", headers={"X-Atlas-Token": TOKEN})
    assert status == 200
    status, _, _ = get(f"{server}/api/route?q=login&token={TOKEN}")
    assert status == 200


def test_health_is_public_but_leaks_nothing(server: str):
    status, body, _ = get(f"{server}/api/health")
    assert status == 200
    assert body["auth"] == "required"
    assert "life_root" not in body and "version" not in body

    status, body, _ = get(f"{server}/api/health", headers={"X-Atlas-Token": TOKEN})
    assert status == 200
    assert "life_root" in body and "version" in body


def test_no_cors_headers_for_a_random_website(server: str):
    _, _, headers = get(
        f"{server}/api/health", headers={"Origin": "https://evil.example.com"}
    )
    assert "Access-Control-Allow-Origin" not in headers


def test_cors_echoed_only_for_the_desktop_app_origin(server: str):
    _, _, headers = get(
        f"{server}/api/health",
        headers={"Origin": "tauri://localhost", "X-Atlas-Token": TOKEN},
    )
    assert headers.get("Access-Control-Allow-Origin") == "tauri://localhost"
    assert headers.get("Vary") == "Origin"


def test_non_loopback_host_header_is_refused(server: str):
    # Simulates DNS rebinding: the request lands on 127.0.0.1 but claims another name.
    status, body, _ = get(
        f"{server}/api/health",
        headers={"Host": "attacker.example.com", "X-Atlas-Token": TOKEN},
    )
    assert status == 403
    assert "loopback" in body["error"].lower()


def test_auth_can_be_disabled_explicitly(tmp_path: Path):
    handler = make_daemon_handler(
        life_root=tmp_path, default_project=tmp_path, static_dir=None, auth_token=""
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        status, _, _ = get(f"http://127.0.0.1:{httpd.server_address[1]}/api/route?q=login")
        assert status == 200
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_token_is_persisted_and_rotatable(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.delenv("ATLAS_DAEMON_TOKEN", raising=False)

    first = load_or_create_token()
    assert first and load_or_create_token() == first
    assert token_path().read_text(encoding="utf-8").strip() == first

    rotated = reset_token()
    assert rotated != first


def test_env_var_overrides_the_stored_token(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setenv("ATLAS_DAEMON_TOKEN", "from-env")
    assert load_or_create_token() == "from-env"
