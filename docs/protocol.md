# Atlas Retrieval Protocol Specification

**Version:** 1.0
**Status:** Draft
**Date:** 2026-07-29

## 1. Abstract

The Atlas Retrieval Protocol (ARP) defines a deterministic lookup order for AI agents to resolve questions against structured project memory. It specifies five layers, a session lifecycle, a drawer format, conformance levels, and failure modes. The protocol is implementation-agnostic: any agent, IDE, or tool MAY implement it without depending on a specific vendor or backend.

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

- **Atlas Walk** — The sequential lookup through all protocol layers for a given query.
- **Drawer** — The atomic unit of memory: a typed, structured file with a defined schema.
- **Layer** — One of the five retrieval stages in the Atlas Walk.
- **Hit** — A layer response indicating that relevant information was found. See Section 5 for the formal definition.
- **Hot set** — The subset of drawers loaded during Wake, selected by relevance scoring.
- **Wing** — A top-level grouping in the Memory Index (e.g., by year or domain).
- **Room** — A second-level grouping within a wing (e.g., architecture, debugging).
- **Scope** — A named subgraph in the Graph Index covering a specific code area.
- **Entity** — A named person, place, object, or concept tracked across drawers.
- **Memory Provider** — Any backend that stores and retrieves drawers (Layer 2).
- **Graph Provider** — Any backend that stores and queries code/knowledge graphs (Layer 4).
- **Index Provider** — Any backend that provides keyword-searchable file indexes (Layer 5).

## 3. Protocol Overview

An Atlas-compatible client MUST execute the Atlas Walk for every retrieval query. The Walk proceeds through layers 1 through 5 in strict order. The client MUST stop at the first layer that produces a Hit. If a layer is not present (no index file, no adapter configured), the client MUST skip it and proceed to the next.

A client MUST NOT invent memory hits. If no layer produces a Hit, the client MUST report that no memory was found.

The number of lookup stages is constant (five). Each stage MAY have its own implementation-specific cost, but the protocol bounds the retrieval process to a fixed sequence of layers.

## 4. Layer Definitions

### 4.1 Layer 1 — Memory Index

**Purpose:** Determine which memory wing and room are relevant to the query.

**Input:** Query keywords.
**Output:** Wing and room identifiers, or SKIP.
**Skip condition:** Index file does not exist.

The Memory Index is a structured file listing wings and rooms with descriptions. The client MUST search it by keyword. The client MUST NOT read the file end-to-end.

### 4.2 Layer 2 — Memory Provider

**Purpose:** Retrieve decisions, lessons, and other structured knowledge.

**Input:** Wing/room from Layer 1 (or query keywords if Layer 1 was skipped).
**Output:** Matching drawers, or SKIP.
**Skip condition:** No Memory Provider is configured.

This layer is OPTIONAL. When present, the client SHOULD retrieve drawers scoped to the wing/room identified in Layer 1. The protocol does not prescribe a specific Memory Provider implementation. Any backend that stores and retrieves drawers conforming to the Drawer Schema (Section 7) is a valid Memory Provider.

### 4.3 Layer 3 — Graph Index

**Purpose:** Identify which code graph scope is relevant.

**Input:** Query context (file paths, module names, symbols).
**Output:** Scope name, or SKIP.
**Skip condition:** Index file does not exist.

The Graph Index is a structured file listing named scopes with paths and status. The client MUST search it by keyword.

### 4.4 Layer 4 — Graph Provider

**Purpose:** Resolve code relationships within the selected scope.

**Input:** Scope from Layer 3.
**Output:** Symbol relationships, call chains, dependency edges, or SKIP.
**Skip condition:** No Graph Provider is configured, or no scope was selected.

A conforming implementation MUST use at most one Graph Provider at a time. Running two graph engines simultaneously is a protocol violation because it produces conflicting signals.

The protocol recognizes two classes of Graph Provider:

| Class | Purpose |
|-------|---------|
| Semantic code graph | Symbols, imports, call chains, dependency trees |
| Visual knowledge graph | Topics, entities, relationships, mind maps |

An implementation MAY support either or both classes, but MUST NOT activate more than one simultaneously.

### 4.5 Layer 5 — Index Provider (Project Cache)

**Purpose:** Locate the specific file to open.

**Input:** Query keywords, paths from upper layers.
**Output:** File path and description.
**Skip condition:** Never skipped. This layer MUST always be present.

The Index Provider maintains a keyword-searchable index of project files. The client MUST search by keyword. The client MUST NOT read the index end-to-end.

### 4.6 Layer Contract Summary

