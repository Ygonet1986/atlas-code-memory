from atlas_memory.commands_graph import add_graph, list_graphs, set_graph_status
from atlas_memory.routing import protocol_score, recall_route


def test_graph_add_list(tmp_path):
    add_graph(tmp_path, "core", "src/core", "core module", "missing")
    entries = list_graphs(tmp_path)
    assert entries[0]["name"] == "core"
    set_graph_status(tmp_path, "core", "ready")
    assert list_graphs(tmp_path)[0]["status"] == "ready"


def test_protocol_score_prefers_atlas_before_grep():
    good = "read mempalace-index then project-cache then edit file"
    bad = "grep -r foo then maybe mempalace-index"
    assert protocol_score(good)["pass"]
    assert protocol_score(bad)["grep_before_atlas"] is True


def test_recall_route(tmp_path):
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mempalace-index.md").write_text(
        "### x\n- **wing:** `demo`\n- **room:** `architecture`\n", encoding="utf-8"
    )
    (tmp_path / ".cursor" / "graphify-index.md").write_text(
        "### core\n- **escopo:** `src`\n- **grafo:** `src/graphify-out/`\n- **status:** ready\n",
        encoding="utf-8",
    )
    (tmp_path / ".cursor" / "project-cache.md").write_text(
        "### main.py\n- **endereço:** `src/main.py`\n- **descrição:** entry\n",
        encoding="utf-8",
    )
    r = recall_route(tmp_path, "architecture of src main")
    assert r["mempalace"]["wing"] == "demo"
    assert r["cache_hits"]
