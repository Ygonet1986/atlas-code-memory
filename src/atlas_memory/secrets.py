from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# High-signal secret patterns (fail closed on match for checkpoints)
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_like", re.compile(r"(?i)aws(.{0,20})?(secret|access).{0,20}['\"][A-Za-z0-9/+=]{30,}")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{16,}")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("openai_sk", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("connection_string", re.compile(r"(?i)(postgres|mysql|mongodb|redis)://[^:\\s]+:[^@\\s]+@")),
]

DENY_FILENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
}


@dataclass
class SecretHit:
    rule: str
    excerpt: str


def scan_text(text: str) -> list[SecretHit]:
    hits: list[SecretHit] = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            excerpt = m.group(0)
            if len(excerpt) > 48:
                excerpt = excerpt[:24] + "…" + excerpt[-8:]
            hits.append(SecretHit(rule=name, excerpt=excerpt))
    return hits


def is_denied_filename(path: str | Path) -> bool:
    name = Path(path).name
    if name in DENY_FILENAMES:
        return True
    if name.startswith(".env"):
        return True
    return False


def load_atlasignore(project: Path) -> list[str]:
    path = project / ".atlasignore"
    if not path.exists():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines
