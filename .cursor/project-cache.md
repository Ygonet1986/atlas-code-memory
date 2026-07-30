# Project Source Cache

Atlas layer 5. File inventory: name → path → description.
Search this file; never read it end-to-end. Partial updates only after each change.

<!-- atlas import and the agent append entries below -->

### revista-atlas.md
- **path:** `docs/revista-atlas.md`
- **description:** Artigo em português tom revista de informática — o que Atlas é, Walk, tokens, Life, daemon.

### article.md
- **path:** `docs/article.md`
- **description:** Whitepaper técnico ARP (retrieval protocol).

### readme.md
- **path:** `readme.md`
- **description:** Atlas Memory

### drawer.py
- **path:** `src/atlas_memory/drawer.py`
- **description:** Drawer parse/validate; project + life types/rooms (`memory`/`event`/`person`/`goal`, temporal rooms).

### life.py
- **path:** `src/atlas_memory/life.py`
- **description:** Atlas Life core — init/wake/remember/recall/rollup; wake prompt respects char_budget for token economy.

### life_git.py
- **path:** `src/atlas_memory/life_git.py`
- **description:** Git pull/commit/push + private GitHub check for life palace.

### life_chat_server.py
- **path:** `src/atlas_memory/life_chat_server.py`
- **description:** HTTP sidecar for Atlas Chat (DeepSeek + remember/sync APIs); honors life_root on GET.

### commands_life.py
- **path:** `src/atlas_memory/commands_life.py`
- **description:** CLI `atlas life` subcommands including serve and --entities on remember.

### commands_bench.py
- **path:** `src/atlas_memory/commands_bench.py`
- **description:** A/B token-proxy bench — blind grep vs recall_route; savings_pct report.

### daemon.py
- **path:** `src/atlas_memory/daemon.py`
- **description:** Local HTTP daemon (route/wake/bench/life) for any AI editor; ~/.atlas/config.json.

### commands_connect.py
- **path:** `src/atlas_memory/commands_connect.py`
- **description:** atlas connect — Cursor global rule+MCP+skill as default where/remember layer.

### cursor-default.md
- **path:** `docs/cursor-default.md`
- **description:** How Atlas becomes Cursor's default orientation + memory layer.

### atlas.mdc (rule)
- **path:** `cursor/rules/atlas.mdc`
- **description:** alwaysApply rule — Atlas Walk, Life, anti grep-first; Cursor authority table.

### routing.py
- **path:** `src/atlas_memory/routing.py`
- **description:** recall_route with wing match, stale weighting, char_budget; protocol_score.

### cli.py
- **path:** `src/atlas_memory/cli.py`
- **description:** Atlas CLI — bench, daemon, connect, life, eval, mcp, graph, etc.

### mcp_server.py
- **path:** `src/atlas_memory/mcp_server.py`
- **description:** MCP tools including atlas_life_* for Cursor.

### atlas-chat
- **path:** `apps/atlas-chat`
- **description:** Desktop UI — Chat, Mind Map, Entities, Savings tabs; Tauri spawns atlas daemon.

### atlas-chat-startup.ps1
- **path:** `scripts/atlas-chat-startup.ps1`
- **description:** Windows Startup script — start life serve (+static UI) and open browser.

### life_autostart.py
- **path:** `src/atlas_memory/life_autostart.py`
- **description:** Install/uninstall Startup shortcuts for Atlas Chat and AtlasDaemon.

### generate_bench_fixture.py
- **path:** `scripts/generate_bench_fixture.py`
- **description:** Builds eval/fixture-monorepo with decoys for token bench.

### mempalace.yaml
- **path:** `mempalace.yaml`
- **description:** Local MemPalace config (wing, rooms). Created by mempalace init; gitignored.

### entities.json
- **path:** `entities.json`
- **description:** Entities detected by MemPalace for this project. Created on init; gitignored.

### graphify-out (src)
- **path:** `src/graphify-out/`
- **description:** Graphify graph for the Python package. Scope `src` is ready in `.cursor/graphify-index.md`.

