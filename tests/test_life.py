from __future__ import annotations

from pathlib import Path

from atlas_memory.drawer import parse_drawer_markdown, validate_drawer
from atlas_memory.life import (
    entity_add_alias,
    entity_detail,
    entity_graph,
    entity_list,
    entity_merge,
    entity_relations,
    life_init,
    pin_drawer,
    recall,
    remember,
    rollup,
    unpin_drawer,
    wake,
)


def test_life_drawer_types_ok(tmp_path: Path):
    text = """[type:memory] [status:active]
summary: Likes morning walks
why: energy
branch: -
commit: -
pr: -
files: -
wing: life-2026
room: day
when: 2026-07-29
period: day
topics: health, routine
"""
    d = parse_drawer_markdown(text)
    assert d.type == "memory"
    assert d.topics == ["health", "routine"]
    assert validate_drawer(d, life=True) == []


def test_life_init_wake_remember_rollup(tmp_path: Path):
    root = tmp_path / "atlas-life"
    result = life_init(root, repo=None, private_check=False, force=True)
    assert result["ok"]
    assert (root / ".cursor" / "mempalace-index.md").exists()

    w = wake(root)
    assert w["ok"]
    assert "Hot day drawers" in w["prompt"]

    r = remember(root, None, summary="Started Atlas Life", why="plan", topics=["atlas"])
    assert r["ok"]
    path = Path(r["path"])
    assert path.exists()
    assert "day" in str(path)

    w2 = wake(root)
    assert any("Started Atlas Life" in (d.get("summary") or "") for d in w2["day_drawers"])

    rec = recall(root, "atlas life")
    assert rec["ok"]
    assert rec["hits"]

    ru = rollup(root, "day")
    assert ru["ok"]
    assert ru["count"] >= 1

    from atlas_memory.life import mindmap_graph, prepare_session_init

    si = prepare_session_init(
        root,
        summary="Wrapped up atlas bootstrap",
        topics=["atlas"],
        last_messages=[{"role": "user", "content": "done for today"}],
    )
    assert si["ok"]
    w3 = wake(root)
    assert w3.get("session_init")
    assert "Session init" in w3["prompt"]

    mm = mindmap_graph(root, period="day")
    assert mm["ok"]
    assert any(n["kind"] == "period" for n in mm["nodes"])


def test_remember_with_entities(tmp_path: Path):
    root = tmp_path / "atlas-life"
    life_init(root, repo=None, private_check=False, force=True)
    r = remember(
        root, None,
        summary="Had coffee with Alice",
        why="social",
        topics=["coffee"],
        entities=["Alice", "Café Central"],
    )
    assert r["ok"]
    assert "alice" in r["entities_linked"]
    assert "caf-central" in r["entities_linked"]

    el = entity_list(root)
    assert el["ok"]
    assert el["count"] == 2
    slugs = [e["slug"] for e in el["entities"]]
    assert "alice" in slugs

    ed = entity_detail(root, "Alice")
    assert ed["ok"]
    assert ed["slug"] == "alice"
    assert len(ed["drawers"]) == 1
    assert "coffee" in (ed["drawers"][0].get("topics") or [])

    eg = entity_graph(root, "Alice")
    assert eg["ok"]
    kinds = {n["kind"] for n in eg["nodes"]}
    assert "entity" in kinds


def test_hot_drawers_pinned(tmp_path: Path):
    root = tmp_path / "atlas-life"
    life_init(root, repo=None, private_check=False, force=True)
    r1 = remember(root, None, summary="Normal drawer", why="test", topics=["a"])
    assert r1["ok"]
    r2 = remember(root, None, summary="Pinned drawer", why="test", topics=["b"])
    assert r2["ok"]
    pin_result = pin_drawer(r2["path"])
    assert pin_result["ok"]
    w = wake(root)
    assert w["ok"]
    summaries = [d.get("summary") for d in w["day_drawers"]]
    assert "Pinned drawer" in summaries
    assert summaries.index("Pinned drawer") < summaries.index("Normal drawer")
    unpin_result = unpin_drawer(r2["path"])
    assert unpin_result["ok"]


def test_entity_alias_and_merge(tmp_path: Path):
    root = tmp_path / "atlas-life"
    life_init(root, repo=None, private_check=False, force=True)
    remember(root, None, summary="Met Alice", why="social", entities=["Alice"])
    remember(root, None, summary="Met Ali", why="social", entities=["Ali"])
    # Add alias so Ali resolves to Alice
    alias_r = entity_add_alias(root, "Alice", "Ali")
    assert alias_r["ok"]
    assert "Ali" in alias_r["aliases"]
    # Now remember with alias — should link to alice slug
    r3 = remember(root, None, summary="Ali likes tea", why="pref", entities=["Ali"])
    assert "alice" in r3["entities_linked"]
    detail = entity_detail(root, "Alice")
    assert detail["ok"]
    assert len(detail["drawers"]) >= 2
    # Merge ali into alice
    el = entity_list(root)
    slugs = [e["slug"] for e in el["entities"]]
    if "ali" in slugs:
        merge_r = entity_merge(root, "Ali", "Alice")
        assert merge_r["ok"]
        el2 = entity_list(root)
        slugs2 = [e["slug"] for e in el2["entities"]]
        assert "ali" not in slugs2


def test_entity_relations(tmp_path: Path):
    root = tmp_path / "atlas-life"
    life_init(root, repo=None, private_check=False, force=True)
    remember(root, None, summary="Alice and Bob met", why="event", entities=["Alice", "Bob"])
    remember(root, None, summary="Alice and Carol met", why="event", entities=["Alice", "Carol"])
    rels = entity_relations(root)
    assert rels["ok"]
    assert rels["count"] >= 1
    pairs = [(r["source"], r["target"]) for r in rels["relations"]]
    assert ("alice", "bob") in pairs


def test_project_type_still_valid():
    text = """[type:decision] [status:active]
summary: Use Postgres
why: team knows it
branch: main
commit: abc
pr: -
files: src/db.py
"""
    d = parse_drawer_markdown(text)
    assert validate_drawer(d, life=False) == []
