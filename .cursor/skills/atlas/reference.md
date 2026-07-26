# Atlas reference

## Drawer taxonomy

| Type | Use |
|------|-----|
| `decision` | Chose A over B |
| `lesson` | What works / failed |
| `preference` | User or project preference |
| `bugfix` | Root cause + fix |
| `build` | Toolchain/CI (no secrets) |

```text
[type:decision] [status:active]
summary: <one sentence>
why: <short>
branch: <or ->
commit: <or ->
pr: <or ->
files: <paths>
supersedes: <optional>
```

Statuses: `active` | `superseded` | `archived`

Validate: `atlas checkpoint drawer.md`

## Rooms

`architecture` · `debugging` · `conventions` · `build` · `general`

## Conflict

Trust the repository. Mark obsolete drawers `superseded` and file a new `active` drawer.

## Secrets deny list

Do not store: `.env*`, API keys, tokens, private keys, credential JSON, DB URLs with passwords.
`atlas checkpoint` rejects common patterns.

## Stale

Sources newer than `graph.json`, missing graph, or explicit `stale` → update graph → `ready`.
`atlas hooks install` wires post-commit marking.

## Hallways

Cross-project patterns → wing `atlas_shared`. Do not mix product drawers into shared wing.

## Wake (L0)

Wing + few hot drawers only. No full palace dump.

## Metrics

Local opt-in counters in `.cursor/atlas-metrics.json` via CLI events. No network.
