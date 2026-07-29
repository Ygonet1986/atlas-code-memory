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

| HTTP | Purpose |
|------|---------|
| `GET /api/health` | daemon version |
| `GET /api/route?q=&project=` | recall route (token GPS) |
| `GET /api/bench` | token-proxy bench report |
| `GET /api/wake` | life wake |
| `POST /api/chat` | Atlas Chat sidecar |

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
