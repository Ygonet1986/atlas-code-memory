---
name: atlas-onboard
description: >-
  Explain and bootstrap a repository using only the Atlas memory stack.
  Use when onboarding to a new codebase or when the user asks to set up Atlas.
---

# Atlas onboard

1. Run `atlas init` if indexes are missing.
2. Run `atlas import` to seed cache from README/ADRs.
3. Run `atlas doctor`.
4. Search `mempalace-index`, then `graphify-index`, then `project-cache` — never whole-repo grep first.
5. Write a short onboarding brief: stack, entrypoints, risks, suggested first graph scopes.
6. Optionally draft 1–3 `decision` drawers under `.cursor/atlas-drawers/` via `atlas checkpoint --write`.
