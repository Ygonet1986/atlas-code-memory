[type:decision] [status:active]
summary: The local daemon now requires a token, refuses wildcard CORS and rejects non-loopback Host headers; team bundle extraction is sandboxed.
why: Binding to 127.0.0.1 is not a security boundary. The daemon answered any caller with Access-Control-Allow-Origin * and no authentication, so any page open in the user's browser could read every personal memory, write false ones, spend DeepSeek credits and trigger git pushes. The token lives in ~/.atlas/daemon-token with owner-only permissions and is accepted via the Authorization request header, the X-Atlas-Token request header, or a query parameter. /api/health stays public for liveness but no longer discloses version or paths. Separately, sync import called tarfile.extractall with no filter on a peer-supplied tarball; extraction now refuses absolute paths, parent traversal, links and device files, and writes nothing if any member fails.
branch: -
commit: -
pr: -
files: src/atlas_memory/http_auth.py, src/atlas_memory/life_chat_server.py, src/atlas_memory/daemon.py, src/atlas_memory/commands_sync.py, src/atlas_memory/cli.py, docs/security.md, tests/test_daemon_auth.py, tests/test_bundle_extract.py
room: architecture
