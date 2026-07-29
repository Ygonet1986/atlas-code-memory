from atlas_memory.life_chat_server import extract_memories


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
