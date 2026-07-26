from __future__ import annotations

import stat
from pathlib import Path

HOOK_SNIPPET = r'''#!/usr/bin/env bash
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
'''


def install_git_hooks(project: Path) -> list[str]:
    project = project.resolve()
    git_hooks = project / ".git" / "hooks"
    actions: list[str] = []
    if not git_hooks.is_dir():
        return ["fail: not a git repository (no .git/hooks)"]

    dest = git_hooks / "post-commit"
    marker = "atlas-memory: mark graphify-index"
    if dest.exists():
        text = dest.read_text(encoding="utf-8", errors="replace")
        if marker in text:
            return [f"keep  {dest} (already wired)"]
        # append
        with dest.open("a", encoding="utf-8") as f:
            f.write("\n\n# --- atlas-memory ---\n")
            f.write("command -v atlas >/dev/null 2>&1 && atlas hooks mark-stale -C \"$(git rev-parse --show-toplevel)\" || true\n")
        actions.append(f"append {dest}")
    else:
        dest.write_text(HOOK_SNIPPET, encoding="utf-8")
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        actions.append(f"create {dest}")

    # also install helper script copy under .cursor/hooks
    local = project / ".cursor" / "hooks"
    local.mkdir(parents=True, exist_ok=True)
    helper = local / "atlas-post-commit.sh"
    helper.write_text(HOOK_SNIPPET, encoding="utf-8")
    helper.chmod(helper.stat().st_mode | stat.S_IEXEC)
    actions.append(f"create {helper}")
    return actions
