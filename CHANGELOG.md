# Changelog

## 0.3.0 — 2026-07-29

### Added
- **Atlas Life**: temporal conversation memory (`day`/`week`/`month`/`year`) on a private GitHub repo
- CLI: `atlas life init|wake|remember|recall|rollup|pull|push|sync|serve`
- MCP tools: `atlas_life_wake`, `atlas_life_remember`, `atlas_life_recall`, `atlas_life_rollup`
- Drawer types: `memory`, `event`, `person`, `goal` (+ life rooms)
- Atlas Chat desktop (`apps/atlas-chat`): DeepSeek sidecar + Tauri scaffold; auto commit/push
- Docs: `docs/life.md`, `docs/atlas-chat.md`

## 0.2.0 — 2026-07-26

### Added
- MCP server (`atlas mcp` / `atlas-mcp`): recall_route, checkpoint, stale, protocol_score
- `atlas graph add|list|ready|stale`
- `atlas migrate`, `atlas onboard`, `atlas route`, `atlas watch`
- `atlas sync export|import` team bundles
- `atlas checkpoint --write|--mine` with `.cursor/atlas-drawers/<room>/` + `mempalace.yaml`
- Protocol eval via `atlas eval --transcript`
- Opt-in telemetry (`ATLAS_TELEMETRY=1` + `ATLAS_TELEMETRY_URL`)
- Claude Code / Codex `AGENTS.md` snippet
- Examples: python-service, nextjs-app, pnpm-monorepo
- Docs: MCP, team-sync, publishing; GitHub Pages index; publish workflow

## 0.1.0 — 2026-07-26

### Added
- Core protocol, CLI init/status/doctor/stale/import/checkpoint/eval/hooks/metrics
- Templates, schema, secret scanner, adapters, Cursor plugin scaffold
