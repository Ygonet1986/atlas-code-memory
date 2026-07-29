---
name: atlas
description: >-
  Atlas token GPS: mempalace-index + MemPalace, graphify-index + Graphify|MindMap,
  project-cache. Route before grep to save exploration tokens. Use for recall,
  architecture navigation, file discovery, atlas init, doctor, stale, import,
  checkpoint, bench, daemon, and eval.
---

# Atlas

Mandatory memory stack for AI coding. **One query order.** Goal: **cut exploration tokens**.

## Layers

| # | Layer | Store |
|---|-------|-------|
| 1 | mempalace-index | `.cursor/mempalace-index.md` |
| 2 | MemPalace | optional MemoryBackend |
| 3 | graphify-index | `.cursor/graphify-index.md` |
| 4 | Graphify *or* Mind Map | optional GraphBackend |
| 5 | project-cache | `.cursor/project-cache.md` |

Never read an entire index. Never grep the monorepo before `atlas route` / `atlas_recall_route`. See `reference.md`.

## CLI

```bash
atlas init [--global-rule]
atlas doctor | status | stale | import | migrate | onboard
atlas migrate [--dry-run] [--no-import] [--global-rule] [--hooks]
atlas route "question"
atlas bench [--fixture] [-C project]
atlas daemon | connect --editor cursor
atlas graph add <name> --scope <dir>
atlas graph list|ready|stale
atlas checkpoint [--write] [--mine] file.md
atlas life init|wake|remember|recall|rollup|pull|push|sync|serve
atlas sync export|import
atlas watch [--once]
atlas eval [--transcript]
atlas mcp
atlas hooks install
atlas metrics [--send]
```

Canonical index field labels are English (`path`, `scope`, `graph`, `description`). Older Portuguese labels are still read; `atlas migrate` rewrites them.

## Protocol

- Past work → index → MemPalace (typed drawers).
- Code relations → graphify-index → one graph backend.
- Edits → project-cache partial update; checkpoint after meaningful features.
- Secrets never persisted; validate with `atlas checkpoint`.
- Code beats palace on conflict → `superseded`.
- Personal / any conversation → **life** root (`atlas life wake` / `remember`); Mind Map only; GitHub private sync.
- **Token rule:** open only `cache_hits` from the route; stay within route/wake char budgets.

## MCP / daemon

Prefer `atlas_recall_route` / `atlas_stale` / `atlas_checkpoint` when the Atlas MCP server is configured.
Or HTTP: `atlas daemon` → `GET /api/route?q=...&project=...`.
Life: `atlas_life_wake` / `atlas_life_remember` / `atlas_life_recall` / `atlas_life_rollup`.

## Anti-patterns

Graphify + Mind Map together · mega-root graphs on huge monorepos · inventing memory · checkpoint every keystroke · grep-first on large trees.
