# Adapters

Atlas Core does not vendor MemPalace or Graphify. It defines slots:

| Slot | Interface (conceptual) | Bundled docs |
|------|------------------------|--------------|
| MemoryBackend | search / add drawer | `adapters/memory/*` |
| GraphBackend | query / path / explain | `adapters/graph/*` |
| FileIndex | name → path → description | built-in `project-cache` |

## Choosing

| Situation | Memory | Graph |
|-----------|--------|-------|
| Solo app, small | none or MemPalace | none |
| Large codebase | MemPalace | Graphify scoped |
| Prefer MCP graph | MemPalace | Mind Map |
| Team patterns | MemPalace + `atlas_shared` | Graphify |

Never enable two graph backends in one project.
