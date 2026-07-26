from atlas_memory.drawer import parse_drawer_markdown, validate_drawer
from atlas_memory.secrets import scan_text


def test_parse_drawer_ok():
    text = """[type:decision] [status:active]
summary: Use Postgres
why: team knows it
branch: main
commit: abc
pr: -
files: src/db.py
"""
    d = parse_drawer_markdown(text)
    assert d.type == "decision"
    assert validate_drawer(d) == []


def test_secret_rejected():
    text = """[type:build] [status:active]
summary: keys
why: bad
branch: -
commit: -
pr: -
files: -
api_key: sk-abcdefghijklmnopqrstuvwxyz123456
"""
    d = parse_drawer_markdown(text)
    errs = validate_drawer(d)
    assert any("secret" in e or "openai" in e or "api" in e for e in errs)


def test_scan_github_pat():
    hits = scan_text("token ghp_" + ("a" * 36))
    assert hits
