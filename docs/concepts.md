# Concepts

## Why Atlas exists

AI coding agents are strong at generating code and weak at **orientation**:

- Every new chat forgets last week’s decisions.
- Grep-first exploration burns tokens on huge trees.
- Multiple “memory” tools compete with `alwaysApply` rules.

Atlas is the **standard route** so any agent, on any project, looks in the same places in the same order.

## Why migrate

| Before | After Atlas |
|--------|-------------|
| Decisions trapped in old chats | Typed drawers + wing/room map |
| Blind repo search | `project-cache` + scoped graphs |
| Graphify *and* Mind Map both yelling “query me” | One graph backend per project |
| Manual onboarding every hire/session | `atlas onboard` / `atlas migrate` |

Migrate when you already pay the tax of re-explaining architecture — not when the repo is still a weekend toy.

## Solution

Atlas is a **router**, not another model:

1. **Where is memory for this project?** → `mempalace-index`
2. **What did we decide?** → MemPalace (optional)
3. **Which code map?** → `graphify-index`
4. **How do symbols connect?** → Graphify or Mind Map (optional, exclusive)
5. **Which file?** → `project-cache`

## Design rules

- One order, graceful skip
- Typed drawers + git fields
- Code wins over stale memory
- Secrets never stored
- Scoped graphs for large monorepos
- Local metrics only (opt-in counters)
