# Atlas Chat (desktop)

Desktop shell for **Atlas**: local daemon (token GPS + Life) + DeepSeek chat + GitHub private sync.

## Location

`apps/atlas-chat/` — Vite + React UI. Sidecar: `atlas daemon` (or `atlas life serve`).

## Configure

```bash
# never commit this
export DEEPSEEK_API_KEY=sk-...
export ATLAS_LIFE_ROOT=$HOME/atlas-life
export ATLAS_CHAT_MODEL=deepseek-chat   # optional
```

Settings in the UI (localStorage only): life root path, model, auto-push toggle.

## Run (dev)

```bash
pip install -e .
atlas life init --life-root "$ATLAS_LIFE_ROOT"   # once
atlas daemon --port 8765 --with-ui   # preferred
# or: atlas life serve --port 8765
cd apps/atlas-chat && npm install && npm run dev
```

Open the Vite URL; it proxies `/api` to the daemon.

## Native shell (Tauri)

```bash
cd apps/atlas-chat
npm run tauri dev
```

On launch, the Tauri shell tries to spawn `atlas daemon` on `127.0.0.1:8765` if nothing is listening. Commands: `daemon_status`, `ensure_daemon`.

UI tabs: Chat · Mind Map · Entities · **Savings** (`GET /api/bench`).

## Session init

**End & init** (or pagehide beacon) writes `.cursor/atlas-session-init.json`. Chat turns only refresh session-init when durable memories were saved.

```bash
atlas life session-end --summary "…" --topics "a,b" --push
```

## Windows autostart

```bash
atlas life autostart install
atlas life autostart uninstall
```

Installs Startup shortcuts for Chat UI and `AtlasDaemon.cmd`.

## Any AI editor

```bash
atlas connect --editor cursor   # or claude | generic
atlas-mcp                       # stdio MCP
```

## Security

- Private GitHub repo only
- API key never written to drawers or git
- Checkpoint secret scan before commit
