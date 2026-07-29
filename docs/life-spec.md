# Atlas Life Specification

**Version:** 1.0
**Status:** Draft
**Date:** 2026-07-29
**Depends on:** Atlas Retrieval Protocol (ARP) v1, Conformance Level 3

## 1. Abstract

Atlas Life extends the Atlas Retrieval Protocol with temporal memory organization, entity tracking, and session continuity for personal conversations. It defines how drawers are organized by time period, how entities (people, places, concepts) are indexed and linked, and how sessions are preserved across conversations.

## 2. Terminology

All terminology from the ARP specification applies. Additional terms:

- **Temporal drawer** — A drawer stored in a time-period directory (day, week, month, year).
- **Rollup** — The operation of consolidating drawers from a shorter period into a summary drawer at a longer period.
- **Entity** — A named person, place, object, or concept tracked across drawers.
- **Entity index** — A JSON file mapping entity slugs to metadata (name, aliases, refs, last seen).
- **Alias** — An alternative name for an entity that resolves to the canonical slug.
- **Co-occurrence** — Two entities appearing in the same drawer, creating an implicit relationship.
- **Session init** — A checkpoint written at the end of a conversation to enable seamless resume.
- **Hot set** — The subset of drawers loaded during Wake, ranked by relevance scoring.

## 3. Temporal Organization

### 3.1 Directory Structure

Drawers MUST be stored in temporal directories:

```
<drawers_root>/day/<YYYY-MM-DD>/
<drawers_root>/week/<YYYY-Wnn>/
<drawers_root>/month/<YYYY-MM>/
<drawers_root>/year/<YYYY>/
<drawers_root>/people/
<drawers_root>/general/
<drawers_root>/entities/<slug>/
```

### 3.2 Period Assignment

Each drawer MUST have a `period` field (`day`, `week`, `month`, or `year`) and a `when` field (ISO 8601 date). The drawer is stored in the directory corresponding to its period and when values.

### 3.3 Drawer Types

Life mode adds the following drawer types to ARP:

`memory`, `event`, `person`, `goal`

These supplement the standard ARP types (`decision`, `lesson`, `preference`, `bugfix`, `build`).

### 3.4 Rooms

Life mode uses the following rooms: `day`, `week`, `month`, `year`, `people`, `general`.

## 4. Rollup

### 4.1 Definition

Rollup consolidates drawers from a shorter period into a summary drawer at the next level:

```
day → week → month → year
```

### 4.2 Rules

- Source drawers MUST be preserved. Rollup creates an additional summary, not a replacement.
- The rollup drawer MUST have `type: memory`, `topics: [rollup, <period>]`, and a `why` field listing the source drawer summaries.
- Rollup MAY be triggered manually or automatically.

## 5. Entities

### 5.1 Entity Index

The entity index is a JSON file with the following schema per entity:

```json
{
  "entities": {
    "<slug>": {
      "name": "canonical name",
      "slug": "url-safe-identifier",
      "aliases": ["alternative name 1", "alternative name 2"],
      "refs": ["relative/path/to/drawer.md"],
      "last_seen": "YYYY-MM-DD"
    }
  }
}
```

### 5.2 Linking

When a drawer is written with an `entities` field, the implementation MUST:

1. For each entity name, resolve aliases before checking direct slug match.
2. If an alias matches an existing entity, link to that entity's slug.
3. If no match, create a new entity entry.
4. Create a reference file in `entities/<slug>/` pointing to the source drawer.
5. Update the entity index with the new reference and `last_seen` date.

### 5.3 Aliases

An entity MAY have multiple aliases. Alias resolution MUST check aliases before direct slug match, so that merged entities always resolve to their canonical target.

Adding an alias: `entity_add_alias(name, alias)` adds `alias` to the entity's aliases list.

### 5.4 Merge

`entity_merge(source, target)` MUST:

1. Move all refs from source to target.
2. Add source's name and aliases as target aliases.
3. Move reference files from `entities/<source_slug>/` to `entities/<target_slug>/`.
4. Remove source from the entity index.

### 5.5 Co-occurrence Relations

Entities that appear in the same drawer have an implicit relationship. The implementation SHOULD support querying co-occurrence pairs with a `strength` metric equal to the number of shared drawers.

### 5.6 Entity Graph

The implementation SHOULD support generating a graph for a single entity showing:

- Central entity node
- Drawer nodes linked to the entity
- Topic nodes extracted from those drawers
- Other entity nodes that co-occur

## 6. Hot Set Scoring

### 6.1 Signals

The Wake hot set SHOULD be ranked by the following signals:

| Signal | Description | Weight guidance |
|--------|-------------|----------------|
| Pinned | Drawer has `pinned: true` | Highest priority |
| Recency | File modification time | Decay over ~7 days |
| Branch affinity | Drawer branch matches current git branch | Moderate boost |
| Access frequency | Number of times recalled via Atlas Walk | Logarithmic scaling |
| Entity activity | Drawer mentions entities seen today | Moderate boost |

### 6.2 Pinned Drawers

A drawer with `pinned: true` MUST always appear in the hot set regardless of other scores.

### 6.3 Access Tracking

When a drawer is returned by `recall`, the implementation SHOULD record an access event in metrics to feed the frequency signal.

## 7. Session Continuity

### 7.1 Session Init

At the end of a conversation, the implementation SHOULD write a session init file containing:

```json
{
  "version": 1,
  "prepared_at": "ISO 8601 datetime",
  "day": "YYYY-MM-DD",
  "week": "YYYY-Wnn",
  "summary": "one-line summary of conversation",
  "topics": ["topic1", "topic2"],
  "greeting": "instruction for next Wake",
  "last_messages": [
    {"role": "user", "content": "clipped message"},
    {"role": "assistant", "content": "clipped message"}
  ]
}
```

### 7.2 Resume

The next Wake MUST load the session init if present. The greeting field SHOULD be used to orient the agent. Messages MUST be clipped (RECOMMENDED: 240 characters max per message, 8 messages max).

## 8. Git Sync

### 8.1 Repository

Life mode drawers SHOULD be stored in a dedicated git repository. The repository MUST be private.

### 8.2 Operations

- **pull**: `git pull --rebase` before reading.
- **commit**: Commit all changes with a descriptive message.
- **push**: Push to remote after commit.
- **sync**: pull + commit + push in sequence.

### 8.3 Auto-commit

The implementation MAY auto-commit and push after each `remember` or `session-end` operation, controlled by a user setting.

## 9. Security

- Life repositories MUST be private. Initialization SHOULD verify this.
- API keys and tokens MUST NOT appear in drawers or the entity index.
- Secret scanning (ARP Section 7.5) applies to all life drawers.
- Session init messages MUST be clipped, never full conversation transcripts.

## 10. References

- [Atlas Retrieval Protocol Specification](protocol.md)
- [Atlas Reference Implementation](../README.md)
- [Atlas Whitepaper](article.md)
