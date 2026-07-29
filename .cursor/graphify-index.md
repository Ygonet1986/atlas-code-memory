# Graphify Index

Atlas layer 3. Map of scoped code graphs.
**Not** AI Mind Map. Search this file; never read it end-to-end.
Statuses: `ready` | `missing` | `stale` — use `atlas stale`.

## How to use

1. Find the scope.
2. If `ready` → query that graph.
3. If `stale`/`missing` → update/create, then this index.

## Format

```markdown
### <short-name>
- **scope:** `<relative/path>`
- **graph:** `<path>/graphify-out/`
- **description:** <1–3 sentences>
- **status:** ready | missing | stale
```

## Scopes

<!-- One scope = one graph. Avoid graphifying the root of huge monorepos. -->

### src
- **scope:** `src`
- **graph:** `src/graphify-out/`
- **description:** Atlas Memory Python package (src/atlas_memory)
- **status:** stale


