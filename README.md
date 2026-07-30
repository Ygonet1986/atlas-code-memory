# Atlas Memory

[![CI](https://img.shields.io/github/actions/workflow/status/Ygonet1986/atlas-memory/ci.yml?label=CI)](https://github.com/Ygonet1986/atlas-memory/actions)
[![PyPI](https://img.shields.io/badge/PyPI-atlas--memory-blue)](https://pypi.org/project/atlas-memory/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**The token GPS for AI coding — Cursor's where-to-look / what-to-remember layer.**

Stop dumping the monorepo into context. Atlas **understands** the project via indexes, **disambiguates** the right files, **remembers** decisions, and **saves exploration tokens** on the next turn.

```text
mempalace-index  →  MemPalace (optional long-term memory)
graphify-index   →  Graphify or Mind Map (optional; pick one)
project-cache    →  real files (always)
```

Two commands from zero to a working router:

```bash
atlas init                        # creates the indexes and indexes your source tree
atlas connect --editor cursor     # also: windsurf, vscode, zed, codex, claude
# ~/.cursor/rules/atlas.mdc + MCP atlas-mcp — then reload MCP
```

Prove token savings:

```bash
atlas bench --fixture   # synthetic monorepo: 99%
atlas bench --real      # the Atlas repo (needs a source checkout): 78%
```

Both suites include negative cases, where the correct answer is for the router to
stay silent instead of returning plausible-looking noise.

Local daemon (any AI editor):

```bash
atlas daemon          # HTTP on 127.0.0.1:8765
atlas-mcp             # stdio MCP
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

---

## Migration guide

Bring an **existing** project into Atlas Memory without throwing away README, ADRs, or Cursor rules.

### One command

```bash
cd ~/code/legacy-app
atlas migrate -C .
atlas doctor -C .
```

Optional flags:

```bash
atlas migrate --dry-run          # plan only (no writes)
atlas migrate --no-import        # skip README/ADR seeding
atlas migrate --global-rule      # also install ~/.cursor/rules/atlas.mdc
atlas migrate --hooks            # install git post-commit stale hook
```

### What migrate does

1. Renames legacy Cursor memory rules → `.cursor/rules/atlas.mdc`
2. Bootstraps missing indexes / skill / `.atlasignore` (`atlas init`)
3. Rewrites Portuguese field labels to English (`endereço`→`path`, `escopo`→`scope`, …)
4. Ensures an `AGENTS.md` Atlas section when Cursor rules already exist
5. Seeds `project-cache` + drawer stubs from README / `docs/adr` (`atlas import`)
6. Writes `.cursor/atlas-migrate-report.md` with next steps

### After migrate

1. Read `.cursor/atlas-migrate-report.md`
2. Fix anything `atlas doctor` reports
3. Review `.cursor/atlas-import/*.drawer.md` → `atlas checkpoint --write --mine`
4. Register scopes: `atlas graph add app --scope app` (never the monorepo root)
5. Optional adapters: MemPalace and Graphify **or** Mind Map

English is the canonical language for Atlas indexes and CLI. Parsers still accept older Portuguese labels; new writes use English only. CLI aliases: `--escopo` → `--scope`, `--descricao` → `--description`.

Full walkthrough (bare repo, Cursor legacy, MemPalace/Graphify, monorepos, teams, rollback): **[docs/migration.md](docs/migration.md)**.

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

## Commands (0.3)

| Command | Purpose |
|---------|---------|
| `atlas init` | Bootstrap indexes |
| `atlas onboard` | Import README/ADRs + onboarding brief |
| `atlas doctor` | Diagnose setup |
| `atlas migrate` | Migrate existing project → Atlas Memory |
| `atlas route "…"` | JSON recall plan for a question |
| `atlas bench` | A/B token-proxy proof (grep vs route) |
| `atlas daemon` | Local HTTP for any AI editor |
| `atlas connect` | Write MCP/rules for Cursor/Claude/generic |
| `atlas graph …` | Manage scoped graphs (`--scope`) |
| `atlas checkpoint --write/--mine` | Validate + file drawers by room |
| `atlas life …` | Personal memory (wake/remember/sync) + Chat serve |
| `atlas sync export/import` | Team bundles |
| `atlas watch` | Mark graphs stale on change |
| `atlas eval` / `--transcript` | Index + protocol scores |
| `atlas mcp` | MCP stdio server |

Life + desktop: [docs/life.md](docs/life.md) · [docs/atlas-chat.md](docs/atlas-chat.md)

Full docs: [docs/index.md](docs/index.md) · Migration: [docs/migration.md](docs/migration.md)

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
