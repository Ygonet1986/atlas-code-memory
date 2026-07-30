"""Build and audit the project-cache layer directly from the source tree.

The cache is the only mandatory Atlas layer, so it must not depend on an agent
remembering to append entries by hand. `build_cache` walks the repository and
writes one entry per source file, deriving the description from the module
docstring, leading comment or exported symbols.
"""

from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path
from typing import Any

from . import metrics
from .secrets import is_denied_filename, load_atlasignore

CODE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".rs", ".go", ".java", ".kt", ".swift", ".rb", ".php", ".cs",
    ".c", ".cc", ".cpp", ".h", ".hpp", ".m", ".mm", ".gd",
    ".sh", ".ps1",
}
DOC_EXTS = {".md"}
DEFAULT_EXTS = CODE_EXTS | DOC_EXTS

SKIP_DIRS = {
    ".git", ".cursor", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "coverage", "vendor", "graphify-out",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "target", "site-packages",
}

MAX_DESC = 160
DEFAULT_MAX_FILES = 2000

CACHE_HEADER = """# Project Source Cache

Atlas layer 5. File inventory: name → path → description.
Search this file; never read it end-to-end. Partial updates only after each change.

<!-- atlas cache build regenerates missing entries; hand-written ones are kept -->
"""


def cache_path(project: Path) -> Path:
    return project / ".cursor" / "project-cache.md"


def path_ignored(rel: str, patterns: list[str]) -> bool:
    parts = rel.split("/")
    name = parts[-1]
    for raw in patterns:
        pat = raw.rstrip("/")
        if not pat:
            continue
        if raw.endswith("/"):
            # Accept both a bare directory name and a multi-segment prefix.
            if pat in parts[:-1] or rel.startswith(pat + "/"):
                return True
            continue
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(name, pat):
            return True
        if pat.startswith("**/") and fnmatch.fnmatch(name, pat[3:]):
            return True
    return False


