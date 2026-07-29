# Atlas reference

## Drawer taxonomy

| Type | Use |
|------|-----|
| `decision` | Chose A over B |
| `lesson` | What works / failed |
| `preference` | User or project preference |
| `bugfix` | Root cause + fix |
| `build` | Toolchain/CI (no secrets) |
| `memory` | Life fact from conversation |
| `event` | Something that happened |
| `person` | People notes |
| `goal` | Intent / goal |

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

Life drawers may also include `when:`, `period:`, `topics:`, `wing:`, `room:`.

Statuses: `active` | `superseded` | `archived`

Validate: `atlas checkpoint drawer.md` · life: `atlas life remember`

## Rooms

Project: `architecture` · `debugging` · `conventions` · `build` · `general`

Life: `day` · `week` · `month` · `year` · `people` · `general`

## Conflict

Trust the repository. Mark obsolete drawers `superseded` and file a new `active` drawer.

## Secrets deny list

Do not store: `.env*`, API keys, tokens, private keys, credential JSON, DB URLs with passwords.
`atlas checkpoint` rejects common patterns. Never put `DEEPSEEK_API_KEY` in life drawers or git.

## Stale

Sources newer than `graph.json`, missing graph, or explicit `stale` → update graph → `ready`.
`atlas hooks install` wires post-commit marking.

## Hallways

Cross-project patterns → wing `atlas_shared`. Do not mix product drawers into shared wing.

## Wake (L0)

Wing + few hot drawers only. No full palace dump.
Life: `atlas life wake` (today + week summary + people).

## Life + GitHub

`$ATLAS_LIFE_ROOT` or `~/atlas-life`. Private repo. `atlas life sync` / remember `--push`.

## Metrics

Local opt-in counters in `.cursor/atlas-metrics.json` via CLI events. No network.
