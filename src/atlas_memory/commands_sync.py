from __future__ import annotations

import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def export_bundle(project: Path, dest: Path | None = None) -> Path:
    """Export Atlas indexes + drawers (no secrets scanner rewrite) for team sync."""
    project = project.resolve()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = dest or (project / ".cursor" / "sync" / f"atlas-bundle-{ts}.tar.gz")
    dest.parent.mkdir(parents=True, exist_ok=True)
    cursor = project / ".cursor"
    with tarfile.open(dest, "w:gz") as tar:
        for rel in (
            "mempalace-index.md",
            "graphify-index.md",
            "project-cache.md",
            "atlas-drawers",
            "atlas-import",
            "atlas-onboard-brief.md",
            "rules/atlas.mdc",
            "skills/atlas",
        ):
            p = cursor / rel
            if p.exists():
                tar.add(p, arcname=f"atlas/{rel}")
        meta = {
            "project": str(project),
            "exported_at": ts,
            "format": "atlas-sync-v1",
        }
        meta_path = dest.parent / f"meta-{ts}.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        tar.add(meta_path, arcname="atlas/meta.json")
        meta_path.unlink(missing_ok=True)
    return dest


def import_bundle(project: Path, bundle: Path, *, merge_cache: bool = True) -> list[str]:
    project = project.resolve()
    bundle = bundle.resolve()
    actions: list[str] = []
    tmp = project / ".cursor" / "sync" / "_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(tmp)
    root = tmp / "atlas"
    cursor = project / ".cursor"
    cursor.mkdir(exist_ok=True)

    for name in ("mempalace-index.md", "graphify-index.md", "rules/atlas.mdc"):
        src = root / name
        if src.exists():
            dest = cursor / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            actions.append(f"restore {name}")

    # skills
    skills = root / "skills" / "atlas"
    if skills.exists():
        dest = cursor / "skills" / "atlas"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skills, dest)
        actions.append("restore skills/atlas")

    drawers = root / "atlas-drawers"
    if drawers.exists():
        dest = cursor / "atlas-drawers"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(drawers, dest)
        actions.append("restore atlas-drawers")

    cache_src = root / "project-cache.md"
    cache_dest = cursor / "project-cache.md"
    if cache_src.exists():
        if merge_cache and cache_dest.exists():
            existing = cache_dest.read_text(encoding="utf-8", errors="replace")
            incoming = cache_src.read_text(encoding="utf-8", errors="replace")
            if incoming not in existing:
                cache_dest.write_text(existing.rstrip() + "\n\n<!-- synced -->\n" + incoming, encoding="utf-8")
                actions.append("merge project-cache")
        else:
            shutil.copy2(cache_src, cache_dest)
            actions.append("restore project-cache")

    shutil.rmtree(tmp, ignore_errors=True)
    if not actions:
        actions.append("bundle empty or nothing restored")
    return actions
