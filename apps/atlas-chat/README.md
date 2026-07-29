# Atlas Chat

Desktop UI for Atlas Life (DeepSeek + private GitHub memory).

## Quick start

```bash
# terminal 1 — API sidecar (requires DEEPSEEK_API_KEY)
export DEEPSEEK_API_KEY=sk-...
export ATLAS_LIFE_ROOT=$HOME/atlas-life
atlas life serve --port 8765

# terminal 2 — UI
cd apps/atlas-chat
npm install
npm run dev
```

## Native (Tauri)

Requires Rust toolchain. Run `atlas life serve` first, then:

```bash
npm run tauri dev
```

Vite proxies `/api` to `127.0.0.1:8765`.
