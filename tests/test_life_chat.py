from pathlib import Path

from atlas_memory.life import life_init, remember
from atlas_memory.life_chat_server import _query_params, _root_from_query, extract_memories, make_handler


def test_extract_memories_strips_json():
    content = 'Hello.\n\n{"memories":[{"type":"memory","summary":"Likes tea","why":"habit","topics":["food"]}]}\n'
    clean, mems = extract_memories(content)
    assert "Likes tea" not in clean or "memories" not in clean
    assert len(mems) == 1
    assert mems[0]["summary"] == "Likes tea"


def test_extract_memories_none():
    clean, mems = extract_memories("Just chatting.")
    assert clean == "Just chatting."
    assert mems == []


def test_query_life_root_override(tmp_path: Path):
    default = tmp_path / "default-life"
    custom = tmp_path / "custom-life"
    life_init(custom, repo=None, private_check=False, force=True)
    remember(custom, None, summary="Only in custom root", why="test", topics=["custom"])
    params = _query_params(f"/api/wake?life_root={custom.as_posix()}")
    root = _root_from_query(params, default)
    assert root is not None
    assert Path(root).resolve() == custom.resolve()

    Handler = make_handler(default, None)
    # Simulate GET wake with custom root via handler internals
    from atlas_memory import life as life_mod

    w = life_mod.wake(_root_from_query({"life_root": str(custom)}, default))
    assert any("custom root" in (d.get("summary") or "") for d in w["day_drawers"])
    # default root empty
    w0 = life_mod.wake(default)
    assert w0["day_drawers"] == [] or not any(
        "custom root" in (d.get("summary") or "") for d in w0["day_drawers"]
    )
    assert Handler is not None
