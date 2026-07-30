import json
from pathlib import Path

import pytest

from atlas_memory.commands_connect import SUPPORTED_EDITORS, connect_editor


@pytest.fixture()
def home(tmp_path: Path, monkeypatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake))
    return fake


def test_windsurf_writes_its_own_rule_and_mcp(tmp_path: Path, home: Path):
    proj = tmp_path / "proj"
    proj.mkdir()
    r = connect_editor("windsurf", project=proj, write=True, global_install=True)
    assert r["ok"]

    rule = proj / ".windsurf" / "rules" / "atlas.md"
    assert rule.exists()
    text = rule.read_text(encoding="utf-8")
    assert not text.startswith("---\ndescription:"), "mdc frontmatter is Cursor-only"
    assert "Windsurf" in text

    mcp = json.loads((home / ".codeium" / "windsurf" / "mcp_config.json").read_text(encoding="utf-8"))
    assert mcp["mcpServers"]["atlas-memory"]["command"] == "atlas-mcp"


def test_vscode_uses_servers_key_and_copilot_instructions(tmp_path: Path):
    r = connect_editor("vscode", project=tmp_path, write=True)
    assert r["ok"]
    mcp = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert "servers" in mcp and "mcpServers" not in mcp
    assert mcp["servers"]["atlas-memory"]["type"] == "stdio"
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()


def test_zed_writes_rules_file_and_context_server(tmp_path: Path, home: Path):
    proj = tmp_path / "proj"
    proj.mkdir()
    connect_editor("zed", project=proj, write=True, global_install=True)
    assert (proj / ".rules").exists()
    settings = json.loads((home / ".config" / "zed" / "settings.json").read_text(encoding="utf-8"))
    assert settings["context_servers"]["atlas-memory"]["command"]["path"] == "atlas-mcp"


def test_codex_appends_to_agents_md(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# House rules\n\nBe careful.\n", encoding="utf-8")
    connect_editor("codex", project=tmp_path, write=True)
    text = agents.read_text(encoding="utf-8")
    assert "Be careful." in text
    assert "Atlas Memory" in text


def test_instructions_are_not_appended_twice(tmp_path: Path):
    connect_editor("codex", project=tmp_path, write=True)
    first = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    connect_editor("codex", project=tmp_path, write=True)
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == first


def test_existing_mcp_servers_are_preserved(tmp_path: Path):
    mcp = tmp_path / ".cursor" / "mcp.json"
    mcp.parent.mkdir(parents=True)
    mcp.write_text(json.dumps({"mcpServers": {"other": {"command": "other-mcp"}}}), encoding="utf-8")
    connect_editor("cursor", project=tmp_path, write=True, global_install=False)
    data = json.loads(mcp.read_text(encoding="utf-8"))
    assert "other" in data["mcpServers"]
    assert "atlas-memory" in data["mcpServers"]


def test_unparseable_config_is_not_clobbered(tmp_path: Path):
    mcp = tmp_path / ".vscode" / "mcp.json"
    mcp.parent.mkdir(parents=True)
    mcp.write_text('// jsonc comment\n{ "servers": {} }', encoding="utf-8")
    connect_editor("vscode", project=tmp_path, write=True)
    assert mcp.read_text(encoding="utf-8").startswith("// jsonc comment")
    assert (tmp_path / ".vscode" / "atlas-mcp.snippet.json").exists()


@pytest.mark.parametrize("editor", SUPPORTED_EDITORS)
def test_every_supported_editor_writes_something(editor: str, tmp_path: Path, home: Path):
    proj = tmp_path / editor
    proj.mkdir()
    r = connect_editor(editor, project=proj, write=True)
    assert r["ok"]
    assert r["actions"], f"{editor} produced no actions"
