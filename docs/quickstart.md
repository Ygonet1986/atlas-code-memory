# Quickstart

## Install

```bash
pip install atlas-code-memory

atlas --version
```

Or from source:

```bash
git clone https://github.com/Ygonet1986/atlas-code-memory.git
cd atlas-code-memory
pip install -e .
```

## New project

```bash
cd ~/code/my-app
atlas init --global-rule        # creates the indexes and indexes your source tree
atlas connect --editor cursor   # Atlas = Cursor default where/remember layer
atlas doctor                    # verify
```

Open the folder in Cursor, **reload MCP**, then ask: “What should we check in Atlas before editing?”

## Build the cache

The project-cache is the only mandatory layer: routing can only point at files it
knows about. `atlas init` builds it for you; these commands keep it current. The
description of each file comes from its module docstring, its leading comment or
its exported symbols.

```bash
atlas cache build            # index new files, keep hand-written descriptions
atlas cache build --prune    # also drop entries whose file was deleted
atlas cache build --force    # regenerate every description
atlas cache status           # coverage report + list of un-indexed files
```

Exclude paths with `.atlasignore`. `atlas hooks install` re-runs the build after
every commit, so the cache never drifts from the tree.

## Connect other editors

```bash
atlas connect --editor windsurf   # .windsurf/rules/ + ~/.codeium/windsurf/mcp_config.json
atlas connect --editor vscode     # .vscode/mcp.json + .github/copilot-instructions.md
atlas connect --editor zed        # .rules + context_servers in Zed settings
atlas connect --editor codex      # AGENTS.md
atlas connect --editor generic    # HTTP daemon instructions for anything else
```

Existing configs are merged, never overwritten.

## Token savings check

```bash
atlas bench --fixture   # synthetic monorepo, ~99% savings
atlas bench --real      # this repository, ~78% savings
atlas bench -C .        # your project, with your own cases via --cases
```

The suites include negative cases: questions with no answer in the repo, where the
router is expected to return nothing rather than plausible-looking noise.

## Local daemon (any AI editor)

```bash
atlas daemon
# HTTP: http://127.0.0.1:8765/api/route?q=...&project=...
```

## Personal memory (Life)

```bash
atlas life init
atlas life wake
```

See [life.md](life.md).

## Migrate an existing project

```bash
cd ~/code/legacy-app
atlas migrate
atlas doctor
```

This bootstraps missing indexes, rewrites legacy Portuguese field labels to English, adds an `AGENTS.md` Atlas section when appropriate, seeds README/ADRs into the cache, and writes `.cursor/atlas-migrate-report.md`.

Full details: [migration.md](migration.md).

## Optional adapters

- Memory: install MemPalace → see `adapters/memory/mempalace.md`
- Graph: install Graphify **or** Mind Map → `atlas graph add …`

## Daily

```bash
atlas stale
atlas checkpoint --write some.drawer.md
atlas hooks install   # once per repo
atlas metrics
```