### adapters/memory/mempalace.md
- **path:** `adapters/memory/mempalace.md`
- **description:** Atlas MemPalace adapter doc (install + wiring).

### adapters/graph/graphify.md
- **path:** `adapters/graph/graphify.md`
- **description:** Atlas Graphify adapter doc (`uv tool install graphifyy`; scopes).

### docs/migration.md
- **path:** `docs/migration.md`
- **description:** English migration guide: bring existing projects into Atlas Memory.

### commands_migrate
- **path:** `src/atlas_memory/commands_migrate.py`
- **description:** Project migration to Atlas Memory: legacy rules, EN label normalize, import, report.

### atlas-doctor.md
- **path:** `.cursor-plugin/commands/atlas-doctor.md`
- **description:** atlas doctor

### atlas-init.md
- **path:** `.cursor-plugin/commands/atlas-init.md`
- **description:** Run in the project root:

### mindmap.md
- **path:** `adapters/graph/mindmap.md`
- **description:** Optional alternative to Graphify (MCP knowledge graph).

### none.md
- **path:** `adapters/memory/none.md`
- **description:** Atlas Core still provides:

### README.md
- **path:** `apps/atlas-chat/README.md`
- **description:** Desktop UI for Atlas Life (DeepSeek + private GitHub memory).

### api.ts
- **path:** `apps/atlas-chat/src/api.ts`
- **description:** Exports ChatMessage, Settings, MindmapNode, MindmapEdge, MindmapGraph, loadSettings, saveSettings, pull

### App.tsx
- **path:** `apps/atlas-chat/src/App.tsx`
- **description:** Exports App

### main.tsx
- **path:** `apps/atlas-chat/src/main.tsx`
- **description:** tsx source at apps/atlas-chat/src/main.tsx

### vite-env.d.ts
- **path:** `apps/atlas-chat/src/vite-env.d.ts`
- **description:** <reference types="vite/client" />

### build.rs
- **path:** `apps/atlas-chat/src-tauri/build.rs`
- **description:** rs source at apps/atlas-chat/src-tauri/build.rs

### lib.rs
- **path:** `apps/atlas-chat/src-tauri/src/lib.rs`
- **description:** Exposes run

### main.rs
- **path:** `apps/atlas-chat/src-tauri/src/main.rs`
- **description:** rs source at apps/atlas-chat/src-tauri/src/main.rs

### vite.config.ts
- **path:** `apps/atlas-chat/vite.config.ts`
- **description:** ts source at apps/atlas-chat/vite.config.ts

### CHANGELOG.md
- **path:** `CHANGELOG.md`
- **description:** - Stronger `atlas migrate`: dry-run, `--no-import`, `--global-rule`, `--hooks`, migration report

### CONTRIBUTING.md
- **path:** `CONTRIBUTING.md`
- **description:** pip install -e ".[dev]"

### reference.md
- **path:** `cursor/skills/atlas/reference.md`
- **description:** [type:decision] [status:active]

### SKILL.md
- **path:** `cursor/skills/atlas/SKILL.md`
- **description:** name: atlas

### adapters.md
- **path:** `docs/adapters.md`
- **description:** Atlas Core does not vendor MemPalace or Graphify. It defines slots:

### atlas-chat.md
- **path:** `docs/atlas-chat.md`
- **description:** Desktop shell for **Atlas**: local daemon (token GPS + Life) + DeepSeek chat + GitHub private sync.

### concepts.md
- **path:** `docs/concepts.md`
- **description:** AI coding agents are strong at generating code and weak at **orientation**:

### index.md
- **path:** `docs/index.md`
- **description:** - [Why Atlas](why-atlas.md) — why adopt or migrate

### life-spec.md
- **path:** `docs/life-spec.md`
- **description:** **Version:** 1.0

### life.md
- **path:** `docs/life.md`
- **description:** Personal conversation memory on a **private** GitHub repo, with temporal drawers and Mind Map scopes.

### mcp.md
- **path:** `docs/mcp.md`
- **description:** atlas mcp

### protocol.md
- **path:** `docs/protocol.md`
- **description:** **Version:** 1.0

