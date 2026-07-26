#!/usr/bin/env bash
# atlas-memory: mark graphify-index entries stale when scoped files change
set -e
if ! command -v atlas >/dev/null 2>&1; then
  exit 0
fi
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
CHANGED="$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || true)"
if [[ -z "$CHANGED" ]]; then
  exit 0
fi
# Pass changed files to atlas hooks mark-stale
echo "$CHANGED" | atlas hooks mark-stale --stdin -C "$ROOT" || true
