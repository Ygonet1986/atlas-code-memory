# Atlas Retrieval Protocol (ARP) v1

## The Problem

Every time you open a new chat with an AI coding agent, it starts from zero. It doesn't know you chose Postgres last month. It doesn't know the team agreed on a specific folder structure. It doesn't know you prefer dark mode or that Alice from accounting needs the CSV export to match the legacy format.

The agent greps your repo, burns tokens re-reading the same files, and gives you contradictory advice because it never saw last week's thread. If you add multiple memory tools — a knowledge graph here, a personal memory there — they fight each other, and the agent doesn't know which one to trust.

**The model is not the bottleneck. Orientation is.**

---

Current agents optimize generation.

Atlas optimizes orientation.

---

## What Atlas Is

Atlas is not a memory system. It is a **deterministic retrieval protocol**.

It does not store embeddings. It does not run a vector database. It does not try to be another brain. Atlas defines a fixed lookup order — the **Atlas Walk** — that every agent, in every session, must follow to find the answer to any question.

Given the same question and the same state, the agent always walks the same path to the same answer. The protocol is deterministic. The protocol never changes.

**Router, not another brain.**

---

## What Atlas Does Not Do

Atlas does not:

- Replace RAG pipelines
- Replace vector databases
- Replace code indexing tools
- Replace git
- Replace LLM memory or context windows

Atlas only defines **lookup order**. It tells existing tools when to speak and in what sequence. It is composable by design — swap any backend without changing the protocol.

---

## The Atlas Walk

Every query executes an Atlas Walk: a sequential lookup through five layers, stopping at the first hit.

```
         Question
            |
     Memory Index -----> FOUND? --> stop
            |
    Memory Provider ---> FOUND? --> stop
            |
      Graph Index ------> FOUND? --> stop
            |
    Graph Provider -----> FOUND? --> stop
            |
    Index Provider -----> open file
```

Every Atlas-compatible client MUST execute the Walk in this order. Missing layer? Skip it. Never invent a memory hit.

A layer can respond with FOUND, NOT_FOUND, SKIP (not configured), STALE (needs refresh), ERROR, or PARTIAL. Only FOUND stops the Walk. Everything else continues to the next layer.

### Why five layers

Each layer answers a different question. The sequence mirrors how humans navigate large systems: first orient, then recall, then map, then locate.

| Layer | Question | Analogy |
|-------|----------|---------|
| Memory Index | Where should I search? | DNS lookup |
| Memory Provider | What did we decide? | L1 cache hit |
| Graph Index | Which code area matters? | Page table lookup |
| Graph Provider | How is it connected? | Virtual memory walk |
| Index Provider | Which file should I open? | Filesystem open() |

### Cost model

The number of lookup stages is constant (five). Each stage may have its own implementation-specific cost, but the protocol bounds the retrieval process to a fixed sequence of layers. Upper layers are intentionally tiny — a memory index is a few kilobytes, a drawer is a handful of structured lines. Most lookups terminate before reaching the Index Provider.

An agent working on a 100,000-file monorepo pays the same protocol overhead as one working on a 50-file project.

---

## The Five Layers

### Layer 1 — Memory Index

A structured file listing **wings** (one per year or domain) and **rooms** (architecture, debugging, conventions, etc.). The agent searches by keyword — it never reads the whole thing.

### Layer 2 — Memory Provider

Any backend that stores and retrieves **drawers** — the atomic unit of memory.

A drawer is:

- **Small** — a few lines of structured text, not an embedding blob
- **Versionable** — it's a file in a git repo; diffs, blame, PRs for free
- **Explainable** — a human can read it and understand the reasoning
- **Auditable** — git metadata traces it back to the exact change
- **Scannable** — secret scanning runs before every write

If code contradicts a drawer, **code wins** — the drawer gets marked `superseded`. This is a hard rule, not a guideline.

The protocol does not prescribe which Memory Provider to use. MemPalace, a flat directory of markdown files, a database — any backend that implements the drawer schema is valid.

### Layer 3 — Graph Index

A list of **scoped graphs**, each covering a specific area of the codebase. The agent picks the right scope instead of loading a mega-graph.

### Layer 4 — Graph Provider

The actual graph for the selected scope. The protocol recognizes two classes:

| Class | Purpose |
|-------|---------|
| Semantic code graph | Symbols, imports, call chains, dependency trees |
| Visual knowledge graph | Topics, entities, relationships, mind maps |

An implementation may support either or both classes, but MUST NOT activate more than one at a time. Two engines produce conflicting signals.

### Layer 5 — Index Provider (Project Cache)

A keyword-searchable index of every file in the project. Always present, always the last stop.

### Layer contract

| Layer | Input | Output |
|-------|-------|--------|
| Memory Index | Query keywords | Wing + Room |
| Memory Provider | Room (or keywords) | Drawers |
| Graph Index | File/symbol context | Scope name |
| Graph Provider | Scope | Symbols / edges |
| Index Provider | Keywords | File path |

---

## Drawer Schema

```yaml
Drawer:
  type:        string    # REQUIRED: decision | lesson | preference | bugfix | build
                         # (life: memory | event | person | goal)
  status:      string    # REQUIRED: active | superseded | archived
  summary:     string    # REQUIRED: one sentence
  id:          string    # RECOMMENDED: stable unique identifier
  why:         string    # RECOMMENDED: reasoning
  branch:      string    # RECOMMENDED: git branch (or "-")
  commit:      string    # RECOMMENDED: git commit hash (or "-")
  pr:          string    # OPTIONAL: pull request reference
  files:       list      # OPTIONAL: source files involved
  supersedes:  string    # OPTIONAL: id of replaced drawer
  wing:        string    # OPTIONAL: memory index wing
  room:        string    # OPTIONAL: memory index room
  when:        string    # OPTIONAL: ISO 8601 date (life mode)
  period:      string    # OPTIONAL: day | week | month | year
  topics:      list      # OPTIONAL: keyword tags
  entities:    list      # OPTIONAL: named entities
  pinned:      boolean   # OPTIONAL: always in hot set
  created:     string    # OPTIONAL: ISO 8601 datetime
  updated:     string    # OPTIONAL: ISO 8601 datetime
```

