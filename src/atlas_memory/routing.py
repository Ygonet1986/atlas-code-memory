from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .commands_stale import parse_graphify_index, stale_report
from .drawer import DEFAULT_ROOMS


def recall_route(project: Path, question: str) -> dict[str, Any]:
    """Suggest Atlas layer order and concrete index hits for a question."""
    project = project.resolve()
    q = question.lower()
    mpi = project / ".cursor" / "mempalace-index.md"
    gfi = project / ".cursor" / "graphify-index.md"
    cache = project / ".cursor" / "project-cache.md"

    route = [
        "mempalace-index",
        "MemPalace (if installed)",
        "graphify-index",
        "Graphify|MindMap (one)",
        "project-cache",
    ]

    wing = room = None
    if mpi.exists():
        text = mpi.read_text(encoding="utf-8", errors="replace")
        # Prefer architecture for decision-like questions
        prefer_room = "general"
        if any(w in q for w in ("decid", "architect", "design", "why")):
            prefer_room = "architecture"
        elif any(w in q for w in ("bug", "fix", "error", "debug")):
            prefer_room = "debugging"
        elif any(w in q for w in ("build", "ci", "compile", "scons", "cmake")):
            prefer_room = "build"
        elif any(w in q for w in ("convention", "style", "prefer")):
            prefer_room = "conventions"
        m = re.search(rf"\*\*room:\*\* `{prefer_room}`.*?^\- \*\*wing:\*\* `([^`]+)`", text, re.M | re.S)
        # simpler: first wing in file
        wings = [m.group(1) for m in re.finditer(r"\*\*wing:\*\* `([^`]+)`", text)]
        wings = [w for w in wings if not w.startswith("<") and w not in {"id", "wing_id"}]
        wing = wings[0] if wings else None
        room = prefer_room if prefer_room in DEFAULT_ROOMS else "general"

    graphs = []
    if gfi.exists():
        for e in parse_graphify_index(gfi.read_text(encoding="utf-8", errors="replace")):
            blob = f"{e['name']} {e['escopo']} {e.get('status','')}".lower()
            score = sum(1 for tok in re.findall(r"[a-z0-9_]+", q) if tok in blob and len(tok) > 2)
            graphs.append({**e, "score": score})
        graphs.sort(key=lambda x: (-x["score"], x["name"]))

    cache_hits = []
    if cache.exists():
        blocks = re.split(r"\n(?=### )", cache.read_text(encoding="utf-8", errors="replace"))
        for block in blocks:
            if not block.startswith("### "):
                continue
            low = block.lower()
            score = sum(1 for tok in re.findall(r"[a-z0-9_./]+", q) if tok in low and len(tok) > 2)
            if score:
                name = block.splitlines()[0][4:].strip()
                addr = ""
                am = re.search(r"\*\*(?:path|endereço):\*\* `([^`]+)`", block)
                if am:
                    addr = am.group(1)
                cache_hits.append({"name": name, "path": addr, "endereco": addr, "score": score})
        cache_hits.sort(key=lambda x: -x["score"])

    return {
        "question": question,
        "route": route,
        "mempalace": {"wing": wing, "room": room, "index": str(mpi) if mpi.exists() else None},
        "graphs": graphs[:5],
        "cache_hits": cache_hits[:8],
        "stale": [
            {"name": r.name, "issues": r.issues}
            for r in stale_report(project)
            if r.issues
        ],
    }


def protocol_score(transcript: str) -> dict[str, Any]:
    """
    Score whether an agent transcript appears to follow Atlas order.
    Heuristic (no LLM required): look for index/tool mentions in order.
    """
    text = transcript.lower()
    checks = [
        ("mempalace_index", r"mempalace-index|mempalace_index"),
        ("mempalace", r"mempalace|palace|drawer"),
        ("graphify_index", r"graphify-index|graphify_index"),
        ("graph_query", r"graphify\s+(query|path|explain)|mindmap_"),
        ("project_cache", r"project-cache|project_cache"),
    ]
    found = []
    for name, pat in checks:
        m = re.search(pat, text)
        if m:
            found.append((name, m.start()))
    ordered = [n for n, _ in sorted(found, key=lambda x: x[1])]
    expected_prefix = ["mempalace_index", "graphify_index", "project_cache"]
    # soft score: earlier atlas signals before raw grep
    grep_pos = re.search(r"\b(grep|rg |glob\b)", text)
    first_atlas = found[0][1] if found else None
    grep_before_atlas = bool(grep_pos and (first_atlas is None or grep_pos.start() < first_atlas))

    score = 0
    if "mempalace_index" in ordered or "mempalace" in ordered:
        score += 25
    if "graphify_index" in ordered or "graph_query" in ordered:
        score += 25
    if "project_cache" in ordered:
        score += 25
    if not grep_before_atlas:
        score += 25

    return {
        "score": score,
        "ordered_signals": ordered,
        "grep_before_atlas": grep_before_atlas,
        "pass": score >= 50,
        "notes": "Heuristic protocol score (0-100). Pass >= 50.",
    }
