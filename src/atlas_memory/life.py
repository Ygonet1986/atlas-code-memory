"""Atlas Life — conversation memory with temporal drawers + GitHub sync."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from . import metrics
from .commands_graph import add_graph
from .commands_init import init_project
from .drawer import (
    LIFE_PERIODS,
    LIFE_ROOMS,
    Drawer,
    parse_drawer_markdown,
    validate_drawer,
)
from .life_git import (
    check_repo_private,
    commit_life,
    ensure_remote_clone,
    pull_rebase,
    push,
    sync,
)
from .paths import data_dir


ENV_LIFE_ROOT = "ATLAS_LIFE_ROOT"


def life_root(explicit: Path | str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get(ENV_LIFE_ROOT)
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / "atlas-life").resolve()


def iso_week_key(d: date | None = None) -> str:
    d = d or date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def period_keys(d: date | None = None) -> dict[str, str]:
    d = d or date.today()
    return {
        "day": d.isoformat(),
        "week": iso_week_key(d),
        "month": d.strftime("%Y-%m"),
        "year": str(d.year),
    }


def drawers_base(root: Path) -> Path:
    return root / ".cursor" / "atlas-drawers"


def period_dir(root: Path, period: str, key: str) -> Path:
    return drawers_base(root) / period / key


def _slug(summary: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", summary.lower()).strip("-")[:50] or "drawer"


def write_life_drawer(root: Path, drawer: Drawer) -> Path:
    period = drawer.period or "day"
    when = drawer.when or date.today().isoformat()
    if period == "day":
        key = when
    elif period == "week":
        key = drawer.when if drawer.when and "W" in drawer.when else iso_week_key()
    elif period == "month":
        key = when[:7] if len(when) >= 7 else date.today().strftime("%Y-%m")
    elif period == "year":
        key = when[:4] if when else str(date.today().year)
    else:
        key = when
    room = drawer.room or period
    if room in ("people", "general"):
        dest_dir = drawers_base(root) / room
    else:
        dest_dir = period_dir(root, period if period in LIFE_PERIODS else "day", key)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_slug(drawer.summary)}.drawer.md"
    # avoid overwrite: append short stamp
    if dest.exists():
        stamp = datetime.now(timezone.utc).strftime("%H%M%S")
        dest = dest_dir / f"{_slug(drawer.summary)}-{stamp}.drawer.md"
    dest.write_text(drawer.to_markdown(), encoding="utf-8")
    return dest


def ensure_day_mindmap_scope(root: Path, day_key: str | None = None) -> None:
    day_key = day_key or date.today().isoformat()
    name = f"day-{day_key}"
    gfi = root / ".cursor" / "graphify-index.md"
    if gfi.exists() and f"### {name}" in gfi.read_text(encoding="utf-8", errors="replace"):
        return
    scope = f"atlas-drawers/day/{day_key}"
    add_graph(
        root,
        name,
        scope,
        description=f"Mind Map scope for conversations on {day_key}.",
        status="missing",
    )


def _read_drawers_in(dir_path: Path, limit: int = 12) -> list[dict[str, Any]]:
    if not dir_path.exists():
        return []
    files = sorted(dir_path.glob("*.drawer.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for f in files[:limit]:
        try:
            d = parse_drawer_markdown(f.read_text(encoding="utf-8"))
            out.append({"path": str(f), "mtime": f.stat().st_mtime, **d.to_dict()})
        except Exception:
            out.append({"path": str(f), "mtime": f.stat().st_mtime, "summary": f.stem, "error": "parse_failed"})
    return out


def _read_all_drawers_in(dir_path: Path) -> list[dict[str, Any]]:
    """Read all drawers without limit (for scoring)."""
    if not dir_path.exists():
        return []
    out: list[dict[str, Any]] = []
    for f in dir_path.glob("*.drawer.md"):
        try:
            d = parse_drawer_markdown(f.read_text(encoding="utf-8"))
            out.append({"path": str(f), "mtime": f.stat().st_mtime, **d.to_dict()})
        except Exception:
            out.append({"path": str(f), "mtime": f.stat().st_mtime, "summary": f.stem, "error": "parse_failed"})
    return out


def _get_current_branch(root: Path) -> str:
    """Try to get the current git branch."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root), capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _get_access_counts(root: Path) -> dict[str, int]:
    """Load drawer access frequency from metrics."""
    mpath = root / ".cursor" / "atlas-metrics.json"
    if not mpath.exists():
        return {}
    try:
        data = json.loads(mpath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    counts: dict[str, int] = {}
    for entry in data.get("log") or []:
        if entry.get("event") == "life_drawer_access":
            p = entry.get("path", "")
            if p:
                counts[p] = counts.get(p, 0) + 1
    return counts


def _get_entity_recency(root: Path) -> dict[str, str]:
    """Map entity slug -> last_seen date from entity index."""
    idx_path = root / ".cursor" / "atlas-entities.json"
    if not idx_path.exists():
        return {}
    try:
        data = json.loads(idx_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, str] = {}
    for slug, info in (data.get("entities") or {}).items():
        ls = info.get("last_seen")
        if ls:
            out[slug] = ls
    return out


def _score_drawer(
    d: dict[str, Any],
    *,
    now_ts: float,
    branch: str,
    access_counts: dict[str, int],
    entity_recency: dict[str, str],
    today: str,
) -> float:
    """Score a drawer for hot set ranking. Higher = more relevant."""
    score = 0.0

    # Pinned drawers get a massive boost
    if d.get("pinned"):
        score += 1000.0

    # Recency: decay over 7 days
    mtime = d.get("mtime", 0.0)
    age_hours = max((now_ts - mtime) / 3600.0, 0.0)
    score += max(10.0 - age_hours / 16.8, 0.0)  # 0 after ~7 days

    # Branch affinity
    git = d.get("git") or {}
    drawer_branch = git.get("branch") or d.get("branch", "-")
    if branch and drawer_branch not in {"-", ""} and drawer_branch == branch:
        score += 5.0

    # Access frequency
    path = d.get("path", "")
    acc = access_counts.get(path, 0)
    if acc > 0:
        import math
        score += min(math.log1p(acc) * 2.0, 8.0)

    # Entity activity: boost if drawer's entities were seen today
    for ent in d.get("entities") or []:
        slug = re.sub(r"[^a-z0-9]+", "-", ent.strip().lower()).strip("-")[:60]
        if entity_recency.get(slug, "") >= today:
            score += 3.0
            break  # one boost is enough

    return score


def _hot_drawers(root: Path, dir_path: Path, limit: int = 12) -> list[dict[str, Any]]:
    """Read all drawers, score them, return top `limit` by relevance."""
    import time
    all_d = _read_all_drawers_in(dir_path)
    if not all_d:
        return []
    now_ts = time.time()
    branch = _get_current_branch(root)
    access_counts = _get_access_counts(root)
    entity_recency = _get_entity_recency(root)
    today = date.today().isoformat()
    for d in all_d:
        d["_score"] = _score_drawer(
            d, now_ts=now_ts, branch=branch,
            access_counts=access_counts, entity_recency=entity_recency,
            today=today,
        )
    all_d.sort(key=lambda x: -x["_score"])
    # Strip internal score before returning
    for d in all_d[:limit]:
        d.pop("_score", None)
    return all_d[:limit]


SESSION_INIT_REL = Path(".cursor") / "atlas-session-init.json"


def session_init_path(root: Path) -> Path:
    return life_root(root) / SESSION_INIT_REL


def prepare_session_init(
    root: Path | None,
    *,
    summary: str = "",
    topics: list[str] | None = None,
    last_messages: list[dict[str, str]] | None = None,
    greeting: str | None = None,
    push_after: bool = False,
) -> dict[str, Any]:
    """Write L0 init for the *next* wake (end of conversation)."""
    root = life_root(root)
    keys = period_keys()
    msgs = last_messages or []
    # keep short snippets only
    clipped: list[dict[str, str]] = []
    for m in msgs[-8:]:
        role = str(m.get("role") or "user")
        content = str(m.get("content") or "").strip().replace("\n", " ")
        if len(content) > 240:
            content = content[:237] + "…"
        if content:
            clipped.append({"role": role, "content": content})
    topic_list = [t for t in (topics or []) if t][:12]
    if not summary and clipped:
        last_user = next((m["content"] for m in reversed(clipped) if m["role"] == "user"), "")
        summary = f"Left off: {last_user}" if last_user else "Conversation checkpoint"
    if not greeting:
        greeting = "Continue from the session init below; do not re-ask settled facts."
    payload = {
        "version": 1,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "day": keys["day"],
        "week": keys["week"],
        "summary": summary or "No summary",
        "topics": topic_list,
        "greeting": greeting,
        "last_messages": clipped,
    }
    path = session_init_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    result: dict[str, Any] = {"ok": True, "path": str(path), "init": payload, "root": str(root)}
    if push_after:
        result["git"] = sync(root, commit_message=f"life: session init {keys['day']}")
    metrics.record(root, "life_session_init")
    return result


def load_session_init(root: Path | None = None) -> dict[str, Any] | None:
    root = life_root(root)
    path = session_init_path(root)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def mindmap_graph(root: Path | None = None, *, period: str = "day") -> dict[str, Any]:
    """Build a simple node/edge graph from life drawers for the Mind Map tab."""
    root = life_root(root)
    keys = period_keys()
    if period not in LIFE_PERIODS and period != "people":
        period = "day"
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    topic_to_ids: dict[str, list[str]] = {}

    # hierarchy spine
    for p, label in (("year", keys["year"]), ("month", keys["month"]), ("week", keys["week"]), ("day", keys["day"])):
        nid = f"period:{p}:{label}"
        nodes.append({"id": nid, "label": f"{p} {label}", "kind": "period", "period": p})
    edges.append({"from": f"period:year:{keys['year']}", "to": f"period:month:{keys['month']}", "rel": "contains"})
    edges.append({"from": f"period:month:{keys['month']}", "to": f"period:week:{keys['week']}", "rel": "contains"})
    edges.append({"from": f"period:week:{keys['week']}", "to": f"period:day:{keys['day']}", "rel": "contains"})

    drawers: list[dict[str, Any]] = []
    if period == "people":
        drawers = _read_drawers_in(drawers_base(root) / "people", limit=40)
        parent = f"period:day:{keys['day']}"
    else:
        drawers = _read_drawers_in(period_dir(root, period, keys[period]), limit=40)
        parent = f"period:{period}:{keys[period]}"

    for i, d in enumerate(drawers):
        nid = f"drawer:{period}:{i}:{_slug(str(d.get('summary') or 'x'))}"
        nodes.append(
            {
                "id": nid,
                "label": str(d.get("summary") or "")[:80],
                "kind": d.get("type") or "memory",
                "period": period,
                "topics": d.get("topics") or [],
            }
        )
        edges.append({"from": parent, "to": nid, "rel": "has"})
        for t in d.get("topics") or []:
            tnorm = str(t).strip().lower()
            if not tnorm:
                continue
            topic_to_ids.setdefault(tnorm, []).append(nid)

    for topic, ids in topic_to_ids.items():
        tid = f"topic:{_slug(topic)}"
        if not any(n["id"] == tid for n in nodes):
            nodes.append({"id": tid, "label": topic, "kind": "topic", "period": period})
        for did in ids:
            edges.append({"from": tid, "to": did, "rel": "about"})

    # Entity nodes linked to drawers
    entity_to_ids: dict[str, list[str]] = {}
    for i, d in enumerate(drawers):
        for ent in d.get("entities") or []:
            enorm = str(ent).strip().lower()
            if enorm:
                nid = f"drawer:{period}:{i}:{_slug(str(d.get('summary') or 'x'))}"
                entity_to_ids.setdefault(enorm, []).append(nid)
    for ent_name, ids in entity_to_ids.items():
        eid = f"entity:{_entity_slug(ent_name)}"
        if not any(n["id"] == eid for n in nodes):
            nodes.append({"id": eid, "label": ent_name, "kind": "entity", "period": period})
        for did in ids:
            edges.append({"from": eid, "to": did, "rel": "about"})

    # scopes from graphify-index
    scopes = []
    gfi = root / ".cursor" / "graphify-index.md"
    if gfi.exists():
        from .commands_stale import parse_graphify_index

        scopes = parse_graphify_index(gfi.read_text(encoding="utf-8", errors="replace"))

    return {
        "ok": True,
        "root": str(root),
        "period": period,
        "keys": keys,
        "nodes": nodes,
        "edges": edges,
        "scopes": scopes[:20],
    }


def wake(
    root: Path | None = None,
    *,
    hot_limit: int = 8,
    char_budget: int = 3000,
) -> dict[str, Any]:
    root = life_root(root)
    keys = period_keys()
    day_drawers = _hot_drawers(root, period_dir(root, "day", keys["day"]), limit=hot_limit)
    week_drawers = _hot_drawers(root, period_dir(root, "week", keys["week"]), limit=3)
    people = _hot_drawers(root, drawers_base(root) / "people", limit=5)
    session = load_session_init(root)

    # Compact prompt under char_budget (token economy)
    prompt_lines = [
        f"# Atlas Life Wake ({keys['day']})",
        f"wing: life-{keys['year']}",
        f"period: day={keys['day']} week={keys['week']} month={keys['month']}",
        "",
    ]
    used = sum(len(x) + 1 for x in prompt_lines)
    if session:
        prompt_lines.append("## Session init (resume here)")
        summary = str(session.get("summary") or "-")[:240]
        prompt_lines.append(f"prepared_at: {session.get('prepared_at', '-')}")
        prompt_lines.append(f"summary: {summary}")
        used += 80 + len(summary)
        if session.get("greeting"):
            prompt_lines.append(f"greeting: {session['greeting']}")
        topics = session.get("topics") or []
        if topics:
            prompt_lines.append("topics: " + ", ".join(str(t) for t in topics[:8]))
        for m in (session.get("last_messages") or [])[-4:]:
            line = f"- ({m.get('role')}) {str(m.get('content') or '')[:160]}"
            if used + len(line) > char_budget * 0.55:
                break
            prompt_lines.append(line)
            used += len(line) + 1
        prompt_lines.append("")
    prompt_lines.append("## Hot day drawers")
    if not day_drawers:
        prompt_lines.append("(none yet)")
    for d in day_drawers:
        line = f"- [{d.get('type', '?')}] {d.get('summary', '')}"
        why = d.get("why") if d.get("why") not in {None, "-", ""} else ""
        extra = f"\n  why: {why}" if why else ""
        if used + len(line) + len(extra) > char_budget:
            prompt_lines.append("- … (budget)")
            break
        prompt_lines.append(line)
        if extra:
            prompt_lines.append(extra.strip("\n"))
        used += len(line) + len(extra) + 1
    if week_drawers and used < char_budget:
        prompt_lines.append("")
        prompt_lines.append("## Week rollup")
        for d in week_drawers:
            line = f"- {d.get('summary', '')}"
            if used + len(line) > char_budget:
                break
            prompt_lines.append(line)
            used += len(line) + 1
    if people and used < char_budget:
        prompt_lines.append("")
        prompt_lines.append("## People")
        for d in people:
            line = f"- {d.get('summary', '')}"
            if used + len(line) > char_budget:
                break
            prompt_lines.append(line)
            used += len(line) + 1
    prompt = "\n".join(prompt_lines) + "\n"
    return {
        "ok": True,
        "root": str(root),
        "keys": keys,
        "wing": f"life-{keys['year']}",
        "day_drawers": day_drawers,
        "week_drawers": week_drawers,
        "people": people,
        "session_init": session,
        "prompt": prompt,
        "char_budget": char_budget,
        "prompt_chars": len(prompt),
    }


def remember(
    root: Path | None,
    text: str | None = None,
    *,
    type: str = "memory",
    summary: str | None = None,
    why: str = "",
    topics: list[str] | None = None,
    entities: list[str] | None = None,
    room: str = "day",
    period: str = "day",
    when: str | None = None,
    push_after: bool = False,
) -> dict[str, Any]:
    root = life_root(root)
    when = when or date.today().isoformat()
    if text:
        drawer = parse_drawer_markdown(text)
        if not drawer.room:
            drawer.room = room
        if not drawer.period:
            drawer.period = period
        if not drawer.when:
            drawer.when = when
        if not drawer.wing:
            drawer.wing = f"life-{when[:4]}"
        if entities and not drawer.entities:
            drawer.entities = entities
    else:
        if not summary:
            return {"ok": False, "errors": ["summary or text required"]}
        drawer = Drawer(
            type=type,
            status="active",
            summary=summary,
            why=why or "-",
            branch="-",
            commit="-",
            pr="-",
            room=room,
            period=period,
            when=when,
            wing=f"life-{when[:4]}",
            topics=topics or [],
            entities=entities or [],
        )
        drawer.raw = drawer.to_markdown()

    errors = validate_drawer(drawer, life=True)
    if errors:
        return {"ok": False, "errors": errors, "drawer": drawer.to_dict()}

    path = write_life_drawer(root, drawer)
    ensure_day_mindmap_scope(root, drawer.when if drawer.period == "day" else date.today().isoformat())
    _append_cache_entry(root, drawer, path)
    linked = _link_drawer_to_entities(root, drawer, path)

    result: dict[str, Any] = {
        "ok": True,
        "path": str(path),
        "drawer": drawer.to_dict(),
        "entities_linked": linked,
        "root": str(root),
    }
    if push_after:
        msg = f"life: remember {drawer.when or date.today().isoformat()} — {drawer.summary[:60]}"
        result["git"] = sync(root, commit_message=msg)
    metrics.record(root, "life_remember", type=drawer.type)
    return result


def _iter_drawer_files(ddir: Path) -> list[Path]:
    if not ddir.exists():
        return []
    if "entities" in ddir.parts and ddir.name == "entities":
        return list(ddir.rglob("*.drawer.md"))
    return list(ddir.glob("*.drawer.md"))


def _recall_search_dirs(root: Path, prefer: str, keys: dict[str, str]) -> list[Path]:
    """Dirs to scan for recall, prefer first then broader fallbacks."""
    base = drawers_base(root)
    dirs: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        key = str(p)
        if key not in seen:
            seen.add(key)
            dirs.append(p)

    if prefer == "people":
        add(base / "people")
    elif prefer in keys:
        add(period_dir(root, prefer, keys[prefer]))
    add(period_dir(root, "day", keys["day"]))
    add(period_dir(root, "week", keys["week"]))
    add(period_dir(root, "month", keys["month"]))
    add(base / "general")
    add(base / "people")
    ent = base / "entities"
    if ent.exists():
        add(ent)
    day_root = base / "day"
    if day_root.exists():
        for ddir in sorted(
            (p for p in day_root.iterdir() if p.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        )[:14]:
            add(ddir)
    return dirs


def _entity_token_boost(root: Path, tokens: list[str], d: dict[str, Any]) -> float:
    """Boost score when question tokens match drawer entities or entity index."""
    boost = 0.0
    ents = [str(e).lower() for e in (d.get("entities") or [])]
    for t in tokens:
        for e in ents:
            if t in e or e in t:
                boost += 4.0
                break
    idx = _load_entity_index(root)
    path = d.get("path", "")
    try:
        rel = Path(path).resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        rel = str(path).replace("\\", "/")
    for slug, info in (idx.get("entities") or {}).items():
        names = [slug, (info.get("name") or "").lower()]
        names.extend(str(a).lower() for a in (info.get("aliases") or []))
        name_hit = any(any(t in n or n in t for n in names if len(n) > 1) for t in tokens)
        if not name_hit:
            continue
        refs = info.get("refs") or []
        if any(rel.endswith(r) or r in rel for r in refs) or any(
            any(t in e for e in ents) for t in tokens
        ):
            boost += 3.0
            break
    return boost


def recall(root: Path | None, question: str, *, limit: int = 10) -> dict[str, Any]:
    root = life_root(root)
    q = question.lower()
    keys = period_keys()
    prefer = "day"
    if any(w in q for w in ("year", "anual", "ano")):
        prefer = "year"
    elif any(w in q for w in ("month", "mês", "mes")):
        prefer = "month"
    elif any(w in q for w in ("week", "semana")):
        prefer = "week"
    elif any(w in q for w in ("people", "pessoa", "who", "quem")):
        prefer = "people"

    tokens = [t for t in re.findall(r"[a-z0-9_]+", q) if len(t) > 2]
    # Avoid matching every drawer via [type:memory] / frontmatter noise
    stop = {
        "memory",
        "event",
        "person",
        "goal",
        "preference",
        "lesson",
        "decision",
        "type",
        "status",
        "active",
        "summary",
        "when",
        "period",
        "room",
        "wing",
        "topics",
        "files",
        "branch",
        "commit",
        "drawer",
        "the",
        "and",
        "for",
    }
    tokens = [t for t in tokens if t not in stop]
    if not tokens:
        return {
            "ok": True,
            "question": question,
            "prefer_period": prefer,
            "keys": keys,
            "wing": f"life-{keys['year']}",
            "hits": [],
            "route": ["mempalace-index", "life drawers", "MindMap (one)", "project-cache"],
        }

    import time

    now_ts = time.time()
    branch = _get_current_branch(root)
    access_counts = _get_access_counts(root)
    entity_recency = _get_entity_recency(root)
    today = date.today().isoformat()

    def _field_blob(d: Any) -> str:
        return " ".join(
            [
                str(getattr(d, "summary", "") or ""),
                str(getattr(d, "why", "") or ""),
                " ".join(getattr(d, "topics", None) or []),
                " ".join(getattr(d, "entities", None) or []),
                str(getattr(d, "wing", "") or ""),
                str(getattr(d, "room", "") or ""),
            ]
        ).lower()

    hits: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for ddir in _recall_search_dirs(root, prefer, keys):
        for f in _iter_drawer_files(ddir):
            sp = str(f.resolve())
            if sp in seen_paths:
                continue
            seen_paths.add(sp)
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                d = parse_drawer_markdown(text)
                blob = _field_blob(d)
                token_score = float(sum(1 for t in tokens if t in blob))
                row = {"path": sp, "mtime": f.stat().st_mtime, **d.to_dict()}
                ent_boost = _entity_token_boost(root, tokens, row)
                if token_score <= 0 and ent_boost <= 0:
                    continue
                hot = _score_drawer(
                    row,
                    now_ts=now_ts,
                    branch=branch,
                    access_counts=access_counts,
                    entity_recency=entity_recency,
                    today=today,
                )
                period_boost = 2.0 if (d.period or d.room) == prefer else 0.0
                score = max(token_score, 0.25) * 10.0 + hot * 0.15 + ent_boost + period_boost
                hits.append({**row, "score": round(score, 3)})
            except Exception:
                continue

    # Entity-index refs when question matches entity names/aliases
    idx = _load_entity_index(root)
    for slug, info in (idx.get("entities") or {}).items():
        names = [slug, (info.get("name") or "").lower()]
        names.extend(str(a).lower() for a in (info.get("aliases") or []))
        if not any(any(t in n or n in t for n in names if len(n) > 1) for t in tokens):
            continue
        for rel in info.get("refs") or []:
            p = root / rel
            if not p.exists() or not str(p).endswith(".drawer.md"):
                continue
            sp = str(p.resolve())
            if sp in seen_paths:
                continue
            seen_paths.add(sp)
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                d = parse_drawer_markdown(text)
                row = {"path": sp, "mtime": p.stat().st_mtime, **d.to_dict()}
                hot = _score_drawer(
                    row,
                    now_ts=now_ts,
                    branch=branch,
                    access_counts=access_counts,
                    entity_recency=entity_recency,
                    today=today,
                )
                hits.append({**row, "score": round(15.0 + hot * 0.15, 3)})
            except Exception:
                continue

    hits.sort(key=lambda x: (-x.get("score", 0), x.get("summary", "")))
    for h in hits[:limit]:
        metrics.record(root, "life_drawer_access", path=h.get("path", ""))
        h.pop("mtime", None)
    return {
        "ok": True,
        "question": question,
        "prefer_period": prefer,
        "keys": keys,
        "wing": f"life-{keys['year']}",
        "hits": hits[:limit],
        "route": ["mempalace-index", "life drawers", "MindMap (one)", "project-cache"],
    }


def rollup(
    root: Path | None,
    period: str,
    *,
    when: str | None = None,
    push_after: bool = False,
) -> dict[str, Any]:
    root = life_root(root)
    if period not in LIFE_PERIODS:
        return {"ok": False, "errors": [f"invalid period {period}"]}
    keys = period_keys()
    key = when or keys[period]

    # Source drawers for rollup
    if period == "week":
        # all days in that ISO week folder siblings — scan day dirs matching week
        source: list[dict[str, Any]] = []
        day_root = drawers_base(root) / "day"
        if day_root.exists():
            for ddir in sorted(day_root.iterdir()):
                if not ddir.is_dir():
                    continue
                try:
                    d = date.fromisoformat(ddir.name)
                except ValueError:
                    continue
                if iso_week_key(d) == key:
                    source.extend(_read_drawers_in(ddir, limit=50))
    elif period == "month":
        source = []
        day_root = drawers_base(root) / "day"
        if day_root.exists():
            for ddir in sorted(day_root.iterdir()):
                if ddir.is_dir() and ddir.name.startswith(key):
                    source.extend(_read_drawers_in(ddir, limit=50))
    elif period == "year":
        source = []
        day_root = drawers_base(root) / "day"
        if day_root.exists():
            for ddir in sorted(day_root.iterdir()):
                if ddir.is_dir() and ddir.name.startswith(key):
                    source.extend(_read_drawers_in(ddir, limit=30))
    else:  # day
        source = _read_drawers_in(period_dir(root, "day", key), limit=50)

    bullets = [f"- [{s.get('type')}] {s.get('summary')}" for s in source[:40]]
    summary = f"Rollup {period} {key}: {len(source)} memories"
    why = "\n".join(bullets) if bullets else "No source drawers"
    drawer = Drawer(
        type="memory",
        status="active",
        summary=summary,
        why=why[:2000],
        branch="-",
        commit="-",
        pr="-",
        room=period,
        period=period,
        when=key,
        wing=f"life-{keys['year']}",
        topics=["rollup", period],
    )
    drawer.raw = drawer.to_markdown()
    errors = validate_drawer(drawer, life=True)
    if errors:
        return {"ok": False, "errors": errors}
    path = write_life_drawer(root, drawer)
    result: dict[str, Any] = {
        "ok": True,
        "path": str(path),
        "count": len(source),
        "drawer": drawer.to_dict(),
    }
    if push_after:
        result["git"] = sync(root, commit_message=f"life: rollup {period} {key}")
    metrics.record(root, "life_rollup", period=period)
    return result


# ---------------------------------------------------------------------------
# Entities — each person/object/concept gets its own index within atlas-life
# ---------------------------------------------------------------------------

ENTITIES_INDEX = Path(".cursor") / "atlas-entities.json"


def _entity_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")[:60] or "entity"


def entities_dir(root: Path) -> Path:
    return drawers_base(root) / "entities"


def entity_dir(root: Path, name: str) -> Path:
    return entities_dir(root) / _entity_slug(name)


def _load_entity_index(root: Path) -> dict[str, Any]:
    path = root / ENTITIES_INDEX
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"entities": {}}


def _save_entity_index(root: Path, index: dict[str, Any]) -> None:
    path = root / ENTITIES_INDEX
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve_entity_slug(idx: dict[str, Any], name: str) -> str | None:
    """Find existing entity by name or alias. Returns slug or None.
    Alias matches take priority over direct slug matches so that
    merged/aliased entities resolve to their canonical target."""
    slug = _entity_slug(name)
    ents = idx.get("entities") or {}
    name_lower = name.strip().lower()
    # Check aliases first — an alias match means this name belongs to another entity
    for s, info in ents.items():
        aliases = info.get("aliases") or []
        if any(_entity_slug(a) == slug or a.strip().lower() == name_lower for a in aliases):
            return s
    if slug in ents:
        return slug
    return None


def _link_drawer_to_entities(root: Path, drawer: Drawer, drawer_path: Path) -> list[str]:
    """Create a reference file in entities/<slug>/ pointing to the original drawer."""
    linked: list[str] = []
    idx = _load_entity_index(root)
    for ent_name in drawer.entities:
        resolved = _resolve_entity_slug(idx, ent_name)
        slug = resolved or _entity_slug(ent_name)
        if not slug:
            continue
        edir = entities_dir(root) / slug
        edir.mkdir(parents=True, exist_ok=True)
        try:
            rel = drawer_path.relative_to(root).as_posix()
        except ValueError:
            rel = str(drawer_path)
        ref_name = drawer_path.stem + ".ref.md"
        ref_path = edir / ref_name
        ref_content = (
            f"# Entity ref: {ent_name}\n"
            f"source: {rel}\n"
            f"type: {drawer.type}\n"
            f"summary: {drawer.summary}\n"
            f"when: {drawer.when or '-'}\n"
            f"topics: {', '.join(drawer.topics) if drawer.topics else '-'}\n"
        )
        ref_path.write_text(ref_content, encoding="utf-8")
        ents = idx.setdefault("entities", {})
        entry = ents.setdefault(slug, {"name": ent_name, "slug": slug, "refs": [], "aliases": []})
        if "aliases" not in entry:
            entry["aliases"] = []
        if rel not in entry["refs"]:
            entry["refs"].append(rel)
        entry["last_seen"] = drawer.when or date.today().isoformat()
        linked.append(slug)
    _save_entity_index(root, idx)
    return linked


def entity_merge(root: Path | None, source: str, target: str) -> dict[str, Any]:
    """Merge source entity into target: move refs, add source as alias, delete source."""
    root = life_root(root)
    idx = _load_entity_index(root)
    ents = idx.get("entities") or {}
    # Use direct slug first, then alias resolution
    src_slug = _entity_slug(source)
    if src_slug not in ents:
        src_slug = _resolve_entity_slug(idx, source) or src_slug
    tgt_slug = _resolve_entity_slug(idx, target) or _entity_slug(target)
    ents = idx.get("entities") or {}
    if src_slug not in ents:
        return {"ok": False, "error": f"source entity {source!r} not found"}
    if tgt_slug not in ents:
        return {"ok": False, "error": f"target entity {target!r} not found"}
    if src_slug == tgt_slug:
        return {"ok": False, "error": "source and target are the same entity"}
    src_entry = ents[src_slug]
    tgt_entry = ents[tgt_slug]
    # Move refs
    tgt_refs = tgt_entry.setdefault("refs", [])
    for ref in src_entry.get("refs") or []:
        if ref not in tgt_refs:
            tgt_refs.append(ref)
    # Add source name + aliases as target aliases
    tgt_aliases = tgt_entry.setdefault("aliases", [])
    src_name = src_entry.get("name") or source
    if src_name not in tgt_aliases:
        tgt_aliases.append(src_name)
    for a in src_entry.get("aliases") or []:
        if a not in tgt_aliases:
            tgt_aliases.append(a)
    # Move ref files from source entity dir to target
    src_dir = entities_dir(root) / src_slug
    tgt_dir = entities_dir(root) / tgt_slug
    tgt_dir.mkdir(parents=True, exist_ok=True)
    if src_dir.exists():
        for f in src_dir.iterdir():
            dest = tgt_dir / f.name
            if not dest.exists():
                f.rename(dest)
            else:
                f.unlink()
        src_dir.rmdir()
    # Remove source from index
    del ents[src_slug]
    _save_entity_index(root, idx)
    return {
        "ok": True,
        "merged": src_slug,
        "into": tgt_slug,
        "target_refs": len(tgt_refs),
        "target_aliases": tgt_aliases,
    }


def entity_add_alias(root: Path | None, name: str, alias: str) -> dict[str, Any]:
    """Add an alias to an existing entity."""
    root = life_root(root)
    idx = _load_entity_index(root)
    slug = _resolve_entity_slug(idx, name)
    if not slug:
        slug = _entity_slug(name)
    ents = idx.get("entities") or {}
    if slug not in ents:
        return {"ok": False, "error": f"entity {name!r} not found"}
    entry = ents[slug]
    aliases = entry.setdefault("aliases", [])
    if alias not in aliases:
        aliases.append(alias)
    _save_entity_index(root, idx)
    return {"ok": True, "slug": slug, "name": entry.get("name"), "aliases": aliases}


def entity_list(root: Path | None = None) -> dict[str, Any]:
    """List all known entities with ref count."""
    root = life_root(root)
    idx = _load_entity_index(root)
    ents = idx.get("entities") or {}
    items = []
    for slug, info in sorted(ents.items(), key=lambda kv: kv[0]):
        items.append({
            "slug": slug,
            "name": info.get("name") or slug,
            "aliases": info.get("aliases") or [],
            "refs": len(info.get("refs") or []),
            "last_seen": info.get("last_seen"),
        })
    return {"ok": True, "root": str(root), "count": len(items), "entities": items}


def entity_detail(root: Path | None = None, name: str = "") -> dict[str, Any]:
    """Get all drawers linked to an entity."""
    root = life_root(root)
    idx = _load_entity_index(root)
    slug = _resolve_entity_slug(idx, name) or _entity_slug(name)
    info = (idx.get("entities") or {}).get(slug)
    if not info:
        return {"ok": False, "error": f"entity {name!r} not found", "slug": slug}
    refs = info.get("refs") or []
    drawers: list[dict[str, Any]] = []
    for rel in refs:
        p = root / rel
        if not p.exists():
            drawers.append({"path": rel, "error": "file missing"})
            continue
        try:
            d = parse_drawer_markdown(p.read_text(encoding="utf-8"))
            drawers.append({"path": rel, **d.to_dict()})
        except Exception:
            drawers.append({"path": rel, "error": "parse_failed"})
    # Also read .ref.md files in entity dir for summary
    edir = entities_dir(root) / slug
    ref_files = sorted(edir.glob("*.ref.md")) if edir.exists() else []
    return {
        "ok": True,
        "slug": slug,
        "name": info.get("name") or name,
        "aliases": info.get("aliases") or [],
        "last_seen": info.get("last_seen"),
        "drawers": drawers,
        "ref_count": len(ref_files),
        "root": str(root),
    }


def entity_graph(root: Path | None = None, name: str = "") -> dict[str, Any]:
    """Build a Mind Map graph for a single entity."""
    root = life_root(root)
    detail = entity_detail(root, name)
    if not detail.get("ok"):
        return detail
    slug = detail.get("slug") or _entity_slug(name)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    # Central entity node
    eid = f"entity:{slug}"
    nodes.append({"id": eid, "label": detail.get("name") or name, "kind": "entity"})
    topic_set: dict[str, str] = {}
    for i, d in enumerate(detail.get("drawers") or []):
        nid = f"drawer:{slug}:{i}:{_slug(str(d.get('summary') or 'x'))}"
        nodes.append({
            "id": nid,
            "label": str(d.get("summary") or "")[:80],
            "kind": d.get("type") or "memory",
            "when": d.get("when"),
        })
        edges.append({"from": eid, "to": nid, "rel": "about"})
        for t in d.get("topics") or []:
            tnorm = str(t).strip().lower()
            if tnorm:
                tid = f"topic:{_slug(tnorm)}"
                if tnorm not in topic_set:
                    topic_set[tnorm] = tid
                    nodes.append({"id": tid, "label": tnorm, "kind": "topic"})
                edges.append({"from": topic_set[tnorm], "to": nid, "rel": "tagged"})
        for ent in d.get("entities") or []:
            other = _entity_slug(ent)
            if other != slug:
                oid = f"entity:{other}"
                if not any(n["id"] == oid for n in nodes):
                    nodes.append({"id": oid, "label": ent, "kind": "entity"})
                edges.append({"from": eid, "to": oid, "rel": "related"})
    return {
        "ok": True,
        "slug": slug,
        "name": detail.get("name") or name,
        "nodes": nodes,
        "edges": edges,
        "root": str(root),
    }


def pin_drawer(drawer_path: str | Path) -> dict[str, Any]:
    """Set pinned: true on a drawer file."""
    p = Path(drawer_path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {p}"}
    text = p.read_text(encoding="utf-8")
    d = parse_drawer_markdown(text)
    if d.pinned:
        return {"ok": True, "path": str(p), "already": True}
    d.pinned = True
    d.raw = d.to_markdown()
    p.write_text(d.raw, encoding="utf-8")
    return {"ok": True, "path": str(p)}


def unpin_drawer(drawer_path: str | Path) -> dict[str, Any]:
    """Remove pinned from a drawer file."""
    p = Path(drawer_path)
    if not p.exists():
        return {"ok": False, "error": f"not found: {p}"}
    text = p.read_text(encoding="utf-8")
    d = parse_drawer_markdown(text)
    if not d.pinned:
        return {"ok": True, "path": str(p), "already": True}
    d.pinned = False
    d.raw = d.to_markdown()
    p.write_text(d.raw, encoding="utf-8")
    return {"ok": True, "path": str(p)}


def entity_relations(root: Path | None = None) -> dict[str, Any]:
    """Build co-occurrence graph: entities that appear in the same drawer are related."""
    root = life_root(root)
    idx = _load_entity_index(root)
    ents = idx.get("entities") or {}
    # Map ref path -> set of entity slugs
    ref_to_entities: dict[str, set[str]] = {}
    for slug, info in ents.items():
        for ref in info.get("refs") or []:
            ref_to_entities.setdefault(ref, set()).add(slug)
    # Count co-occurrences
    pairs: dict[tuple[str, str], int] = {}
    for ref, slugs in ref_to_entities.items():
        slug_list = sorted(slugs)
        for i, a in enumerate(slug_list):
            for b in slug_list[i + 1:]:
                key = (a, b)
                pairs[key] = pairs.get(key, 0) + 1
    relations = []
    for (a, b), strength in sorted(pairs.items(), key=lambda x: -x[1]):
        relations.append({
            "source": a,
            "source_name": ents.get(a, {}).get("name", a),
            "target": b,
            "target_name": ents.get(b, {}).get("name", b),
            "strength": strength,
        })
    return {"ok": True, "root": str(root), "relations": relations, "count": len(relations)}


def _append_cache_entry(root: Path, drawer: Drawer, path: Path) -> None:
    cache = root / ".cursor" / "project-cache.md"
    if not cache.exists():
        return
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    name = path.stem
    block = (
        f"\n### {name}\n"
        f"- **path:** `{rel}`\n"
        f"- **description:** Life {drawer.type}: {drawer.summary}\n"
    )
    body = cache.read_text(encoding="utf-8", errors="replace")
    if rel in body:
        return
    cache.write_text(body.rstrip() + "\n" + block, encoding="utf-8")


def _seed_life_indexes(root: Path) -> list[str]:
    actions: list[str] = []
    keys = period_keys()
    year = keys["year"]
    wing = f"life-{year}"

    mpi = root / ".cursor" / "mempalace-index.md"
    header = """# MemPalace Index

Atlas layer 1. Map of wings/rooms for this life palace.
Search this file; never read it end-to-end.

## How to use

1. Find the wing/room (temporal or people).
2. Recall/write drawers scoped to that period.
3. Mind Map is the only GraphBackend for life.

## Wings / rooms

"""
    rooms_seed = []
    for room in LIFE_ROOMS:
        label = f"{wing}-{room}" if room != "general" else wing
        rooms_seed.append(f"### {label}")
        rooms_seed.append(f"- **wing:** `{wing}`")
        rooms_seed.append(f"- **room:** `{room}`")
        rooms_seed.append(f"- **workspace:** `{root}`")
        rooms_seed.append(f"- **description:** Life room `{room}` for conversation memory.")
        rooms_seed.append("- **status:** active")
        rooms_seed.append("")
    mpi.write_text(header + "\n".join(rooms_seed), encoding="utf-8")
    actions.append("seed mempalace-index (life)")

    gfi = root / ".cursor" / "graphify-index.md"
    gfi.write_text(
        """# Graphify Index (Mind Map scopes)

Atlas layer 3 for life. **Mind Map only** — do not use Graphify here.
Statuses: `ready` | `missing` | `stale`.

## Scopes

""",
        encoding="utf-8",
    )
    actions.append("seed graphify-index (mindmap)")
    ensure_day_mindmap_scope(root, keys["day"])

    for period in LIFE_PERIODS:
        period_dir(root, period, keys[period]).mkdir(parents=True, exist_ok=True)
    (drawers_base(root) / "people").mkdir(parents=True, exist_ok=True)
    (drawers_base(root) / "general").mkdir(parents=True, exist_ok=True)
    entities_dir(root).mkdir(parents=True, exist_ok=True)
    (root / "mindmaps").mkdir(exist_ok=True)

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            ".env\n.env.*\n*.pem\n*.key\n.DS_Store\n"
            ".cursor/atlas-metrics.json\n**/mempalace.db\n"
            "apps/**/node_modules/\n",
            encoding="utf-8",
        )
        actions.append("create .gitignore")

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Atlas Life\n\n"
            "Private personal memory palace (day / week / month / year).\n\n"
            "Do **not** make this repository public. Never commit API keys.\n",
            encoding="utf-8",
        )
        actions.append("create README.md")

    # life-oriented skill overlay note in rules
    rule = root / ".cursor" / "rules" / "atlas.mdc"
    if rule.exists():
        extra = (
            "\n\n## Life mode\n\n"
            "This root is an Atlas **life** palace. Use rooms "
            "`day|week|month|year|people|general`. "
            "GraphBackend: Mind Map only. Wake = today + hot set. "
            "Persist with `atlas life remember` and sync to GitHub private.\n"
        )
        body = rule.read_text(encoding="utf-8", errors="replace")
        if "Life mode" not in body:
            rule.write_text(body.rstrip() + extra, encoding="utf-8")
            actions.append("annotate atlas.mdc life mode")

    return actions


