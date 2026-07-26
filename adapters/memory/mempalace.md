# MemoryBackend: MemPalace

Optional. Atlas works without it (indexes only).

## Install

Follow https://github.com/MemPalace/mempalace — CLI `mempalace` + optional Cursor plugin/MCP.

## Atlas wiring

1. `atlas init` creates `.cursor/mempalace-index.md` with wing/rooms.
2. Agent searches the index, then calls MemPalace scoped to that wing/room.
3. Material writes use Atlas drawer taxonomy (`atlas checkpoint` before filing).

## Detection

`atlas doctor` checks `mempalace` on `PATH`.

## Without MemPalace

Skip layer 2. Decisions can still be drafted under `.cursor/atlas-import/` via `atlas import` until a backend is installed.
