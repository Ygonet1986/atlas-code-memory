from pathlib import Path

from atlas_memory.commands_cache import cache_status
from atlas_memory.commands_init import init_project
from atlas_memory.routing import recall_route


def make_source_tree(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text('"""Validate JWT tokens."""\n', encoding="utf-8")
    (src / "orders.py").write_text('"""Create customer orders."""\n', encoding="utf-8")
    return tmp_path


def test_init_leaves_the_router_usable(tmp_path: Path):
    project = make_source_tree(tmp_path)
    init_project(project)

    assert cache_status(project)["coverage_pct"] == 100.0
    hits = recall_route(project, "where are jwt tokens validated")["cache_hits"]
    assert hits and hits[0]["path"] == "src/auth.py"


def test_init_reports_how_many_files_it_indexed(tmp_path: Path):
    project = make_source_tree(tmp_path)
    actions = init_project(project)
    assert any("index 2 source files" in a for a in actions)


def test_no_cache_flag_skips_indexing(tmp_path: Path):
    project = make_source_tree(tmp_path)
    init_project(project, build_cache_index=False)
    assert cache_status(project)["coverage_pct"] == 0.0
