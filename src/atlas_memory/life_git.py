"""Git helpers for atlas-life (private GitHub clone)."""

from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def is_git_repo(root: Path) -> bool:
    return (root / ".git").exists() or _run(["git", "rev-parse", "--is-inside-work-tree"], root).returncode == 0


def git_status_porcelain(root: Path) -> str:
    return _run(["git", "status", "--porcelain"], root).stdout


def pull_rebase(root: Path) -> dict[str, Any]:
    if not is_git_repo(root):
        return {"ok": False, "error": "not a git repository"}
    proc = _run(["git", "pull", "--rebase", "--autostash"], root)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


def push(root: Path) -> dict[str, Any]:
    if not is_git_repo(root):
        return {"ok": False, "error": "not a git repository"}
    proc = _run(["git", "push"], root)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


def commit_life(root: Path, message: str | None = None, paths: list[str] | None = None) -> dict[str, Any]:
    """Stage life paths and commit. No-op if clean."""
    if not is_git_repo(root):
        return {"ok": False, "error": "not a git repository", "committed": False}

    status = git_status_porcelain(root)
    if not status.strip():
        return {"ok": True, "committed": False, "message": "clean working tree"}

    add_args = ["git", "add", "-A"]
    if paths:
        add_args = ["git", "add", "--"] + paths
    add = _run(add_args, root)
    if add.returncode != 0:
        return {
            "ok": False,
            "committed": False,
            "error": "git add failed",
            "stderr": (add.stderr or "")[-2000:],
        }

    # re-check after add (ignore untracked we didn't want)
    if not git_status_porcelain(root).strip():
        return {"ok": True, "committed": False, "message": "nothing staged"}

    today = date.today().isoformat()
    msg = message or f"life: remember {today}"
    proc = _run(["git", "commit", "-m", msg], root)
    return {
        "ok": proc.returncode == 0,
        "committed": proc.returncode == 0,
        "returncode": proc.returncode,
        "message": msg,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


def sync(root: Path, *, commit_message: str | None = None) -> dict[str, Any]:
    """pull --rebase, commit if dirty, push."""
    pulled = pull_rebase(root)
    committed = {"ok": True, "committed": False}
    if pulled.get("ok"):
        committed = commit_life(root, commit_message)
    pushed = {"ok": False, "skipped": True}
    if pulled.get("ok") and committed.get("ok"):
        # push if we committed or already had local commits ahead
        pushed = push(root)
        pushed["skipped"] = False
    return {
        "ok": bool(pulled.get("ok")) and bool(committed.get("ok")) and (pushed.get("skipped") or pushed.get("ok")),
        "pull": pulled,
        "commit": committed,
        "push": pushed,
        "at": datetime.now(timezone.utc).isoformat(),
    }


def check_repo_private(repo: str) -> dict[str, Any]:
    """Require GitHub repo to be private via `gh`. repo like OWNER/NAME."""
    proc = subprocess.run(
        ["gh", "repo", "view", repo, "--json", "isPrivate,nameWithOwner,url"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": "gh repo view failed",
            "stderr": (proc.stderr or "")[-1000:],
            "private": None,
        }
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid gh JSON", "private": None}
    is_private = bool(data.get("isPrivate"))
    return {
        "ok": is_private,
        "private": is_private,
        "nameWithOwner": data.get("nameWithOwner"),
        "url": data.get("url"),
        "error": None if is_private else "repository must be private",
    }


def ensure_remote_clone(dest: Path, repo: str) -> dict[str, Any]:
    """Clone OWNER/NAME into dest if missing; otherwise pull."""
    dest = dest.resolve()
    if dest.exists() and is_git_repo(dest):
        return {"ok": True, "action": "exists", "path": str(dest), "pull": pull_rebase(dest)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{repo}.git"
    proc = subprocess.run(
        ["gh", "repo", "clone", repo, str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        # fallback git clone
        proc2 = subprocess.run(
            ["git", "clone", url, str(dest)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc2.returncode != 0:
            return {
                "ok": False,
                "action": "clone",
                "error": (proc.stderr or "") + (proc2.stderr or ""),
                "path": str(dest),
            }
    return {"ok": True, "action": "cloned", "path": str(dest)}
