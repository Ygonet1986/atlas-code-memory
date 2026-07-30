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


class UnsafeBundleError(ValueError):
    """A bundle member would write outside the extraction directory."""


def _safe_members(tar: tarfile.TarFile, dest: Path) -> list[tarfile.TarInfo]:
    """Reject members that escape ``dest`` or are not plain files/directories.

    A bundle is something a teammate hands you, so it is untrusted input by
    design: absolute paths, ``..`` and links are all ways out of the sandbox.
    """
    dest = dest.resolve()
    safe: list[tarfile.TarInfo] = []
    for member in tar.getmembers():
        name = member.name.replace("\\", "/")
        if name.startswith("/") or Path(name).is_absolute() or ".." in Path(name).parts:
            raise UnsafeBundleError(f"bundle member escapes the target directory: {member.name}")
        if member.issym() or member.islnk():
            raise UnsafeBundleError(f"bundle contains a link, which is not allowed: {member.name}")
        if not (member.isfile() or member.isdir()):
            raise UnsafeBundleError(f"bundle contains a special file: {member.name}")
        resolved = (dest / name).resolve()
        if resolved != dest and dest not in resolved.parents:
            raise UnsafeBundleError(f"bundle member escapes the target directory: {member.name}")
        # Never import setuid/setgid or world-writable bits from a peer.
        member.mode = 0o755 if member.isdir() else 0o644
        safe.append(member)
    return safe


def extract_bundle(bundle: Path, dest: Path) -> None:
    """Extract a team bundle, refusing any member that escapes ``dest``."""
    with tarfile.open(bundle, "r:gz") as tar:
        members = _safe_members(tar, dest)
        # filter="data" also strips links and absolute paths on 3.12+; the
        # explicit check above keeps the guarantee on 3.10 and 3.11.
        try:
            tar.extractall(dest, members=members, filter="data")
        except TypeError:
            tar.extractall(dest, members=members)


def import_bundle(project: Path, bundle: Path, *, merge_cache: bool = True) -> list[str]:
    project = project.resolve()
    bundle = bundle.resolve()
    actions: list[str] = []
    tmp = project / ".cursor" / "sync" / "_extract"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    extract_bundle(bundle, tmp)
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
