from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .secrets import scan_text

# Project (coding) drawers
PROJECT_DRAWER_TYPES = {"decision", "lesson", "preference", "bugfix", "build"}
# Life (conversation memory) drawers
LIFE_DRAWER_TYPES = {"memory", "event", "person", "goal", "preference", "lesson", "decision"}
DRAWER_TYPES = PROJECT_DRAWER_TYPES | LIFE_DRAWER_TYPES

DRAWER_STATUS = {"active", "superseded", "archived"}

DEFAULT_ROOMS = ("architecture", "debugging", "conventions", "build", "general")
LIFE_ROOMS = ("day", "week", "month", "year", "people", "general")
ALL_ROOMS = tuple(dict.fromkeys((*DEFAULT_ROOMS, *LIFE_ROOMS)))

LIFE_PERIODS = {"day", "week", "month", "year"}

HEADER_RE = re.compile(
    r"\[type:(?P<type>\w+)\]\s*\[status:(?P<status>\w+)\]",
    re.IGNORECASE,
)


@dataclass
class Drawer:
    type: str
    status: str
    summary: str
    why: str = ""
    branch: str = "-"
    commit: str = "-"
    pr: str = "-"
    files: list[str] = field(default_factory=list)
    supersedes: str = ""
    wing: str = ""
    room: str = ""
    when: str = ""
    period: str = ""
    topics: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    pinned: bool = False
    raw: str = ""

    def to_markdown(self) -> str:
        files = ", ".join(self.files) if self.files else "-"
        topics = ", ".join(self.topics) if self.topics else "-"
        lines = [
            f"[type:{self.type}] [status:{self.status}]",
            f"summary: {self.summary}",
            f"why: {self.why or '-'}",
            f"branch: {self.branch or '-'}",
            f"commit: {self.commit or '-'}",
            f"pr: {self.pr or '-'}",
            f"files: {files}",
        ]
        if self.supersedes:
            lines.append(f"supersedes: {self.supersedes}")
        if self.wing:
            lines.append(f"wing: {self.wing}")
        if self.room:
            lines.append(f"room: {self.room}")
        if self.when:
            lines.append(f"when: {self.when}")
        if self.period:
            lines.append(f"period: {self.period}")
        if self.topics:
            lines.append(f"topics: {topics}")
        if self.entities:
            lines.append(f"entities: {', '.join(self.entities)}")
        if self.pinned:
            lines.append("pinned: true")
        return "\n".join(lines) + "\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "status": self.status,
            "summary": self.summary,
            "why": self.why,
            "git": {"branch": self.branch, "commit": self.commit, "pr": self.pr},
            "files": self.files,
            "supersedes": self.supersedes or None,
            "wing": self.wing or None,
            "room": self.room or None,
            "when": self.when or None,
            "period": self.period or None,
            "topics": self.topics or None,
            "entities": self.entities or None,
            "pinned": self.pinned,
        }


def parse_drawer_markdown(text: str) -> Drawer:
    text = text.strip()
    m = HEADER_RE.search(text)
    if not m:
        raise ValueError("Drawer must start with [type:…] [status:…]")
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line or line.strip().startswith("["):
            continue
        key, _, val = line.partition(":")
        fields[key.strip().lower()] = val.strip()
    summary = fields.get("summary", "").strip()
    if not summary:
        raise ValueError("Drawer requires summary:")
    files_raw = fields.get("files", "-")
    files = [] if files_raw in {"", "-"} else [f.strip() for f in files_raw.split(",") if f.strip()]
    topics_raw = fields.get("topics", "-")
    topics = [] if topics_raw in {"", "-"} else [t.strip() for t in topics_raw.split(",") if t.strip()]
    entities_raw = fields.get("entities", "-")
    entities = [] if entities_raw in {"", "-"} else [e.strip() for e in entities_raw.split(",") if e.strip()]
    pinned_raw = fields.get("pinned", "").lower()
    pinned = pinned_raw in {"true", "yes", "1"}
    return Drawer(
        type=m.group("type").lower(),
        status=m.group("status").lower(),
        summary=summary,
        why=fields.get("why", ""),
        branch=fields.get("branch", "-"),
        commit=fields.get("commit", "-"),
        pr=fields.get("pr", "-"),
        files=files,
        supersedes=fields.get("supersedes", ""),
        wing=fields.get("wing", ""),
        room=fields.get("room", ""),
        when=fields.get("when", ""),
        period=fields.get("period", ""),
        topics=topics,
        entities=entities,
        pinned=pinned,
        raw=text,
    )


def validate_drawer(drawer: Drawer, *, life: bool | None = None) -> list[str]:
    """Validate drawer. If life=True, prefer life rooms/types; if False, project; if None, accept either."""
    errors: list[str] = []
    allowed_types = DRAWER_TYPES
    if life is True:
        allowed_types = LIFE_DRAWER_TYPES
    elif life is False:
        allowed_types = PROJECT_DRAWER_TYPES
    if drawer.type not in allowed_types:
        errors.append(f"invalid type {drawer.type!r}; expected one of {sorted(allowed_types)}")
    if drawer.status not in DRAWER_STATUS:
        errors.append(f"invalid status {drawer.status!r}; expected one of {sorted(DRAWER_STATUS)}")
    if drawer.room:
        if life is True and drawer.room not in LIFE_ROOMS:
            errors.append(f"unusual room {drawer.room!r}; preferred {LIFE_ROOMS}")
        elif life is False and drawer.room not in DEFAULT_ROOMS:
            errors.append(f"unusual room {drawer.room!r}; preferred {DEFAULT_ROOMS}")
        elif life is None and drawer.room not in ALL_ROOMS:
            errors.append(f"unusual room {drawer.room!r}; preferred {ALL_ROOMS}")
    if drawer.period and drawer.period not in LIFE_PERIODS:
        errors.append(f"invalid period {drawer.period!r}; expected one of {sorted(LIFE_PERIODS)}")
    hits = scan_text(drawer.raw or drawer.to_markdown())
    for h in hits:
        errors.append(f"secret-like content matched rule {h.rule}: {h.excerpt}")
    return errors


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