def life_init(
    dest: Path | None = None,
    *,
    repo: str | None = None,
    private_check: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Create or clone atlas-life and seed indexes."""
    actions: list[str] = []
    root = life_root(dest)

    if repo:
        if private_check:
            priv = check_repo_private(repo)
            if not priv.get("ok"):
                return {"ok": False, "error": priv.get("error") or "repo not private", "private_check": priv}
        clone = ensure_remote_clone(root, repo)
        actions.append(f"clone/ensure {repo} -> {root}")
        if not clone.get("ok"):
            return {"ok": False, "error": clone.get("error"), "clone": clone}
    else:
        root.mkdir(parents=True, exist_ok=True)
        actions.append(f"mkdir {root}")

    init_actions = init_project(root, force=force, global_rule=False)
    actions.extend(init_actions)
    actions.extend(_seed_life_indexes(root))

    # copy life skill snippet if present
    life_skill = data_dir("templates", "life-SKILL.snippet.md")
    skill_dest = root / ".cursor" / "skills" / "atlas" / "SKILL.md"
    if life_skill.exists() and skill_dest.exists():
        snippet = life_skill.read_text(encoding="utf-8")
        body = skill_dest.read_text(encoding="utf-8", errors="replace")
        if "atlas life" not in body.lower():
            skill_dest.write_text(body.rstrip() + "\n\n" + snippet, encoding="utf-8")
            actions.append("append life skill")

    cfg = root / ".cursor" / "atlas-life.json"
    cfg.write_text(
        json.dumps(
            {
                "mode": "life",
                "repo": repo,
                "graph_backend": "mindmap",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    actions.append("write atlas-life.json")
    metrics.record(root, "life_init")
    return {"ok": True, "root": str(root), "repo": repo, "actions": actions}


def life_pull(root: Path | None = None) -> dict[str, Any]:
    root = life_root(root)
    return {"root": str(root), **pull_rebase(root)}


def life_push(root: Path | None = None, message: str | None = None) -> dict[str, Any]:
    root = life_root(root)
    committed = commit_life(root, message)
    pushed = push(root) if committed.get("ok") else {"ok": False, "skipped": True}
    return {"root": str(root), "commit": committed, "push": pushed, "ok": committed.get("ok") and pushed.get("ok")}


def life_sync(root: Path | None = None, message: str | None = None) -> dict[str, Any]:
    root = life_root(root)
    return {"root": str(root), **sync(root, commit_message=message)}
