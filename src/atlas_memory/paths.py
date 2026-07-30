from __future__ import annotations

import importlib.resources as resources
from pathlib import Path


def package_data_root() -> Path:
    """Return filesystem path to bundled data (templates, cursor, schemas…)."""
    # Editable/dev: prefer repo layout next to package
    here = Path(__file__).resolve().parent
    repo_data_candidates = [
        here.parent.parent / "templates",
        here / "data" / "templates",
    ]
    for c in repo_data_candidates:
        if c.exists():
            # repo root when templates/ lives at repo
            if c.name == "templates":
                return c.parent
            return c.parent  # data/
    # wheel install
    try:
        root = resources.files("atlas_memory") / "data"
        return Path(str(root))
    except Exception:
        return here.parent.parent


def repo_root_from_pkg() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def source_checkout_root() -> Path | None:
    """Repo root when running from a source checkout, None from an installed wheel."""
    root = repo_root_from_pkg()
    return root if (root / "pyproject.toml").exists() and (root / "eval").is_dir() else None


def data_dir(*parts: str) -> Path:
    root = package_data_root()
    # If root is repo (has templates/), use it; if root is data/, use it
    if (root / "templates").exists():
        return root.joinpath(*parts)
    if root.name == "data":
        return root.joinpath(*parts)
    # fallback repo
    return repo_root_from_pkg().joinpath(*parts)
