# GraphBackend: Graphify

Optional scoped code knowledge graphs.

## Install

```bash
uv tool install graphifyy   # package name has two y's
graphify --version
```

## Atlas wiring

1. Never `graphify .` on huge multi-engine monorepos — pick a subdirectory.
2. Register in `.cursor/graphify-index.md` with `status: ready|missing|stale`.
3. Agent: search index → `graphify query|path|explain` in that scope.
4. `atlas stale` / git hooks keep status honest.

## Conflict

Do **not** enable AI Mind Map in the same project.
