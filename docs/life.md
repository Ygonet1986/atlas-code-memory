# Atlas Life

Personal conversation memory on a **private** GitHub repo, with temporal drawers and Mind Map scopes.

## Why

Cursor (and the Atlas Chat desktop app) forgets what you said last week. Life mode stores durable facts as typed drawers, organized by **day → week → month → year**, synced via git.

## Setup

```bash
# Create a PRIVATE repo first (gh or GitHub UI)
gh repo create atlas-life --private --clone=false

export ATLAS_LIFE_ROOT="$HOME/atlas-life"
atlas life init --repo YOUR_USER/atlas-life
```

`init` refuses public repos unless you pass `--skip-private-check` (not recommended).

## Protocol

1. `atlas life wake` — today + hot drawers only (no year dump)
2. Answer using real memory; never invent
3. Durable facts → `atlas life remember --text "…" --push`
4. Mind Map for the day scope; mark index ready/stale
5. `atlas life rollup week|month|year` to consolidate

## Drawer types (life)

`memory` · `event` · `person` · `goal` · `preference` · `lesson` · `decision`

Rooms: `day` · `week` · `month` · `year` · `people` · `general`

```text
[type:memory] [status:active]
summary: Prefer dark mode in Atlas Chat
why: eyestrain
branch: -
commit: -
pr: -
files: -
wing: life-2026
room: day
when: 2026-07-29
period: day
topics: preferences, ui
```

## Clients

| Client | Role |
|--------|------|
| Cursor + MCP | `atlas_life_wake` / `remember` / `recall` / `rollup` |
| Atlas Chat desktop | DeepSeek chat; pull on open; auto commit+push |

Never store `DEEPSEEK_API_KEY` in the life repo.

## Git sync

```bash
atlas life pull
atlas life remember --text "…" --push
atlas life sync
```

## See also

- [Atlas Chat desktop](atlas-chat.md)
- [MCP](mcp.md)
- [Security](security.md)
