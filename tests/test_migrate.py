from pathlib import Path

from atlas_memory.commands_migrate import migrate_project, normalize_english_labels


def test_migrate_normalizes_portuguese_labels(tmp_path: Path):
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "project-cache.md").write_text(
        "### main.py\n- **endereço:** `src/main.py`\n- **descrição:** entry\n",
        encoding="utf-8",
    )
    (cursor / "graphify-index.md").write_text(
        "### core\n- **escopo:** `src`\n- **grafo:** `src/graphify-out/`\n- **status:** ready\n",
        encoding="utf-8",
    )
    actions = migrate_project(tmp_path, run_import=False, write_report=True)
    cache = (cursor / "project-cache.md").read_text(encoding="utf-8")
    gfi = (cursor / "graphify-index.md").read_text(encoding="utf-8")
    assert "**path:**" in cache
    assert "**description:**" in cache
    assert "**endereço:**" not in cache
    assert "**scope:**" in gfi
    assert "**graph:**" in gfi
    assert "**escopo:**" not in gfi
    assert (cursor / "atlas-migrate-report.md").exists()
    assert any("normalize" in a for a in actions)


def test_migrate_dry_run_does_not_write_labels(tmp_path: Path):
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    original = "### x\n- **endereço:** `a.py`\n- **descrição:** y\n"
    (cursor / "project-cache.md").write_text(original, encoding="utf-8")
    migrate_project(tmp_path, dry_run=True, run_import=False, write_report=False)
    assert (cursor / "project-cache.md").read_text(encoding="utf-8") == original
    assert not (cursor / "atlas-migrate-report.md").exists()


def test_normalize_english_labels_alone(tmp_path: Path):
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mempalace-index.md").write_text(
        "### t\n- **wing:** `w`\n- **descrição:** room\n",
        encoding="utf-8",
    )
    actions = normalize_english_labels(tmp_path)
    text = (cursor / "mempalace-index.md").read_text(encoding="utf-8")
    assert "**description:**" in text
    assert actions


def test_migrate_moves_legacy_rule(tmp_path: Path):
    cursor = tmp_path / ".cursor"
    rules = cursor / "rules"
    rules.mkdir(parents=True)
    legacy = rules / "agent-memory-stack.mdc"
    legacy.write_text("# legacy\n", encoding="utf-8")
    migrate_project(tmp_path, run_import=False, write_report=False)
    assert not legacy.exists()
    assert (rules / "atlas.mdc").exists()
