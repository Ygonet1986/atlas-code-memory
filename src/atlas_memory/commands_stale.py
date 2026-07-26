from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

SOURCE_EXTS = {
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".py",
    ".gd",
    ".cs",
    ".rs",
    ".go",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mm",
    ".m",
    ".java",
    ".kt",
    ".swift",
}
SKIP_DIRS = {
    ".git",
    "node_modules",
    "graphify-out",
    "bin",
    "lib",
    "__pycache__",
    ".venv",
    "dist",
    "build",
    ".next",
    "vendor",
}


@dataclass
class StaleReport:
    name: str
    escopo: str
    status: str
    issues: list[str]


def parse_graphify_index(text: str) -> list[dict[str, str]]:
    blocks = re.split(r"\n(?=### )", text)
    out: list[dict[str, str]] = []
    for block in blocks:
        if not block.startswith("### "):
            continue
        name = block.splitlines()[0][4:].strip()
        if name.startswith("<") or "nome-curto" in name or "short-name" in name:
            continue
        escopo = grafo = status = ""
        for line in block.splitlines():
            if "**scope:**" in line or "**escopo:**" in line:
                m = re.search(r"`([^`]+)`", line)
                escopo = m.group(1) if m else ""
            if "**graph:**" in line or "**grafo:**" in line:
                m = re.search(r"`([^`]+)`", line)
                grafo = m.group(1) if m else ""
            if "**status:**" in line:
                status = line.split("**status:**", 1)[-1].strip().split()[0]
        if not escopo or escopo.startswith("<"):
            continue
        out.append({"name": name, "escopo": escopo, "grafo": grafo, "status": status})
    return out


def _graph_json(project: Path, escopo: str, grafo: str) -> Path:
    if grafo:
        p = project / grafo
        if p.name == "graph.json":
            return p
        return p / "graph.json"
    return project / escopo / "graphify-out" / "graph.json"


def _sources_newer_than(scope: Path, graph_mtime: float, cap: int = 4000) -> bool:
    if not scope.exists():
        return False
    count = 0
    for dirpath, dirnames, filenames in os.walk(scope):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix.lower() not in SOURCE_EXTS:
                continue
            p = Path(dirpath) / fn
            try:
                if p.stat().st_mtime > graph_mtime + 1:
                    return True
            except OSError:
                continue
            count += 1
            if count >= cap:
                return False
    return False


def stale_report(project: Path) -> list[StaleReport]:
    project = project.resolve()
    index = project / ".cursor" / "graphify-index.md"
    if not index.exists():
        return []
    entries = parse_graphify_index(index.read_text(encoding="utf-8", errors="replace"))
    reports: list[StaleReport] = []
    for e in entries:
        issues: list[str] = []
        gj = _graph_json(project, e["escopo"], e["grafo"])
        status = e["status"]
        if status == "missing" or not gj.exists():
            issues.append("graph missing")
        elif status == "stale":
            issues.append("marked stale")
        elif gj.exists():
            if _sources_newer_than(project / e["escopo"], gj.stat().st_mtime):
                issues.append("sources newer than graph.json")
        reports.append(StaleReport(e["name"], e["escopo"], status, issues))
    return reports


def mark_stale_touched(project: Path, changed_files: list[str]) -> list[str]:
    """Set status: stale for graphify-index entries whose escopo prefixes a changed file."""
    project = project.resolve()
    index = project / ".cursor" / "graphify-index.md"
    if not index.exists():
        return []
    text = index.read_text(encoding="utf-8")
    entries = parse_graphify_index(text)
    updated = []
    new_text = text
    for e in entries:
        escopo = e["escopo"].rstrip("/") + "/"
        hit = any(
            f.replace("\\", "/").startswith(escopo) or f.replace("\\", "/") == e["escopo"]
            for f in changed_files
        )
        if not hit or e["status"] == "stale":
            continue
        # replace status line inside this named block only — simple global replace of first ready for name is hard;
        # do a careful block rewrite
        pattern = rf"(### {re.escape(e['name'])}\n.*?\n- \*\*status:\*\* )ready"
        new_text2, n = re.subn(pattern, r"\1stale", new_text, count=1, flags=re.S)
        if n:
            new_text = new_text2
            updated.append(e["name"])
    if updated:
        index.write_text(new_text, encoding="utf-8")
    return updated
