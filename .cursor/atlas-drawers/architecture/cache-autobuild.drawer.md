[type:decision] [status:active]
summary: project-cache is now generated from the source tree (atlas cache build) instead of being appended by hand.
why: The cache is the only mandatory routing layer, but it was 28% complete and depended on an agent remembering to append entries; no new user would ever curate it. Descriptions come from module docstrings, leading comments or exported symbols; hand-written entries are preserved unless --force. Coverage is enforced by atlas doctor and refreshed by the post-commit hook.
branch: -
commit: -
pr: -
files: src/atlas_memory/commands_cache.py, src/atlas_memory/commands_doctor.py, src/atlas_memory/cli.py, src/atlas_memory/mcp_server.py, src/atlas_memory/daemon.py, hooks/git/post-commit
room: architecture
