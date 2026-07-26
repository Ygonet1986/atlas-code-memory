# Concepts

## Problem

Coding agents reset context every session. They re-grep large repos and forget decisions.

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
