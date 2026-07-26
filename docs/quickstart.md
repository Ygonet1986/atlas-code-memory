# Quickstart

## Install

```bash
git clone https://github.com/YOUR_USER/atlas-memory.git
cd atlas-memory
pip install -e .

atlas --version
```

## New project

```bash
cd ~/code/my-app
atlas init --global-rule
atlas doctor
atlas import
```

Open the folder in Cursor. Ask: “What does Atlas say we should check before editing?”

## Optional adapters

- Memory: install MemPalace → see `adapters/memory/mempalace.md`
- Graph: install Graphify **or** Mind Map → register scopes in `.cursor/graphify-index.md`

## Daily

```bash
atlas stale
atlas checkpoint .cursor/atlas-import/some.drawer.md
atlas hooks install   # once per repo
atlas metrics
```
