# Changelog

## Unreleased

### Added
- `atlas cache build` / `atlas cache status`: the project-cache layer is now built
  from the source tree instead of being appended by hand. Descriptions come from
  module docstrings, leading comments or exported symbols; hand-written entries
  are preserved unless `--force`.
- `atlas doctor` reports project-cache coverage and tells you how to fix it.
- MCP tools `atlas_cache_status` / `atlas_cache_build`; daemon `GET|POST /api/cache`.
- The `post-commit` hook keeps the cache in sync after every commit.
- `atlas init` indexes the source tree on the way out, so routing answers the first
  question instead of needing a second command (`--no-cache` opts out).
- Real editor integrations in `atlas connect`: `windsurf` (`.windsurf/rules/`,
  `~/.codeium/windsurf/mcp_config.json`), `vscode`/`copilot` (`.vscode/mcp.json`
  with the `servers` key, `.github/copilot-instructions.md`), `zed` (`.rules`,
  `context_servers`) and `codex` (`AGENTS.md`).
- Negative bench cases (`expect_no_hits`, `expect_path_absent`) that measure what
  the router must *not* return, plus `atlas bench --real` against this repository.

### Security
- **The local daemon now requires a token.** It used to answer any caller with
  `Access-Control-Allow-Origin: *` and no authentication, so any page open in the
  user's browser could read every personal memory, write false ones, spend DeepSeek
  credits and trigger git pushes. Requests now need the token from
  `~/.atlas/daemon-token` (`atlas token`, `atlas token --rotate`, or
  `ATLAS_DAEMON_TOKEN`), sent as a bearer header, `X-Atlas-Token` or `?token=`.
  `atlas daemon --no-auth` restores the old behaviour and says so loudly.
- Wildcard CORS is gone. The daemon echoes an origin only for the desktop app's own
  origin, and rejects requests whose `Host` is not loopback, which blocks DNS
  rebinding.
- `GET /api/health` stays reachable without a token for liveness probes, but no
  longer discloses the version or the life-root path to an unauthenticated caller.
- **Team bundle extraction is sandboxed.** `atlas sync import` called
  `tarfile.extractall` with no filter on a file a teammate handed you. It now
  refuses absolute paths, `..` traversal, symlinks, hard links and device files,
  writes nothing if any member fails, and normalises file modes.

### Changed
- Routing drops English and Portuguese function words and tokens too common in the
  index to discriminate, so unrelated questions now return nothing instead of noise.
- The bench baseline honours `.atlasignore` and skips generated artifacts. Measured
  savings on a real repository is 78%, against 99% on the synthetic fixture.
- MCP `serverInfo.version` follows the package version instead of a hardcoded string.

### Fixed
- Editor configs are merged, never overwritten; unparseable JSONC is left alone and
  a snippet is written next to it.
- Skipped directory names are matched relative to the project root. A checkout living
  under a path containing `build/`, `dist/`, `vendor/` or `site-packages/` used to be
  invisible to both the cache builder and the bench baseline.
- `atlas bench --real` explains that it needs a source checkout instead of silently
  benchmarking whatever directory it landed in.
- `pyproject` URLs point at the actual repository.

## 0.3.1 — 2026-07-30

### Added
- Stronger `atlas migrate`: dry-run, `--no-import`, `--global-rule`, `--hooks`, migration report
- Portuguese → English field-label normalization (`endereço`/`escopo`/`grafo`/`descrição`)
- [docs/migration.md](docs/migration.md) + README Migration guide (English)

### Changed
- Canonical English keys/CLI: `scope`, `graph`, `path`, `description` (PT aliases still accepted)
- Examples and docs use `--scope` instead of `--escopo`

## 0.3.0 — 2026-07-29

### Added
- **Atlas Life**: temporal conversation memory (`day`/`week`/`month`/`year`) on a private GitHub repo
- CLI: `atlas life init|wake|remember|recall|rollup|pull|push|sync|serve`
- MCP tools: `atlas_life_wake`, `atlas_life_remember`, `atlas_life_recall`, `atlas_life_rollup`
- Drawer types: `memory`, `event`, `person`, `goal` (+ life rooms)
- Atlas Chat desktop (`apps/atlas-chat`): DeepSeek sidecar + Tauri scaffold; auto commit/push
- Docs: `docs/life.md`, `docs/atlas-chat.md`

## 0.2.0 — 2026-07-26

### Added
- MCP server (`atlas mcp` / `atlas-mcp`): recall_route, checkpoint, stale, protocol_score
- `atlas graph add|list|ready|stale`
- `atlas migrate`, `atlas onboard`, `atlas route`, `atlas watch`
- `atlas sync export|import` team bundles
- `atlas checkpoint --write|--mine` with `.cursor/atlas-drawers/<room>/` + `mempalace.yaml`
- Protocol eval via `atlas eval --transcript`
- Opt-in telemetry (`ATLAS_TELEMETRY=1` + `ATLAS_TELEMETRY_URL`)
- Claude Code / Codex `AGENTS.md` snippet
- Examples: python-service, nextjs-app, pnpm-monorepo
- Docs: MCP, team-sync, publishing; GitHub Pages index; publish workflow

## 0.1.0 — 2026-07-26

### Added
- Core protocol, CLI init/status/doctor/stale/import/checkpoint/eval/hooks/metrics
- Templates, schema, secret scanner, adapters, Cursor plugin scaffold
