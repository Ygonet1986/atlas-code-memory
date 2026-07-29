# Quickstart

## Install

```bash
git clone https://github.com/Ygonet1986/atlas-memory.git
cd atlas-memory
pip install -e .

atlas --version
```

## New project

```bash
cd ~/code/my-app
atlas init --global-rule
atlas onboard
atlas doctor
atlas connect --editor cursor   # Atlas = Cursor default where/remember layer
```

Open the folder in Cursor, **reload MCP**, then ask: “What should we check in Atlas before editing?”

## Token savings check

```bash
atlas bench --fixture
# or against this repo after indexes exist:
atlas bench -C .
```

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
