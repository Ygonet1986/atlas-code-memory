---
name: atlas
description: >-
  Atlas memory router: mempalace-index + MemPalace, graphify-index + Graphify|MindMap,
  project-cache. Use for recall, architecture navigation, file discovery, atlas init,
  doctor, stale, import, checkpoint, and eval.
---

# Atlas

Mandatory memory stack for AI coding. **One query order.**

## Layers

| # | Layer | Store |
|---|-------|-------|
| 1 | mempalace-index | `.cursor/mempalace-index.md` |
| 2 | MemPalace | optional MemoryBackend |
| 3 | graphify-index | `.cursor/graphify-index.md` |
| 4 | Graphify *or* Mind Map | optional GraphBackend |
| 5 | project-cache | `.cursor/project-cache.md` |

Never read an entire index. See `reference.md`.

## CLI

```bash
atlas init [--global-rule]
atlas doctor
atlas status
atlas stale
atlas import
atlas checkpoint file.md
atlas eval
atlas hooks install
atlas metrics
```

## Protocol

- Past work → index → MemPalace (typed drawers).
- Code relations → graphify-index → one graph backend.
- Edits → project-cache partial update; checkpoint after meaningful features.
- Secrets never persisted; validate with `atlas checkpoint`.
- Code beats palace on conflict → `superseded`.

## Anti-patterns

Graphify + Mind Map together · mega-root graphs on huge monorepos · inventing memory · checkpoint every keystroke.
