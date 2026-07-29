# Why Atlas

## One-liner

**Atlas is the token GPS for AI coding — orientation that cuts exploration cost.**

## Pitch

If you build software with Cursor, Claude Code, or Codex, you already know the loop:

1. Open a new chat  
2. Re-explain the architecture  
3. Watch the agent grep the wrong half of the monorepo  
4. Correct it  
5. Lose the correction when the thread ends  

Atlas breaks that loop with a **mandatory, portable protocol**:

```text
memory map → decisions → code graph → file index
```

You keep your editor and your models. You gain a shared orientation layer that works the same on every project — and burns fewer tokens getting there.

## Token economy (measurable)

Exploration is the expensive part. Atlas routes before grep:

```bash
atlas bench --fixture
```

On the bundled `eval/fixture-monorepo` (100+ decoy files), Atlas opens ranked `project-cache` hits while the baseline arm opens every matching decoy. Report fields:

| Field | Meaning |
|-------|---------|
| `token_proxy_baseline` | `chars/4` of files a blind grep would load |
| `token_proxy_atlas` | `chars/4` of indexes + routed targets |
| `savings_pct` | relative reduction |

Run against a real monorepo: `atlas bench -C /path/to/repo --cases eval/cases/bench`.

## Migrate if…

- You maintain more than one serious repo with an AI assistant  
- Architecture decisions keep getting rediscovered  
- You installed MemPalace / Graphify / Mind Map and need **one order**, not three  
- Token spend on “exploration” hurts more than generation  

## Don’t migrate yet if…

- The project is disposable and fits in one context window  
- You have no recurring decisions to remember  

Starting early still helps: `atlas init` is cheap and grows with the repo.

## Local app / any editor

```bash
pip install -e .
atlas daemon                 # HTTP: /api/route /api/wake /api/bench
atlas connect --editor cursor
# or: --editor claude | generic
```

MCP stdio remains `atlas-mcp`. The desktop shell (`apps/atlas-chat`) talks to the same daemon.

## Proof points

- Local-first, MIT, no required cloud  
- `atlas bench` A/B token-proxy harness (CI)  
- Secret scanning on checkpoints  
- Scoped graphs for large codebases  
- `atlas migrate` / `atlas onboard` for adoption  
- MCP + HTTP daemon for agents that speak tool-calling  
