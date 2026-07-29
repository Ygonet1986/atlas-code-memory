# Project Source Cache

Atlas layer 5. File inventory: name → path → description.
Search this file; never read it end-to-end. Partial updates only after each change.

<!-- atlas import and the agent append entries below -->

### revista-atlas.md
- **path:** `docs/revista-atlas.md`
- **description:** Artigo em português tom revista de informática — o que Atlas é, Walk, tokens, Life, daemon.

### article.md
- **path:** `docs/article.md`
- **description:** Whitepaper técnico ARP (retrieval protocol).

### readme.md
- **path:** `readme.md`
- **description:** Atlas Memory

### drawer.py
- **path:** `src/atlas_memory/drawer.py`
- **description:** Drawer parse/validate; project + life types/rooms (`memory`/`event`/`person`/`goal`, temporal rooms).

### life.py
- **path:** `src/atlas_memory/life.py`
- **description:** Atlas Life core — init/wake/remember/recall/rollup; wake prompt respects char_budget for token economy.

### life_git.py
- **path:** `src/atlas_memory/life_git.py`
- **description:** Git pull/commit/push + private GitHub check for life palace.

### life_chat_server.py
- **path:** `src/atlas_memory/life_chat_server.py`
- **description:** HTTP sidecar for Atlas Chat (DeepSeek + remember/sync APIs); honors life_root on GET.

### commands_life.py
- **path:** `src/atlas_memory/commands_life.py`
- **description:** CLI `atlas life` subcommands including serve and --entities on remember.

### commands_bench.py
- **path:** `src/atlas_memory/commands_bench.py`
- **description:** A/B token-proxy bench — blind grep vs recall_route; savings_pct report.

### daemon.py
- **path:** `src/atlas_memory/daemon.py`
- **description:** Local HTTP daemon (route/wake/bench/life) for any AI editor; ~/.atlas/config.json.

### commands_connect.py
- **path:** `src/atlas_memory/commands_connect.py`
- **description:** atlas connect — Cursor global rule+MCP+skill as default where/remember layer.

### cursor-default.md
- **path:** `docs/cursor-default.md`
- **description:** How Atlas becomes Cursor's default orientation + memory layer.

### atlas.mdc (rule)
- **path:** `cursor/rules/atlas.mdc`
- **description:** alwaysApply rule — Atlas Walk, Life, anti grep-first; Cursor authority table.

### routing.py
- **path:** `src/atlas_memory/routing.py`
- **description:** recall_route with wing match, stale weighting, char_budget; protocol_score.

### cli.py
- **path:** `src/atlas_memory/cli.py`
- **description:** Atlas CLI — bench, daemon, connect, life, eval, mcp, graph, etc.

### mcp_server.py
- **path:** `src/atlas_memory/mcp_server.py`
- **description:** MCP tools including atlas_life_* for Cursor.

### atlas-chat
- **path:** `apps/atlas-chat`
- **description:** Desktop UI — Chat, Mind Map, Entities, Savings tabs; Tauri spawns atlas daemon.

### atlas-chat-startup.ps1
- **path:** `scripts/atlas-chat-startup.ps1`
- **description:** Windows Startup script — start life serve (+static UI) and open browser.

### life_autostart.py
- **path:** `src/atlas_memory/life_autostart.py`
- **description:** Install/uninstall Startup shortcuts for Atlas Chat and AtlasDaemon.

### generate_bench_fixture.py
- **path:** `scripts/generate_bench_fixture.py`
- **description:** Builds eval/fixture-monorepo with decoys for token bench.

