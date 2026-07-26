# Atlas for Claude Code / Codex

Add to your project `CLAUDE.md` or `AGENTS.md`:

```markdown
## Atlas

Before searching the repo, follow Atlas order:
1. `.cursor/mempalace-index.md` → wing/room
2. MemPalace (if available)
3. `.cursor/graphify-index.md` → scoped graph
4. Graphify **or** Mind Map (not both)
5. `.cursor/project-cache.md` → file path

Bootstrap: `atlas init && atlas doctor`
MCP (optional): `atlas mcp` / `atlas-mcp`
```

Copy this file's snippet with:

```bash
atlas migrate -C .
# or manually append integrations/agents/AGENTS.snippet.md
```