---

## Session Lifecycle

Every session follows three named operations: **Wake**, **Work**, **Checkpoint**.

### Wake

Load the memory index + a small **hot set** of drawers. Hot means relevant, not just recent: recently used, frequently accessed, related to the current branch, pinned by the user, or connected to active entities.

No full memory dump. The agent starts oriented, not overwhelmed.

### Work (Atlas Walk + modifications)

For each question, execute an Atlas Walk. Read and modify real files using paths from the Index Provider.

### Checkpoint

After meaningful changes, write a drawer summarizing what happened and why. This is how the memory grows — one small, typed, auditable unit at a time.

Stale detection: if a file change invalidates a graph scope, mark it stale. Refresh before the next read.

---

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Memory Index missing | Skip Layer 1; continue |
| Memory Provider unavailable | Skip Layer 2; continue |
| Graph scope stale | Refresh; if fails, skip |
| Drawer corrupted | Skip drawer; log warning |
| Index Provider outdated | Rebuild; use stale with warning |
| Secret detected in drawer | Reject the write |
| Concurrent write conflict | Git merge; latest commit wins |

---

## Why Atlas Is Different

Most memory systems try to remember everything. Atlas tries to remember just enough to answer the next question.

Most systems optimize storage. Atlas optimizes retrieval.

Most systems ask: *"What should we save?"*
Atlas asks: *"Where should the agent look first?"*

### Compared to existing systems

| System | Approach | Atlas difference |
|--------|----------|-----------------|
| Mem0 | Embedding-based personal memory | Atlas doesn't embed; it routes to structured drawers |
| Zep | Session memory with temporal decay | Atlas uses explicit lifecycle (active/superseded/archived), not decay |
| Graphiti | Temporal knowledge graph | Atlas separates the graph from the protocol; graph is one layer, not the system |
| Cognee | RAG pipeline with knowledge graphs | Atlas is not a pipeline; it's a lookup order that any pipeline can follow |
| Supermemory | Universal memory layer | Atlas is not a layer; it's the sequence in which layers are consulted |

---

## Atlas Life: Versioned Human Memory

Atlas started as a code memory router, but the same protocol works for personal conversations.

**Atlas Life treats conversations as versioned knowledge rather than disposable chat history.**

This is git for human memory. Every conversation produces structured drawers, committed to a private repository, organized by time, and linked to the people and concepts they mention.

### Temporal organization

```
day → week → month → year
```

Daily drawers accumulate. `rollup` consolidates them — like git squash, but for memory.

### Entities

Every person, place, or concept gets an entity index with aliases, co-occurrence tracking, and relationship graphs. A person like "Alice" might appear across months of drawers. The entity index resolves aliases ("Ali" maps to "Alice"), tracks co-occurrences ("Alice and Bob appeared in 7 shared drawers"), and supports merge operations.

### Session init

At the end of each conversation, Atlas saves a checkpoint. The next Wake loads it. The greeting changes from "How can I help you?" to "Continuing from where we left off."

---

## The Protocol as a Standard

The most important property of Atlas is not any single component. It is this:

**The protocol never changes.**

The Atlas Walk is the same whether the client is Cursor, Claude, GPT, Gemini, DeepSeek, Codex, or Aider. Any agent that implements the Walk gets deterministic memory retrieval.

This is analogous to how POSIX standardized the interface between applications and operating systems. Atlas proposes the same for agent memory: a stable ABI between agents and the knowledge they need.

### Conformance Levels

| Level | Requires | Capability |
|-------|----------|------------|
| 0 | Index Provider | File discovery |
| 1 | + Memory Index + Memory Provider | Decision recall, checkpoints |
| 2 | + Graph Index + Graph Provider | Code relationship mapping |
| 3 | + Life mode (temporal + entities) | Personal memory across sessions |

A Level 0 implementation is useful on day one. Higher levels add capability without changing the Walk.

### Implications

- **Interoperability** — A drawer written by one agent can be read by any other.
- **Portability** — Switch agents without losing project memory. Drawers live in the repo, not in any vendor's cloud.
- **Auditability** — Every memory is a file. Review it, diff it, revert it.
- **Composability** — Swap any provider. The protocol only defines the order.

---

## Design Principles

1. **One protocol, every project.** The agent always executes the same Atlas Walk.
2. **Router, not another brain.** Atlas doesn't think. It points.
3. **Works at day one.** Index Provider alone is useful. Add layers as the project grows.
4. **Code wins.** When a drawer says one thing and the code says another, the code is right.
5. **No secrets in memory.** Scanned before every write. Fail loud.
6. **Scoped, not global.** Small graphs per feature, not one massive index.
7. **Git-native.** Drawers are files. Diffs, blame, PRs — all work.
8. **Protocol-first.** The value is in the Atlas Walk, not in any single implementation.

---

## Conclusion

Without Atlas, every session starts from zero. The agent spends its budget orienting instead of solving.

With Atlas, the agent starts from the last checkpoint. It knows what the project decided, where the code lives, and what you talked about yesterday.

Memory that survives the session. Retrieval that never changes.

That's Atlas.

---

*For the normative protocol specification, see [ARP Specification](protocol.md).*
*For the Atlas Life specification, see [Life Spec](life-spec.md).*
*For the reference implementation, see [README](../README.md).*
