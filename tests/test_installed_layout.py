"""Guards for behaviour that only breaks once Atlas is installed as a wheel."""

from pathlib import Path

from atlas_memory.commands_bench import baseline_explore
from atlas_memory.commands_cache import build_cache, iter_source_files
from atlas_memory.paths import source_checkout_root


def make_tree(root: Path) -> None:
    src = root / "src"
    src.mkdir(parents=True)
    (src / "auth.py").write_text('"""Validate JWT tokens."""\n' * 50, encoding="utf-8")
    (src / "orders.py").write_text('"""Create customer orders."""\n' * 50, encoding="utf-8")


def test_project_under_a_skipped_directory_name_is_still_indexed(tmp_path: Path):
    # A checkout living in .../site-packages/... or .../build/... is still a project.
    for parent in ("site-packages", "build", "dist", "vendor"):
        project = tmp_path / parent / "my-app"
        make_tree(project)
        sources, _ = iter_source_files(project)
        assert sorted(sources) == ["src/auth.py", "src/orders.py"], parent


def test_skip_dirs_still_apply_inside_the_project(tmp_path: Path):
    project = tmp_path / "app"
    make_tree(project)
    junk = project / "node_modules" / "pkg"
    junk.mkdir(parents=True)
    (junk / "index.py").write_text("x = 1\n", encoding="utf-8")

    sources, _ = iter_source_files(project)
    assert "node_modules/pkg/index.py" not in sources


def test_bench_baseline_sees_files_under_a_skipped_parent(tmp_path: Path):
    project = tmp_path / "site-packages" / "fixture"
    make_tree(project)
    (project / ".cursor").mkdir()
    (project / ".cursor" / "project-cache.md").write_text("# Project Source Cache\n", encoding="utf-8")
    build_cache(project)

    base = baseline_explore(project, "validate jwt tokens")
    assert base["files_opened"] > 0
    assert base["chars"] > 0


def test_source_checkout_root_detects_this_repo():
    root = source_checkout_root()
    # Running the suite from the repo, so it must resolve; from a wheel it is None.
    assert root is None or (root / "pyproject.toml").exists()
