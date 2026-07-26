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
```

Open the folder in Cursor. Ask: “What should we check in Atlas before editing?”

## Migrate an existing project

```bash
cd ~/code/legacy-app
atlas migrate
atlas doctor
```

This normalizes indexes, adds an `AGENTS.md` Atlas section when appropriate, and keeps existing cache content.

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