| Layer | Input | Output | Provider interface |
|-------|-------|--------|--------------------|
| 1. Memory Index | Query keywords | Wing + Room | Built-in (file) |
| 2. Memory Provider | Room (or keywords) | Drawers | Pluggable |
| 3. Graph Index | File/symbol context | Scope name | Built-in (file) |
| 4. Graph Provider | Scope | Symbols / edges | Pluggable |
| 5. Index Provider | Keywords | File path | Built-in (file) |

## 5. Hit Definition

A layer response is classified as one of the following:

| Status | Meaning | Action |
|--------|---------|--------|
| FOUND | Layer returned relevant information | Stop the Walk; use this result |
| NOT_FOUND | Layer exists but had no match | Continue to next layer |
| SKIP | Layer is not configured / index missing | Continue to next layer |
| STALE | Layer exists but data is outdated | Refresh if possible, then retry; if refresh fails, continue |
| ERROR | Layer encountered an unrecoverable error | Log the error; continue to next layer |
| PARTIAL | Layer returned incomplete information | Continue to next layer to augment; MAY combine results |

A **Hit** is defined as a FOUND response. The client MUST stop the Walk at the first FOUND. For PARTIAL responses, the client MAY continue walking to augment the result, but SHOULD prefer the earliest layer's data in case of conflict.

## 6. Session Lifecycle

### 6.1 Wake

At the start of a session, the client MUST:

1. Load the Memory Index (Layer 1).
2. Load a hot set of drawers from the Memory Provider (Layer 2), if present.

The hot set SHOULD be selected by relevance scoring, considering:

- Recency (file modification time)
- Access frequency (usage counters)
- Branch affinity (drawers matching the current git branch)
- Pin status (drawers explicitly marked as pinned)
- Entity activity (drawers linked to recently active entities)

The hot set size SHOULD be bounded (RECOMMENDED: 8-12 drawers). The client MUST NOT load the full memory store during Wake.

### 6.2 Work

During the session, the client executes Atlas Walks as needed. Between walks, it reads and modifies real source files using paths obtained from the Index Provider (Layer 5).

### 6.3 Checkpoint

After meaningful changes, the client SHOULD write a drawer summarizing the change. The drawer MUST pass validation (type, status, secret scan) before being persisted.

### 6.4 Stale Detection

If a source file change invalidates a graph scope, the client SHOULD mark the scope as `stale` in the Graph Index. The client MUST NOT read from a stale scope without first attempting to refresh it.

## 7. Drawer Schema

### 7.1 Header

The first line MUST match:

```
[type:<TYPE>] [status:<STATUS>]
```

### 7.2 Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| type | REQUIRED | string | Drawer type (see 7.3) |
| status | REQUIRED | string | `active`, `superseded`, or `archived` |
| summary | REQUIRED | string | One-sentence description |
| id | RECOMMENDED | string | Stable unique identifier (for sync/dedup) |
| why | RECOMMENDED | string | Reasoning behind this knowledge |
| branch | RECOMMENDED | string | Git branch, or `-` |
| commit | RECOMMENDED | string | Git commit hash, or `-` |
| pr | OPTIONAL | string | Pull request reference, or `-` |
| files | OPTIONAL | list | Source files involved (comma-separated) |
| supersedes | OPTIONAL | string | Identifier of the drawer this replaces |
| wing | OPTIONAL | string | Memory palace wing |
| room | OPTIONAL | string | Memory palace room |
| when | OPTIONAL | string | ISO 8601 date (life mode) |
| period | OPTIONAL | string | `day`, `week`, `month`, or `year` (life mode) |
| topics | OPTIONAL | list | Keyword tags (comma-separated) |
| entities | OPTIONAL | list | Named entities (comma-separated) |
| pinned | OPTIONAL | boolean | If true, always include in hot set |
| created | OPTIONAL | string | ISO 8601 datetime of creation |
| updated | OPTIONAL | string | ISO 8601 datetime of last modification |

### 7.3 Drawer Types

**Project types:** `decision`, `lesson`, `preference`, `bugfix`, `build`

**Life types (Level 3):** `memory`, `event`, `person`, `goal`, `preference`, `lesson`, `decision`

Implementations MAY define additional types provided they do not conflict with the above.

### 7.4 Status Transitions

```
active --[code contradicts]--> superseded
active --[no longer relevant]--> archived
superseded --[correction]--> active (new drawer, not mutation)
```

When source code contradicts an active drawer, the drawer MUST be marked `superseded`. Code always wins over memory.

### 7.5 Secret Scanning

Before persisting any drawer, the implementation MUST scan its content for secrets (API keys, tokens, passwords, private keys). If a secret is detected, the write MUST fail. No secrets MAY reach the memory layer.

## 8. Failure Modes

Implementations MUST handle the following failure modes gracefully:

