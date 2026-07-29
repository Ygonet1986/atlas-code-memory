from __future__ import annotations

import re
from pathlib import Path

from .commands_stale import parse_graphify_index


INDEX_HEADER = """# Graphify Index

Atlas layer 3. Map of scoped code graphs.
**Not** AI Mind Map. Search this file; never read it end-to-end.
Statuses: `ready` | `missing` | `stale` — use `atlas stale`.

## Scopes

"""


def _index_path(project: Path) -> Path:
    return project / ".cursor" / "graphify-index.md"


def list_graphs(project: Path) -> list[dict[str, str]]:
    path = _index_path(project)
    if not path.exists():
        return []
    return parse_graphify_index(path.read_text(encoding="utf-8", errors="replace"))


def add_graph(project: Path, name: str, scope: str, description: str = "", status: str = "missing") -> str:
    project = project.resolve()
    path = _index_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(INDEX_HEADER, encoding="utf-8")
    entries = list_graphs(project)
    if any(e["name"] == name for e in entries):
        return f"exists {name}"
    scope = scope.strip().rstrip("/")
    graph = f"{scope}/graphify-out/"
    block = "\n".join(
        [
            f"### {name}",
            f"- **scope:** `{scope}`",
            f"- **graph:** `{graph}`",
            f"- **description:** {description or name}",
            f"- **status:** {status}",
            "",
        ]
    )
    text = path.read_text(encoding="utf-8")
    if "_No Graphify scopes registered yet._" in text or "_Nenhum Graphify registrado ainda._" in text:
        text = text.replace("_No Graphify scopes registered yet._", block).replace(
            "_Nenhum Graphify registrado ainda._", block
        )
    else:
        text = text.rstrip() + "\n\n" + block
    path.write_text(text + "\n", encoding="utf-8")
    return f"added {name}"


def set_graph_status(project: Path, name: str, status: str) -> str:
    if status not in {"ready", "missing", "stale"}:
        raise ValueError("status must be ready|missing|stale")
    path = _index_path(project)
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    pattern = rf"(### {re.escape(name)}\n.*?\n- \*\*status:\*\* )\w+"
    new_text, n = re.subn(pattern, rf"\g<1>{status}", text, count=1, flags=re.S)
    if not n:
        raise KeyError(f"graph entry not found: {name}")
    path.write_text(new_text, encoding="utf-8")
    # If ready, ensure graph dir exists hint
    return f"{name} -> {status}"
