# Atlas Memory

[![CI](https://img.shields.io/github/actions/workflow/status/Ygonet1986/atlas-memory/ci.yml?label=CI)](https://github.com/Ygonet1986/atlas-memory/actions)
[![PyPI](https://img.shields.io/badge/PyPI-atlas--memory-blue)](https://pypi.org/project/atlas-memory/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**The memory router for AI coding agents.**

Stop re-teaching your agent the same repo every chat. Atlas gives every AI coding session a **fixed path**: decisions → code map → the right file — without dumping your entire codebase into context.

```text
mempalace-index  →  MemPalace (optional long-term memory)
graphify-index   →  Graphify or Mind Map (optional; pick one)
project-cache    →  real files (always)
```

---

## Why use Atlas (or migrate to it)

### The problem with “just chat with the repo”

| What happens today | Cost |
|--------------------|------|
| Agent greps the whole tree every session | Tokens, time, noise |
| Last week’s architecture decision lives in an old thread | Rework and contradictory advice |
| Huge monorepos (or multi-engine trees) overwhelm context | Wrong files, hallucinated paths |
| “Memory” tools fight each other (two graphs, three “search me first” rules) | Unpredictable agents |
| Secrets accidentally pasted into notes | Security risk |

**Your model is not the bottleneck. Orientation is.**

### Why Atlas

1. **One protocol, every project** — The agent always asks the same five questions in the same order. No improvisation.
2. **Router, not another brain** — Atlas doesn’t replace Cursor, Claude, or MemPalace. It tells them *where to look*.
3. **Works at day one, scales later** — `project-cache` alone is useful. Add MemPalace and Graphify when you need them.
4. **Safe by default** — Typed checkpoints, secret scanning, code-wins-over-stale-memory.
5. **Built for real repos** — Scoped graphs instead of one mega-index of 30k files.
6. **Migratable** — `atlas migrate` / `atlas onboard` turn README/ADRs and loose Cursor rules into Atlas layout.

### Who should migrate

- You already use Cursor (or Claude Code / Codex) on more than one project  
- You’ve repeated “we decided X last month” more than twice  
- Grep-first workflows feel slow or wrong on a large codebase  
- You tried MemPalace / Graphify / Mind Map and want **one hierarchy**, not three competing rules  

### Who can wait

- Greenfield toy apps with a handful of files and no lasting decisions — start with `atlas init` when the project grows.

---

## 60-second install

```bash
git clone https://github.com/Ygonet1986/atlas-memory.git
cd atlas-memory
pip install -e .

cd ~/code/your-app
atlas init --global-rule
atlas onboard
atlas doctor
```

Open the project in Cursor. The Atlas rule steers the agent automatically.

Migrate an existing setup:

```bash
atlas migrate -C .
atlas doctor -C .
```

---

## How it works

```text
1. mempalace-index   → which memory wing/room?
2. MemPalace         → what did we decide / learn?
3. graphify-index    → which code graph?
4. Graphify|MindMap  → how do symbols connect?
5. project-cache     → which file to open?
```

Missing layer → skip. Never invent memory hits.

---

## Commands (0.2)

| Command | Purpose |
|---------|---------|
| `atlas init` | Bootstrap indexes |
| `atlas onboard` | Import README/ADRs + onboarding brief |
| `atlas doctor` | Diagnose setup |
| `atlas migrate` | Legacy Cursor memory → Atlas |
| `atlas route "…"` | JSON recall plan for a question |
| `atlas graph …` | Manage scoped graphs |
| `atlas checkpoint --write/--mine` | Validate + file drawers by room |
| `atlas sync export/import` | Team bundles |
| `atlas watch` | Mark graphs stale on change |
| `atlas eval` / `--transcript` | Index + protocol scores |
| `atlas mcp` | MCP stdio server |

Full docs: [docs/index.md](docs/index.md)

---

## MCP (Cursor)

```json
{
  "mcpServers": {
    "atlas-memory": {
      "command": "atlas-mcp"
    }
  }
}
```

---

## Optional adapters

| Slot | Options |
|------|---------|
| Memory | [MemPalace](adapters/memory/mempalace.md) or none |
| Code graph | [Graphify](adapters/graph/graphify.md) **or** [Mind Map](adapters/graph/mindmap.md) — never both |
| File index | Built-in `project-cache` (required) |

---

## License

MIT — see [LICENSE](LICENSE).