### publishing.md
- **path:** `docs/publishing.md`
- **description:** cd /path/to/atlas-memory

### quickstart.md
- **path:** `docs/quickstart.md`
- **description:** git clone https://github.com/Ygonet1986/atlas-memory.git

### security.md
- **path:** `docs/security.md`
- **description:** - Atlas runs locally; no required cloud.

### team-sync.md
- **path:** `docs/team-sync.md`
- **description:** atlas sync export -C . -o atlas-bundle.tar.gz

### why-atlas.md
- **path:** `docs/why-atlas.md`
- **description:** **Atlas is the token GPS for AI coding — orientation that cuts exploration cost.**

### cursor/README.md
- **path:** `hooks/cursor/README.md`
- **description:** name = "atlas-memory"

### AGENTS.snippet.md
- **path:** `integrations/agents/AGENTS.snippet.md`
- **description:** Follow Atlas order: mempalace-index → MemPalace → graphify-index → Graphify|MindMap → project-cache.

### agents/README.md
- **path:** `integrations/agents/README.md`
- **description:** Add to your project `CLAUDE.md` or `AGENTS.md`:

### README.md
- **path:** `README.md`
- **description:** [![CI](https://img.shields.io/github/actions/workflow/status/Ygonet1986/atlas-memory/ci.yml?label=CI)](https://github.com/Ygonet1986/atlas-memory/actions)

### __init__.py
- **path:** `src/atlas_memory/__init__.py`
- **description:** py source at src/atlas_memory/__init__.py

### commands_cache.py
- **path:** `src/atlas_memory/commands_cache.py`
- **description:** Build and audit the project-cache layer directly from the source tree.

### commands_checkpoint.py
- **path:** `src/atlas_memory/commands_checkpoint.py`
- **description:** Defines ensure_mempalace_yaml, drawers_root, write_drawer_file, file_checkpoint

### commands_doctor.py
- **path:** `src/atlas_memory/commands_doctor.py`
- **description:** Defines which, doctor

### commands_eval.py
- **path:** `src/atlas_memory/commands_eval.py`
- **description:** Defines EvalCase, load_cases, run_eval

### commands_graph.py
- **path:** `src/atlas_memory/commands_graph.py`
- **description:** Defines list_graphs, add_graph, set_graph_status

### commands_hooks.py
- **path:** `src/atlas_memory/commands_hooks.py`
- **description:** Defines install_git_hooks

### commands_import.py
- **path:** `src/atlas_memory/commands_import.py`
- **description:** Defines import_docs

### commands_init.py
- **path:** `src/atlas_memory/commands_init.py`
- **description:** Defines init_project

### commands_onboard.py
- **path:** `src/atlas_memory/commands_onboard.py`
- **description:** Defines onboard

### commands_stale.py
- **path:** `src/atlas_memory/commands_stale.py`
- **description:** Defines StaleReport, parse_graphify_index, stale_report, mark_stale_touched

### commands_sync.py
- **path:** `src/atlas_memory/commands_sync.py`
- **description:** Defines export_bundle, import_bundle

### commands_watch.py
- **path:** `src/atlas_memory/commands_watch.py`
- **description:** Defines watch_project

### metrics.py
- **path:** `src/atlas_memory/metrics.py`
- **description:** Defines metrics_path, record, summary

### paths.py
- **path:** `src/atlas_memory/paths.py`
- **description:** Defines package_data_root, repo_root_from_pkg, data_dir

### secrets.py
- **path:** `src/atlas_memory/secrets.py`
- **description:** Defines SecretHit, scan_text, is_denied_filename, load_atlasignore

### telemetry.py
- **path:** `src/atlas_memory/telemetry.py`
- **description:** Defines maybe_send_telemetry

### graphify-index.md
- **path:** `templates/graphify-index.md`
- **description:** Atlas layer 3. Map of scoped code graphs.

### life-SKILL.snippet.md
- **path:** `templates/life-SKILL.snippet.md`
- **description:** atlas life init [--repo OWNER/atlas-life]

### mempalace-index.md
- **path:** `templates/mempalace-index.md`
- **description:** Atlas layer 1. Map of wings/rooms for this project.

### project-cache.md
- **path:** `templates/project-cache.md`
- **description:** Atlas layer 5. File inventory: name → path → description.

### test_bench.py
- **path:** `tests/test_bench.py`
- **description:** Defines test_token_proxy, test_bench_fixture_saves_tokens

### test_checkpoint_write.py
- **path:** `tests/test_checkpoint_write.py`
- **description:** Defines test_file_checkpoint_write

### test_daemon_connect.py
- **path:** `tests/test_daemon_connect.py`
- **description:** Defines test_connect_cursor_dry_run, test_connect_cursor_write, test_connect_cursor_global, test_connect_generic, test_daemon_config

### test_drawer.py
- **path:** `tests/test_drawer.py`
- **description:** Defines test_parse_drawer_ok, test_secret_rejected, test_scan_github_pat

### test_init.py
- **path:** `tests/test_init.py`
- **description:** Defines test_init_creates_indexes, test_parse_skips_placeholders

### test_life.py
- **path:** `tests/test_life.py`
- **description:** Defines test_life_drawer_types_ok, test_life_init_wake_remember_rollup, test_remember_with_entities, test_hot_drawers_pinned, test_entity_alias_and_merge, test…

### test_life_chat.py
- **path:** `tests/test_life_chat.py`
- **description:** Defines test_extract_memories_strips_json, test_extract_memories_none, test_query_life_root_override

### test_migrate.py
- **path:** `tests/test_migrate.py`
- **description:** Defines test_migrate_normalizes_portuguese_labels, test_migrate_dry_run_does_not_write_labels, test_normalize_english_labels_alone, test_migrate_moves_legacy_r…

### test_routing_graph.py
- **path:** `tests/test_routing_graph.py`
- **description:** Defines test_graph_add_list, test_protocol_score_prefers_atlas_before_grep, test_recall_route

### test_bench_negative.py
- **path:** `tests/test_bench_negative.py`
- **description:** Defines make_project, write_case, test_negative_case_passes_when_router_stays_silent, test_negative_case_fails_when_router_leaks, test_expect_path_absent_catch…

### test_cache_build.py
- **path:** `tests/test_cache_build.py`
- **description:** Defines make_project, test_build_indexes_every_source_file, test_build_uses_docstrings_and_comments, test_build_preserves_handwritten_entries, test_force_refre…

### test_connect_editors.py
- **path:** `tests/test_connect_editors.py`
- **description:** Defines home, test_windsurf_writes_its_own_rule_and_mcp, test_vscode_uses_servers_key_and_copilot_instructions, test_zed_writes_rules_file_and_context_server,…

### test_routing_precision.py
- **path:** `tests/test_routing_precision.py`
- **description:** Defines write_cache, test_query_tokens_drop_function_words, test_query_tokens_drop_portuguese_function_words, test_unrelated_question_returns_no_hits, test_rel…

### test_init_builds_cache.py
- **path:** `tests/test_init_builds_cache.py`
- **description:** Defines make_source_tree, test_init_leaves_the_router_usable, test_init_reports_how_many_files_it_indexed, test_no_cache_flag_skips_indexing

### test_installed_layout.py
- **path:** `tests/test_installed_layout.py`
- **description:** Guards for behaviour that only breaks once Atlas is installed as a wheel.

### http_auth.py
- **path:** `src/atlas_memory/http_auth.py`
- **description:** Access control for the local Atlas HTTP daemon.

### test_bundle_extract.py
- **path:** `tests/test_bundle_extract.py`
- **description:** Defines add_file, test_parent_traversal_is_refused, test_absolute_path_is_refused, test_symlink_is_refused, test_device_files_are_refused, test_nothing_is_writ…

### test_daemon_auth.py
- **path:** `tests/test_daemon_auth.py`
- **description:** Defines server, get, test_request_without_token_is_rejected, test_wrong_token_is_rejected, test_bearer_header_is_accepted, test_custom_header_and_query_param_a…