| Failure | Required behavior |
|---------|-------------------|
| Memory Index missing | SKIP Layer 1; continue Walk |
| Memory Provider unavailable | SKIP Layer 2; continue Walk |
| Graph Index missing | SKIP Layer 3; continue Walk |
| Graph Provider unavailable | SKIP Layer 4; continue Walk |
| Graph scope stale | Attempt refresh; if refresh fails, SKIP and log warning |
| Drawer corrupted (parse failure) | SKIP the drawer; log warning; do NOT halt the Walk |
| Index Provider outdated | Rebuild index; if rebuild fails, use stale data with warning |
| Secret detected in drawer | REJECT the write; return error to caller |
| Concurrent write conflict | Defer to version control (git merge); latest commit wins |

## 9. Concurrency

### 9.1 Multiple Writers

When multiple agents or clients write drawers to the same repository concurrently, the following rules apply:

- Each drawer is a separate file. Concurrent writes to different drawers MUST NOT conflict.
- If two agents write a drawer with the same filename, the version control system (git) is the arbiter. The implementation SHOULD use unique filenames (e.g., including timestamps) to minimize conflicts.
- Memory and Graph indexes are append-oriented. Concurrent appends SHOULD be resolved by git merge. If a merge conflict occurs, the implementation SHOULD accept both entries.

### 9.2 Read During Write

A client MAY read from any layer while another client is writing. Readers MUST tolerate partially-written files gracefully (treat parse failures as SKIP).

### 9.3 Locking

The protocol does NOT require locking. File-level atomicity provided by the operating system and git is sufficient for the expected workload (low-frequency writes of small files).

## 10. Conformance Levels

| Level | Required Layers | Capability |
|-------|----------------|------------|
| 0 | Layer 5 (Index Provider) | File discovery and keyword search |
| 1 | + Layer 1 (Memory Index) + Layer 2 (Memory Provider) | Decision recall, checkpoints, structured memory |
| 2 | + Layer 3 (Graph Index) + Layer 4 (Graph Provider) | Code relationship mapping, scoped graphs |
| 3 | + Life mode (temporal drawers + entities) | Personal memory, session continuity, entity tracking |

A Level 0 implementation MUST support Index Provider search. Each subsequent level adds the layers below it.

An implementation MAY claim partial conformance (e.g., "Level 1 without external Memory Provider — drawers stored as plain files") provided it documents which optional components are missing.

An implementation claiming a conformance level MUST pass the corresponding test suite for that level (when a test suite is published).

## 11. Life Mode (Level 3)

### 11.1 Temporal Organization

Life mode organizes drawers into temporal directories:

```
<drawers_root>/day/<YYYY-MM-DD>/
<drawers_root>/week/<YYYY-Wnn>/
<drawers_root>/month/<YYYY-MM>/
<drawers_root>/year/<YYYY>/
```

### 11.2 Entities

Entities are named references (people, places, concepts) extracted from drawers. An entity index MUST track:

- Canonical name and slug
- Aliases (alternative names for the same entity)
- References to source drawers
- Last-seen date

When a drawer is written with an `entities` field, the implementation MUST update the entity index.

Entity alias resolution MUST check aliases before direct slug match, so that merged entities always resolve to their canonical target.

### 11.3 Entity Relations

Entities that co-occur in the same drawer have an implicit relationship. Implementations SHOULD support querying co-occurrence pairs with a strength metric (number of shared drawers).

### 11.4 Rollup

The `rollup` operation consolidates drawers from a shorter period into a summary drawer at the next level (day to week, week to month, month to year). Source drawers MUST be preserved; the rollup is an additional higher-level view.

### 11.5 Session Init

At the end of a conversation, the implementation SHOULD write a session init file containing:

- Summary of the conversation
- Active topics
- Last messages (clipped)
- Greeting for the next Wake

The next Wake MUST load the session init if present.

## 12. Interoperability Requirements

- Drawers MUST be stored as plain text files. Any tool that reads text can read a drawer.
- Indexes MUST be structured text files with keyword-searchable content.
- The entity index MUST be a JSON file with a documented schema.
- All protocol files SHOULD live in the repository. No external service is required.
- An implementation MUST NOT require a specific LLM, IDE, or vendor service to execute the Atlas Walk.
- Provider interfaces (Memory, Graph, Index) MUST be pluggable. The protocol defines the contract, not the implementation.

## 13. Security Considerations

- Life mode repositories MUST be private. The implementation SHOULD verify this during initialization.
- API keys, tokens, and credentials MUST NOT be stored in drawers, indexes, or any file managed by the protocol.
- Secret scanning (Section 7.5) is REQUIRED, not optional.
- Session init files SHOULD NOT contain sensitive information; message content MUST be clipped and summarized.

## 14. References

- RFC 2119: Key words for use in RFCs to Indicate Requirement Levels
- [Atlas Reference Implementation](../README.md)
- [Atlas Whitepaper](article.md)
- [Atlas Life Specification](life-spec.md)
