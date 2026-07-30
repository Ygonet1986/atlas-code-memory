# Atlas as Cursor's default memory layer

Atlas is the **general where-to-look / what-to-remember solution for Cursor** when you run connect.

It does not replace the Cursor IDE. It becomes the mandatory orientation + durable memory protocol the agent follows in every chat (`alwaysApply` rule + MCP).

## One command

```bash
pip install -e .   # or: pip install atlas-code-memory
atlas connect --editor cursor
```

This installs:

| Path | Role |
|------|------|
| `~/.cursor/rules/atlas.mdc` | alwaysApply — Walk + Life + anti grep-first |
| `~/.cursor/mcp.json` | `atlas-mcp` stdio server |
| `~/.cursor/skills/atlas/` | skill + reference |
| `./.cursor/...` | project copies of the same |
| `~/.cursor/atlas-DEFAULT.md` | note that Atlas is the default layer |

Then **reload MCP** or restart Cursor.

Project-only (no user home):

```bash
atlas connect --editor cursor --no-global -C .
```

## What the agent must do

1. **Where to look:** `atlas_recall_route` before grepping large trees; open only routed files  
2. **What to remember (project):** checkpoints / drawers + project-cache updates  
3. **What to remember (life):** `atlas_life_wake` / `remember` / `recall` across conversations  

Cursor's built-in Memories stay secondary when Atlas MCP is available.

## Verify

```bash
atlas doctor -C .
atlas route "where is auth?" -C .
atlas bench --fixture
```

See also: [why-atlas.md](why-atlas.md) · [mcp.md](mcp.md) · [revista-atlas.md](revista-atlas.md)
