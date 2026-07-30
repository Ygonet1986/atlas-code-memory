# Migration guide

Migrate any existing codebase into **Atlas Memory** so agents follow one orientation protocol instead of re-grepping and re-learning the repo every chat.

## Who should migrate

- You already use Cursor, Claude Code, or Codex on more than one project
- Architecture decisions keep getting rediscovered across threads
- You installed MemPalace / Graphify / Mind Map and need **one order**, not three competing rules
- Grep-first exploration is expensive on a large tree

Skip migration for disposable toys that fit in one context window — start with `atlas init` when the project grows.

## What `atlas migrate` does

| Step | Effect |
|------|--------|
| Legacy rule rename | `agent-memory-stack.mdc` / similar → `.cursor/rules/atlas.mdc` |
| Bootstrap | Creates missing indexes, rule, skill, `.atlasignore` (`atlas init`) |
| English labels | Rewrites Portuguese field labels (`endereço`→`path`, `escopo`→`scope`, …) |
| `AGENTS.md` | Appends an Atlas section when Cursor rules already exist |
| Cache header | Ensures `project-cache.md` has an English Atlas header |
| Import | Seeds `project-cache` + `.cursor/atlas-import/*.drawer.md` from README/ADRs |
| Report | Writes `.cursor/atlas-migrate-report.md` with next steps |

Optional flags:

```bash
atlas migrate --dry-run          # plan only
atlas migrate --no-import        # skip README/ADR seeding
atlas migrate --global-rule      # also install ~/.cursor/rules/atlas.mdc
atlas migrate --hooks            # install git post-commit stale hook
```

## Quick path (recommended)

```bash
# Install Atlas once
pip install -e /path/to/atlas-code-memory   # or: pip install atlas-code-memory

cd ~/code/your-existing-app
atlas migrate -C .
atlas doctor -C .
```

Then open the project in Cursor and ask the agent to follow Atlas before editing.

## From common starting points

### A) Bare git repo (no AI memory yet)

```bash
atlas init --global-rule
atlas onboard
atlas doctor
```

`onboard` = init + import + onboard skill + brief. Prefer this for greenfield.

### B) Cursor project with loose rules / old memory stack

```bash
atlas migrate
atlas doctor
```

Migrates legacy rule names, normalizes indexes, and imports docs.

### C) Already using MemPalace and/or Graphify

```bash
atlas migrate --no-import   # if cache is already curated
atlas graph add app --scope app   # register each graph scope
atlas graph ready app             # after graphify update
atlas doctor
```

Keep **one** graph backend: Graphify **or** Mind Map — never both.

### D) Portuguese Atlas indexes (older local copies)

Early Atlas drafts used Portuguese field labels (`endereço`, `escopo`, `grafo`, `descrição`). Migrate rewrites them to English:

| Old (PT) | Canonical (EN) |
|----------|----------------|
| `endereço` | `path` |
| `descrição` | `description` |
| `escopo` | `scope` |
| `grafo` | `graph` |

Parsers still **read** the old labels; new writes use English only. CLI keeps `--escopo` / `--descricao` as aliases of `--scope` / `--description`.

### E) Monorepo

```bash
atlas migrate
atlas graph add web --scope packages/web
atlas graph add api --scope packages/api
# Do not graphify the monorepo root
```

## After migrate checklist

1. Read `.cursor/atlas-migrate-report.md`
2. `atlas doctor` — fix FAIL/WARN lines
3. Review `.cursor/atlas-import/*.drawer.md` → `atlas checkpoint --write --mine`
4. Register first graph scope(s) if the tree is large
5. Optional: MemPalace (`adapters/memory/mempalace.md`) and Graphify (`adapters/graph/graphify.md`)

## Protocol reminder

```text
1. mempalace-index   → wing/room
2. MemPalace         → decisions / lessons (optional)
3. graphify-index    → which scoped graph
4. Graphify|MindMap  → symbol relations (optional, exclusive)
5. project-cache     → which file to open
```

Missing layer → skip. Never invent memory hits. **Code wins** over stale palace drawers.

## Team rollout

```bash
# One engineer migrates and exports a bundle
atlas sync export -o atlas-bundle.zip

# Others import
atlas sync import atlas-bundle.zip
atlas doctor
```

See [team-sync.md](team-sync.md).

## Rollback

Atlas is file-based. To undo a migration:

- Delete or revert `.cursor/mempalace-index.md`, `graphify-index.md`, `project-cache.md`, `rules/atlas.mdc`, `skills/atlas/`, `atlas-import/`, `atlas-migrate-report.md`
- Restore any renamed legacy rule from git history

No cloud account is required for core Atlas.
