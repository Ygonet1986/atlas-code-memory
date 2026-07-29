# Project Source Cache

Atlas layer 5. File inventory: name → path → description.
Search this file; never read it end-to-end. Partial updates only after each change.

<!-- atlas import and the agent append entries below -->

### README.md
- **path:** `README.md`
- **description:** Atlas Memory

### readme.md
- **path:** `readme.md`
- **description:** Atlas Memory

### drawer.py
- **path:** `src/atlas_memory/drawer.py`
- **description:** Drawer parse/validate; project + life types/rooms (`memory`/`event`/`person`/`goal`, temporal rooms).

### life.py
- **path:** `src/atlas_memory/life.py`
- **description:** Atlas Life core — init/wake/remember/recall/rollup against ATLAS_LIFE_ROOT.

### life_git.py
- **path:** `src/atlas_memory/life_git.py`
- **description:** Git pull/commit/push + private GitHub check for life palace.

### life_chat_server.py
- **path:** `src/atlas_memory/life_chat_server.py`
- **description:** HTTP sidecar for Atlas Chat (DeepSeek + remember/sync APIs).

### commands_life.py
- **path:** `src/atlas_memory/commands_life.py`
- **description:** CLI `atlas life` subcommands including serve.

### mcp_server.py
- **path:** `src/atlas_memory/mcp_server.py`
- **description:** MCP tools including atlas_life_* for Cursor.

### atlas-chat
- **path:** `apps/atlas-chat`
- **description:** Desktop UI (Vite/React + Tauri scaffold) — Chat + Mind Map tabs, session-end init, DeepSeek sidecar.

### atlas-chat-startup.ps1
- **path:** `scripts/atlas-chat-startup.ps1`
- **description:** Windows Startup script — start life serve (+static UI) and open browser.

### life_autostart.py
- **path:** `src/atlas_memory/life_autostart.py`
- **description:** Install/uninstall Startup shortcut for Atlas Chat.

