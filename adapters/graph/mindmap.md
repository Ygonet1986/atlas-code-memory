# GraphBackend: AI Mind Map

Optional alternative to Graphify (MCP knowledge graph).

## Install

Follow the upstream AI Mind Map MCP docs for your editor.

## Atlas wiring

Use Mind Map **instead of** Graphify as layer 4. Still maintain `graphify-index.md` as the **scope map** (name can stay; it means “code-graph index”), or rename entries’ descriptions to point at Mind Map scopes.

## Conflict

Do **not** run Graphify + Mind Map together. `atlas doctor` fails if both rule files are detected.
