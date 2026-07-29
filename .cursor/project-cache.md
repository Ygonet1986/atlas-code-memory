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

### RH bottlenecks + APB candidate
- **path:** `riemann-lab/notes/05_bottlenecks_and_candidate_theory.md`
- **description:** RH bottlenecks G1–G6 and APB/S·G·P attack speculation; explicitly not a proof.

### RH research log
- **path:** `riemann-lab/notes/06_research_log.md`
- **description:** PI decisions: MC2 Attack S demoted; pivot to Attack P (Li).

### riemann_lab.mc2_spectral
- **path:** `riemann-lab/src/riemann_lab/mc2_spectral.py`
- **description:** MC2 truncated-matrix experiment vs zeros; spacing metric.

### riemann_lab.li_battery
- **path:** `riemann-lab/src/riemann_lab/li_battery.py`
- **description:** Attack P battery — truncated Li coefficients (mpmath/numpy).

### riemann_lab.voros_sum
- **path:** `riemann-lab/src/riemann_lab/voros_sum.py`
- **description:** Voros sum Λ_n (A_nm, Φ_m Bernoulli) with mpmath; calibrated on Λ_1, Λ_2.

### riemann_lab.instinct
- **path:** `riemann-lab/src/riemann_lab/instinct.py`
- **description:** Digital instinct — dig_instinct vs proof_proximity (cap) vs proof_illusion.

### voros_lambda_n100
- **path:** `riemann-lab/notes/data/voros_lambda_n100.json`
- **description:** Voros Λ_n series through n=100 with remainders; all positive.

### voros_lambda_n200
- **path:** `riemann-lab/notes/data/voros_lambda_n200.json`
- **description:** Voros Λ_n series through n=200; tip remainders ~1e-4.

### false_rh_control
- **path:** `riemann-lab/src/riemann_lab/false_rh_control.py`
- **description:** Pedagogical false-RH control (DH-like off-line zero contaminant).

### research_tree
- **path:** `riemann-lab/research_tree.yaml`
- **description:** Research loop tree; switches by instinct.band.

### research_tree runner
- **path:** `riemann-lab/src/riemann_lab/research_tree.py`
- **description:** Walker sequence/switch/action; transcripts under notes/data/loop_runs/.

### dh_probe
- **path:** `riemann-lab/src/riemann_lab/dh_probe.py`
- **description:** Qualitative DH f_- probe (legacy); asymptote + off-line onset.

### dh_exact
- **path:** `riemann-lab/src/riemann_lab/dh_exact.py`
- **description:** Exact DH Λ± (Voros 1703.02844 eqs 92–96): Bernoulli poly 1/5,2/5; calibrated Λ±,1–2.

### dh_lambda_pm_exact
- **path:** `riemann-lab/notes/data/dh_lambda_pm_exact.json`
- **description:** Λ± series exported by dh_exact (default n≤40).

### riemann_lab.li_xi
- **path:** `riemann-lab/src/riemann_lab/li_xi.py`
- **description:** Li via ξ derivatives (safe at s=1); compares to truncated zero sum.

### Attack P Li survey
- **path:** `riemann-lab/notes/07_attack_p_li.md`
- **description:** Keiper–Li/Voros distillation and next Φ_m milestone.
