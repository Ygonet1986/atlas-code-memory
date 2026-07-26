# Atlas Memory

[![CI](https://img.shields.io/github/actions/workflow/status/atlas-memory/atlas-memory/ci.yml?label=CI)](https://github.com/atlas-memory/atlas-memory/actions)
[![PyPI](https://img.shields.io/badge/PyPI-atlas--memory-blue)](https://pypi.org/project/atlas-memory/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**The memory router for AI coding agents.**

```text
mempalace-index → MemPalace (optional)
graphify-index  → Graphify or Mind Map (optional, pick one)
project-cache   → real files (always)
```

```bash
pip install -e .          # or: pip install atlas-memory (after PyPI publish)
atlas init --global-rule
atlas doctor
atlas onboard
```

## Commands (0.2)

| Command | Purpose |
|---------|---------|
| `atlas init` | Bootstrap indexes |
| `atlas doctor` | Diagnose setup |
| `atlas route "…"` | JSON recall plan |
| `atlas graph …` | Manage scoped graphs |
| `atlas checkpoint --write/--mine` | Validate + file drawers by room |
| `atlas onboard` | Import + brief + onboard skill |
| `atlas migrate` | Legacy → Atlas |
| `atlas sync export/import` | Team bundles |
| `atlas watch` | Mark graphs stale on change |
| `atlas eval` / `--transcript` | Index + protocol scores |
| `atlas mcp` | MCP stdio server |

Docs: [docs/index.md](docs/index.md)

## MCP (Cursor)

```json
{ "mcpServers": { "atlas-memory": { "command": "atlas-mcp" } } }
```

## License

MIT
