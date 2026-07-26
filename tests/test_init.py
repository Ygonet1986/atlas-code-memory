from pathlib import Path

from atlas_memory.commands_init import init_project
from atlas_memory.commands_stale import parse_graphify_index


def test_init_creates_indexes(tmp_path: Path):
    actions = init_project(tmp_path)
    assert (tmp_path / ".cursor" / "mempalace-index.md").exists()
    assert (tmp_path / ".cursor" / "graphify-index.md").exists()
    assert (tmp_path / ".cursor" / "project-cache.md").exists()
    assert any("create" in a or "seed" in a for a in actions)
    text = (tmp_path / ".cursor" / "mempalace-index.md").read_text()
    assert "**wing:**" in text


def test_parse_skips_placeholders():
    text = """# Graphify Index

### <nome-curto>
- **escopo:** `<caminho/relativo>`
- **status:** ready

### real
- **escopo:** `src`
- **grafo:** `src/graphify-out/`
- **status:** ready
"""
    entries = parse_graphify_index(text)
    assert len(entries) == 1
    assert entries[0]["name"] == "real"
