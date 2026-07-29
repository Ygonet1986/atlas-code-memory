# Atlas Chat (desktop)

Desktop chat client for **Atlas Life**: DeepSeek LLM + local `atlas life` core + GitHub private sync.

## Location

`apps/atlas-chat/` — Vite + React UI. Local API sidecar: `atlas life serve`.

## Configure

```bash
# never commit this
export DEEPSEEK_API_KEY=sk-...
export ATLAS_LIFE_ROOT=$HOME/atlas-life
export ATLAS_CHAT_MODEL=deepseek-chat   # optional
```

Settings in the UI (stored under OS user config / localStorage only): life root path, model, auto-push toggle.

## Run (dev)

```bash
pip install -e .
atlas life init --life-root "$ATLAS_LIFE_ROOT"   # once
atlas life serve --port 8765
# another terminal:
cd apps/atlas-chat && npm install && npm run dev
```

Open the Vite URL; it proxies `/api` to the sidecar.

## Session init

At end of a conversation (UI **End & init**, or automatically on page close / after chat turns), Atlas writes `.cursor/atlas-session-init.json`. The next `wake` loads that block first so the agent resumes without re-asking settled facts.

```bash
atlas life session-end --summary "…" --topics "a,b" --push
```

## Mind Map tab

UI tab **Mind Map** (or `atlas life mindmap --period day`) builds a node graph from temporal drawers + topics.

## Windows autostart

```bash
atlas life autostart install
# opens http://127.0.0.1:8765/ after boot (serve + built UI in apps/atlas-chat/dist)
atlas life autostart uninstall
```

Build UI once: `cd apps/atlas-chat && npm run build`. Then:

```bash
atlas life serve --with-ui --open
```

## Native shell (optional)

Tauri 2 scaffold lives in `apps/atlas-chat/src-tauri/` for packaging. The Python sidecar remains the source of truth for Atlas + git.

## Security

- Private GitHub repo only
- API key never written to drawers or git
- Checkpoint secret scan before commit
