from pathlib import Path

from atlas_memory.commands_cache import (
    build_cache,
    cache_status,
    describe_file,
    parse_cache,
    path_ignored,
)
from atlas_memory.routing import recall_route


def make_project(tmp_path: Path) -> Path:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "project-cache.md").write_text(
        "# Project Source Cache\n\nAtlas layer 5.\n", encoding="utf-8"
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text(
        '"""Handle user login and session refresh."""\n\n\ndef login():\n    pass\n',
        encoding="utf-8",
    )
    (src / "billing.py").write_text("def charge():\n    pass\n\n\nclass Invoice:\n    pass\n", encoding="utf-8")
    (src / "widget.tsx").write_text(
        "/** Renders the settings panel. */\nexport function Panel() {}\n", encoding="utf-8"
    )
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def test_build_indexes_every_source_file(tmp_path: Path):
    project = make_project(tmp_path)
    result = build_cache(project)
    assert result["coverage_pct"] == 100.0
    assert len(result["added"]) == 3

    text = (project / ".cursor" / "project-cache.md").read_text(encoding="utf-8")
    assert "src/auth.py" in text
    assert "src/billing.py" in text
    assert "node_modules" not in text


def test_build_uses_docstrings_and_comments(tmp_path: Path):
    project = make_project(tmp_path)
    assert describe_file(project, "src/auth.py") == "Handle user login and session refresh."
    assert describe_file(project, "src/widget.tsx") == "Renders the settings panel."
    # No docstring: fall back to the top-level symbols.
    assert "Invoice" in describe_file(project, "src/billing.py")


def test_build_preserves_handwritten_entries(tmp_path: Path):
    project = make_project(tmp_path)
    cache = project / ".cursor" / "project-cache.md"
    cache.write_text(
        "# Project Source Cache\n\n"
        "### auth.py\n- **path:** `src/auth.py`\n- **description:** Curated by a human.\n",
        encoding="utf-8",
    )
    build_cache(project)
    text = cache.read_text(encoding="utf-8")
    assert "Curated by a human." in text
    assert "src/billing.py" in text


def test_force_refreshes_and_prune_drops_deleted(tmp_path: Path):
    project = make_project(tmp_path)
    build_cache(project)
    (project / "src" / "billing.py").unlink()

    result = build_cache(project, force=True, prune=True)
    assert "src/billing.py" in result["pruned"]
    text = (project / ".cursor" / "project-cache.md").read_text(encoding="utf-8")
    assert "src/billing.py" not in text
    assert "src/auth.py" in text


def test_dry_run_does_not_write(tmp_path: Path):
    project = make_project(tmp_path)
    before = (project / ".cursor" / "project-cache.md").read_text(encoding="utf-8")
    result = build_cache(project, dry_run=True)
    assert result["added"]
    assert (project / ".cursor" / "project-cache.md").read_text(encoding="utf-8") == before


def test_status_reports_missing_and_stale(tmp_path: Path):
    project = make_project(tmp_path)
    status = cache_status(project)
    assert status["coverage_pct"] == 0.0
    assert "src/auth.py" in status["missing"]

    build_cache(project)
    (project / "src" / "widget.tsx").unlink()
    status = cache_status(project)
    assert status["missing"] == []
    assert status["stale"] == ["src/widget.tsx"]


def test_atlasignore_supports_multi_segment_dirs(tmp_path: Path):
    patterns = ["eval/fixture-monorepo/", "node_modules/", "*.pem"]
    assert path_ignored("eval/fixture-monorepo/src/a.py", patterns)
    assert path_ignored("deep/node_modules/a.py", patterns)
    assert path_ignored("certs/server.pem", patterns)
    assert not path_ignored("eval/cases/bench/a.json", patterns)


def test_parse_cache_roundtrip(tmp_path: Path):
    project = make_project(tmp_path)
    build_cache(project)
    header, entries = parse_cache((project / ".cursor" / "project-cache.md").read_text(encoding="utf-8"))
    assert header.startswith("# Project Source Cache")
    assert {e["path"] for e in entries} == {"src/auth.py", "src/billing.py", "src/widget.tsx"}


def test_built_cache_makes_route_find_the_file(tmp_path: Path):
    project = make_project(tmp_path)
    assert recall_route(project, "where is user login handled")["cache_hits"] == []
    build_cache(project)
    hits = recall_route(project, "where is user login handled")["cache_hits"]
    assert hits and hits[0]["path"] == "src/auth.py"
