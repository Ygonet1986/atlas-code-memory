from pathlib import Path

from atlas_memory.commands_connect import connect_editor
from atlas_memory.daemon import load_config, make_daemon_handler, save_config


def test_connect_cursor_dry_run(tmp_path: Path):
    r = connect_editor("cursor", project=tmp_path, write=False, global_install=False)
    assert r["ok"]
    assert any("mcp.json" in p for p in (r.get("files") or {}))


def test_connect_cursor_write(tmp_path: Path):
    r = connect_editor("cursor", project=tmp_path, write=True, global_install=False)
    assert r["ok"]
    assert (tmp_path / ".cursor" / "mcp.json").exists()
    rule = (tmp_path / ".cursor" / "rules" / "atlas.mdc").read_text(encoding="utf-8")
    assert "where to look" in rule.lower() or "where-to-look" in rule.lower() or "What to remember" in rule


def test_connect_cursor_global(tmp_path: Path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    proj = tmp_path / "proj"
    proj.mkdir()
    r = connect_editor("cursor", project=proj, write=True, global_install=True)
    assert r["ok"]
    assert r["global_install"] is True
    assert (fake_home / ".cursor" / "rules" / "atlas.mdc").exists()
    assert (fake_home / ".cursor" / "mcp.json").exists()
    assert (fake_home / ".cursor" / "atlas-DEFAULT.md").exists()


def test_connect_generic(tmp_path: Path):
    r = connect_editor("generic", project=tmp_path, write=True)
    assert r["ok"]
    assert (tmp_path / ".atlas" / "CONNECT.md").exists()


def test_daemon_config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # On Windows HOME may not redirect Path.home(); patch config_dir via save to tmp
    from atlas_memory import daemon as d

    monkeypatch.setattr(d, "config_dir", lambda: tmp_path / ".atlas")
    path = save_config({"port": 8765, "host": "127.0.0.1"})
    assert path.exists()
    cfg = load_config()
    assert cfg["port"] == 8765
    Handler = make_daemon_handler(life_root=tmp_path, default_project=tmp_path, static_dir=None)
    assert Handler is not None
