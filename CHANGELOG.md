# Changelog

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