def iter_source_files(
    project: Path,
    *,
    exts: set[str] | None = None,
    limit: int = DEFAULT_MAX_FILES,
) -> tuple[list[str], bool]:
    """Return (relative posix paths, truncated) for indexable source files."""
    exts = exts or DEFAULT_EXTS
    patterns = load_atlasignore(project)
    out: list[str] = []
    truncated = False
    for path in sorted(project.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in exts:
            continue
        rel_parts = path.relative_to(project).parts
        # Match only inside the project: a repo living under a directory called
        # "build" or "site-packages" must still be fully indexable.
        if any(part in SKIP_DIRS for part in rel_parts[:-1]):
            continue
        if is_denied_filename(path):
            continue
        rel = "/".join(rel_parts)
        if path_ignored(rel, patterns):
            continue
        out.append(rel)
        if len(out) >= limit:
            truncated = True
            break
    return out, truncated


def _clip(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= MAX_DESC:
        return text
    return text[: MAX_DESC - 1].rstrip() + "…"


def _describe_python(text: str) -> str:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return ""
    doc = ast.get_docstring(tree)
    if doc:
        return _clip(doc.strip().splitlines()[0])
    names = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
    ]
    if names:
        return _clip("Defines " + ", ".join(names[:8]))
    return ""


def _leading_comment(text: str) -> str:
    lines = text.splitlines()
    block = re.match(r"\s*/\*\*?(.*?)\*/", text, re.S)
    if block:
        body = re.sub(r"^\s*\*+", "", block.group(1), flags=re.M).strip()
        if body:
            return _clip(body.splitlines()[0])
    collected: list[str] = []
    for line in lines[:10]:
        stripped = line.strip()
        if stripped.startswith(("//", "#!", "//!")):
            cleaned = stripped.lstrip("/#!").strip()
            if cleaned:
                collected.append(cleaned)
        elif stripped:
            break
    if collected:
        return _clip(" ".join(collected))
    return ""


def _describe_ts(text: str) -> str:
    lead = _leading_comment(text)
    if lead:
        return lead
    names = re.findall(
        r"^export\s+(?:default\s+)?(?:async\s+)?"
        r"(?:function|class|const|let|type|interface|enum)\s+([A-Za-z_$][\w$]*)",
        text,
        re.M,
    )
    if names:
        return _clip("Exports " + ", ".join(list(dict.fromkeys(names))[:8]))
    return ""


def _describe_rust(text: str) -> str:
    doc = [ln.strip()[3:].strip() for ln in text.splitlines()[:20] if ln.strip().startswith("//!")]
    if doc:
        return _clip(" ".join(doc))
    names = re.findall(r"^\s*pub\s+(?:fn|struct|enum|trait|mod)\s+([A-Za-z_]\w*)", text, re.M)
    if names:
        return _clip("Exposes " + ", ".join(list(dict.fromkeys(names))[:8]))
    return ""


def _describe_go(text: str) -> str:
    lead = _leading_comment(text)
    if lead:
        return lead
    names = re.findall(r"^func\s+([A-Z]\w*)", text, re.M)
    if names:
        return _clip("Exposes " + ", ".join(list(dict.fromkeys(names))[:8]))
    return ""


def _describe_markdown(text: str) -> str:
    title = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            if not title:
                title = stripped.lstrip("#").strip()
            continue
        if stripped.startswith(("---", "```", "|", "<!--")):
            continue
        return _clip(stripped)
    return _clip(title) if title else ""


def describe_file(project: Path, rel: str) -> str:
    """Derive a one-line description for a source file."""
    path = project / rel
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    suffix = path.suffix.lower()
    desc = ""
    if suffix == ".py":
        desc = _describe_python(text)
    elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        desc = _describe_ts(text)
    elif suffix == ".rs":
        desc = _describe_rust(text)
    elif suffix == ".go":
        desc = _describe_go(text)
    elif suffix == ".md":
        desc = _describe_markdown(text)
    else:
        desc = _leading_comment(text)
    if desc:
        return desc
    kind = suffix.lstrip(".") or "file"
    return f"{kind} source at {rel}"


ENTRY_RE = re.compile(r"\*\*(?:path|endereço|endereco):\*\*\s*`([^`]+)`", re.IGNORECASE)


def parse_cache(text: str) -> tuple[str, list[dict[str, str]]]:
    """Split the cache into (header, entries). Entries keep their raw block."""
    blocks = re.split(r"\n(?=### )", text)
    header = ""
    entries: list[dict[str, str]] = []
    for i, block in enumerate(blocks):
        if not block.startswith("### "):
            if i == 0:
                header = block.rstrip()
            continue
        name = block.splitlines()[0][4:].strip()
        m = ENTRY_RE.search(block)
        entries.append(
            {
                "name": name,
                "path": m.group(1) if m else "",
                "raw": block.rstrip(),
            }
        )
    return header, entries


def _entry_name(rel: str, taken: set[str]) -> str:
    name = rel.rsplit("/", 1)[-1]
    if name not in taken:
        return name
    parts = rel.split("/")
    if len(parts) >= 2:
        candidate = "/".join(parts[-2:])
        if candidate not in taken:
            return candidate
    return rel


def _render(name: str, rel: str, description: str) -> str:
    return f"### {name}\n- **path:** `{rel}`\n- **description:** {description}"


def build_cache(
    project: Path,
    *,
    force: bool = False,
    prune: bool = False,
    limit: int = DEFAULT_MAX_FILES,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add a cache entry for every source file that lacks one.

    Hand-written descriptions are preserved unless ``force``. ``prune`` drops
    entries whose path no longer exists on disk.
    """
    project = project.resolve()
    path = cache_path(project)
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else CACHE_HEADER
    header, entries = parse_cache(text)
    if not header.strip():
        header = CACHE_HEADER.rstrip()

    sources, truncated = iter_source_files(project, limit=limit)
    indexed = {e["path"] for e in entries if e["path"]}

    pruned: list[str] = []
    if prune:
        kept: list[dict[str, str]] = []
        for entry in entries:
            rel = entry["path"]
            if rel and not (project / rel).exists():
                pruned.append(rel)
                continue
            kept.append(entry)
        entries = kept
        indexed = {e["path"] for e in entries if e["path"]}

    taken = {e["name"] for e in entries}
    added: list[str] = []
    updated: list[str] = []

    by_path = {e["path"]: e for e in entries if e["path"]}
    for rel in sources:
        if rel in by_path:
            if not force:
                continue
            description = describe_file(project, rel)
            entry = by_path[rel]
            entry["raw"] = _render(entry["name"], rel, description)
            updated.append(rel)
            continue
        description = describe_file(project, rel)
        name = _entry_name(rel, taken)
        taken.add(name)
        entry = {"name": name, "path": rel, "raw": _render(name, rel, description)}
        entries.append(entry)
        by_path[rel] = entry
        added.append(rel)

    body = "\n\n".join(e["raw"] for e in entries)
    new_text = header.rstrip() + "\n\n" + body + "\n" if body else header.rstrip() + "\n"

    if not dry_run and (added or updated or pruned):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text, encoding="utf-8")
        metrics.record(project, "cache_build", added=len(added), updated=len(updated))

    covered = len([r for r in sources if r in by_path])
    return {
        "ok": True,
        "path": str(path),
        "sources": len(sources),
        "entries": len(entries),
        "added": added,
        "updated": updated,
        "pruned": pruned,
        "coverage_pct": round(100.0 * covered / len(sources), 1) if sources else 100.0,
        "truncated": truncated,
        "dry_run": dry_run,
    }


def cache_status(project: Path, *, limit: int = DEFAULT_MAX_FILES) -> dict[str, Any]:
    """Coverage report: how many source files have a cache entry."""
    project = project.resolve()
    path = cache_path(project)
    if not path.exists():
        return {
            "ok": False,
            "error": "no project-cache.md — run atlas init",
            "sources": 0,
            "indexed": 0,
            "coverage_pct": 0.0,
            "missing": [],
            "stale": [],
        }
    _, entries = parse_cache(path.read_text(encoding="utf-8", errors="replace"))
    indexed = {e["path"] for e in entries if e["path"]}
    sources, truncated = iter_source_files(project, limit=limit)
    missing = [r for r in sources if r not in indexed]
    stale = [r for r in sorted(indexed) if r and not (project / r).exists()]
    covered = len(sources) - len(missing)
    return {
        "ok": True,
        "path": str(path),
        "sources": len(sources),
        "entries": len(entries),
        "indexed": covered,
        "coverage_pct": round(100.0 * covered / len(sources), 1) if sources else 100.0,
        "missing": missing,
        "stale": stale,
        "truncated": truncated,
    }
