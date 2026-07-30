from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .commands_stale import parse_graphify_index, stale_report
from .drawer import DEFAULT_ROOMS

# Default context budget for route payloads (token economy)
DEFAULT_ROUTE_CHAR_BUDGET = 4000
DEFAULT_WAKE_CHAR_BUDGET = 3000

# Function words carry no routing signal but match almost any entry, which is
# how an unrelated question ends up with confident-looking hits.
STOPWORDS = {
    # English
    "the", "and", "for", "where", "what", "how", "are", "was", "were", "with",
    "from", "that", "this", "these", "those", "does", "did", "can", "could",
    "should", "would", "will", "into", "our", "its", "their", "they", "them",
    "you", "your", "when", "why", "who", "whom", "which", "but", "not", "all",
    "any", "some", "more", "most", "than", "then", "there", "here", "been",
    "being", "have", "has", "had", "about", "after", "before", "between",
    "during", "over", "under", "again", "only", "own", "same", "such", "too",
    "very", "just", "also", "out", "off", "per", "via", "upon", "each", "both",
    # Portuguese
    "que", "como", "onde", "qual", "quais", "para", "por", "com", "sem", "dos",
    "das", "uma", "uns", "umas", "este", "esta", "isso", "aquele", "aquela",
    "nao", "não", "sim", "mas", "tambem", "também", "seu", "sua", "meu",
    "minha", "nos", "nas", "foi", "era", "sao", "são", "tem", "têm", "tinha",
    "quando", "porque", "pelo", "pela", "num", "numa", "aos", "ser",
}

# A token present in most cache entries cannot discriminate between them.
COMMON_TOKEN_DF_RATIO = 0.6
MIN_BLOCKS_FOR_DF_FILTER = 10


def query_tokens(question: str) -> list[str]:
    """Meaningful lowercase tokens from a natural-language question."""
    raw = re.findall(r"[a-z0-9_./]+", question.lower())
    return [t for t in raw if len(t) > 2 and t not in STOPWORDS]


def _discriminating(tokens: list[str], blocks: list[str]) -> list[str]:
    """Drop tokens so common in this index that they rank nothing."""
    n = len(blocks)
    if n < MIN_BLOCKS_FOR_DF_FILTER:
        return tokens
    cutoff = n * COMMON_TOKEN_DF_RATIO
    return [t for t in tokens if sum(1 for b in blocks if t in b) <= cutoff]


def _trim_to_budget(items: list[dict[str, Any]], budget: int, key: str = "summary") -> list[dict[str, Any]]:
    """Keep items in order until approximate char budget is exhausted."""
    out: list[dict[str, Any]] = []
    used = 0
    for item in items:
        blob = str(item.get(key) or "") + str(item.get("path") or "") + str(item.get("name") or "")
        cost = max(len(blob), 40)
        if out and used + cost > budget:
            break
        out.append(item)
        used += cost
    return out


def recall_route(
    project: Path,
    question: str,
    *,
    char_budget: int = DEFAULT_ROUTE_CHAR_BUDGET,
    max_cache_hits: int = 6,
    max_graphs: int = 4,
) -> dict[str, Any]:
    """Suggest Atlas layer order and concrete index hits for a question.

    Returns a compact payload sized for token economy (char_budget).
    """
    project = project.resolve()
    q = question.lower()
    tokens = query_tokens(q)
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
        prefer_room = "general"
        if any(w in q for w in ("decid", "architect", "design", "why")):
            prefer_room = "architecture"
        elif any(w in q for w in ("bug", "fix", "error", "debug")):
            prefer_room = "debugging"
        elif any(w in q for w in ("build", "ci", "compile", "scons", "cmake")):
            prefer_room = "build"
        elif any(w in q for w in ("convention", "style", "prefer")):
            prefer_room = "conventions"
        room = prefer_room if prefer_room in DEFAULT_ROOMS else "general"

        # Match wing by question tokens against wing id + nearby block text
        wing_scores: list[tuple[int, str]] = []
        for m in re.finditer(
            r"###\s+([^\n]+)\n(.*?)(?=\n### |\Z)",
            text,
            re.S,
        ):
            block = (m.group(1) + "\n" + m.group(2)).lower()
            wm = re.search(r"\*\*wing:\*\* `([^`]+)`", block)
            if not wm:
                continue
            wname = wm.group(1)
            if wname.startswith("<") or wname in {"id", "wing_id"}:
                continue
            score = sum(1 for t in tokens if t in block or t in wname.lower())
            wing_scores.append((score, wname))
        if wing_scores:
            wing_scores.sort(key=lambda x: (-x[0], x[1]))
            wing = wing_scores[0][1]
        else:
            wings = [m.group(1) for m in re.finditer(r"\*\*wing:\*\* `([^`]+)`", text)]
            wings = [w for w in wings if not w.startswith("<") and w not in {"id", "wing_id"}]
            wing = wings[0] if wings else None

    graphs = []
    if gfi.exists():
        for e in parse_graphify_index(gfi.read_text(encoding="utf-8", errors="replace")):
            scope = e.get("scope") or e.get("escopo") or ""
            desc = e.get("description") or e.get("descricao") or ""
            blob = f"{e['name']} {scope} {e.get('status', '')} {desc}".lower()
            score = sum(1 for tok in tokens if tok in blob)
            status = (e.get("status") or "").lower()
            # Prefer ready scopes; demote stale/missing for ranking (still report)
            if status == "ready":
                score += 2
            elif status == "stale":
                score -= 1
            elif status == "missing":
                score -= 2
            graphs.append({**e, "score": score})
        graphs.sort(key=lambda x: (-x["score"], x["name"]))

    cache_hits = []
    if cache.exists():
        blocks = [
            b
            for b in re.split(r"\n(?=### )", cache.read_text(encoding="utf-8", errors="replace"))
            if b.startswith("### ")
        ]
        lows = [b.lower() for b in blocks]
        cache_tokens = _discriminating(tokens, lows)
        for block, low in zip(blocks, lows):
            score = sum(1 for tok in cache_tokens if tok in low)
            if score:
                name = block.splitlines()[0][4:].strip()
                addr = ""
                am = re.search(
                    r"\*\*(?:path|endereço|endereco):\*\* `([^`]+)`",
                    block,
                    flags=re.IGNORECASE,
                )
                if am:
                    addr = am.group(1)
                desc = ""
                dm = re.search(r"\*\*(?:description|descrição):\*\*\s*(.+)", block)
                if dm:
                    desc = dm.group(1).strip()[:160]
                cache_hits.append(
                    {
                        "name": name,
                        "path": addr,
                        "endereco": addr,
                        "score": score,
                        "summary": desc or name,
                    }
                )
        cache_hits.sort(key=lambda x: -x["score"])

    # Apply char budget to cache hits (primary context cost)
    budgeted_hits = _trim_to_budget(cache_hits[:max_cache_hits], max(char_budget // 2, 800))
    budgeted_graphs = graphs[:max_graphs]

    return {
        "question": question,
        "route": route,
        "mempalace": {"wing": wing, "room": room, "index": str(mpi) if mpi.exists() else None},
        "graphs": budgeted_graphs,
        "cache_hits": budgeted_hits,
        "char_budget": char_budget,
        "stale": [
            {"name": r.name, "issues": r.issues}
            for r in stale_report(project)
            if r.issues
        ],
        "hint": "Open only cache_hits paths; do not grep the monorepo first.",
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
