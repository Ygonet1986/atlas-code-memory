from atlas_memory.commands_checkpoint import file_checkpoint


def test_file_checkpoint_write(tmp_path):
    text = """[type:decision] [status:active]
summary: Prefer SQLite for demo
why: zero ops
branch: main
commit: -
pr: -
files: README.md
room: architecture
"""
    result = file_checkpoint(tmp_path, text, mine=False)
    assert result["ok"] is True
    path = result["path"]
    assert "architecture" in path
    assert (tmp_path / "mempalace.yaml").exists()
