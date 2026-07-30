# Atlas MCP

```bash
atlas mcp
# or
atlas-mcp
```

## Local daemon (HTTP + same tools)

```bash
atlas daemon --host 127.0.0.1 --port 8765
atlas connect --editor cursor   # writes .cursor/mcp.json
```

Every request needs the daemon token (printed on startup, also `atlas token`):

```bash
curl -H "Authorization: Bearer $(atlas token)" \
  "http://127.0.0.1:8765/api/route?q=where+is+login&project=$PWD"
```

See [security.md](security.md) for why, and for the origin and Host rules.

| HTTP | Purpose |
|------|---------|
| `GET /api/health` | daemon version |
| `GET /api/route?q=&project=` | recall route (token GPS) |
| `GET /api/bench` | token-proxy bench report |
| `GET /api/cache?project=` | project-cache coverage |
| `POST /api/cache` | build the cache (`prune`, `force`, `dry_run`) |
| `GET /api/wake` | life wake |
| `POST /api/chat` | Atlas Chat sidecar |

## Editors

| Editor | What `atlas connect` writes |
|--------|-----------------------------|
| `cursor` | `.cursor/mcp.json`, `.cursor/rules/atlas.mdc`, skill (project + `~`) |
| `windsurf` | `.windsurf/rules/atlas.md`, `~/.codeium/windsurf/mcp_config.json` |
| `vscode` / `copilot` | `.vscode/mcp.json` (`servers` key), `.github/copilot-instructions.md` |
| `zed` | `.rules`, `context_servers` in `~/.config/zed/settings.json` |
| `claude` / `claude-code` | `.mcp.json`, `CLAUDE.md` |
| `codex` | `AGENTS.md`, `.atlas/codex-config.toml` to paste into `~/.codex/config.toml` |
| `generic` | `.atlas/CONNECT.md` with the HTTP daemon contract |

Existing configs are merged. If a config cannot be parsed (JSON with comments),
Atlas leaves it untouched and writes a `.snippet.json` beside it.

## Cursor `mcp.json` (user or project)

```json
{
  "mcpServers": {
    "atlas-memory": {
      "command": "atlas-mcp"
    }
  }
}
```

Or: `atlas connect --editor cursor`.

## Tools

| Tool | Purpose |
|------|---------|
| `atlas_recall_route` | wing/room + graph + cache hints (open only these files) |
| `atlas_checkpoint` | validate drawer (+ optional write) |
| `atlas_stale` | stale/missing scopes |
| `atlas_cache_status` | project-cache coverage + un-indexed files |
| `atlas_cache_build` | index un-indexed source files into project-cache |
| `atlas_protocol_score` | heuristic transcript score |
| `atlas_life_wake` | life palace hot set for today |
| `atlas_life_remember` | write life drawer (+ optional push) |
| `atlas_life_recall` | temporal recall for life questions |
| `atlas_life_entity_list` | list entities |
| `atlas_life_entity_detail` | drawers for an entity |
| `atlas_life_entity_graph` | entity mind map |
| `atlas_life_entity_relations` | co-occurrence graph |
| `atlas_life_entity_merge` | merge entities |
| `atlas_life_entity_alias` | add alias |
| `atlas_life_rollup` | consolidate day/week/month/year |
