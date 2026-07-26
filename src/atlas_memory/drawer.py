from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .secrets import scan_text

DRAWER_TYPES = {"decision", "lesson", "preference", "bugfix", "build"}
DRAWER_STATUS = {"active", "superseded", "archived"}
DEFAULT_ROOMS = ("architecture", "debugging", "conventions", "build", "general")

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
    raw: str = ""

    def to_markdown(self) -> str:
        files = ", ".join(self.files) if self.files else "-"
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
        raw=text,
    )


def validate_drawer(drawer: Drawer) -> list[str]:
    errors: list[str] = []
    if drawer.type not in DRAWER_TYPES:
        errors.append(f"invalid type {drawer.type!r}; expected one of {sorted(DRAWER_TYPES)}")
    if drawer.status not in DRAWER_STATUS:
        errors.append(f"invalid status {drawer.status!r}; expected one of {sorted(DRAWER_STATUS)}")
    if drawer.room and drawer.room not in DEFAULT_ROOMS:
        errors.append(f"unusual room {drawer.room!r}; preferred {DEFAULT_ROOMS}")
    hits = scan_text(drawer.raw or drawer.to_markdown())
    for h in hits:
        errors.append(f"secret-like content matched rule {h.rule}: {h.excerpt}")
    return errors


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
