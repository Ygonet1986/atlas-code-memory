from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import metrics
from .commands_hooks import install_git_hooks
from .commands_import import import_docs
from .commands_init import init_project


# Legacy Portuguese markdown field labels → English (Atlas canonical).
_FIELD_LABEL_REWRITES: list[tuple[str, str]] = [
    (r"\*\*endereço:\*\*", "**path:**"),
    (r"\*\*endereco:\*\*", "**path:**"),
    (r"\*\*descrição:\*\*", "**description:**"),
    (r"\*\*descricao:\*\*", "**description:**"),
    (r"\*\*escopo:\*\*", "**scope:**"),
    (r"\*\*grafo:\*\*", "**graph:**"),
]

_PLACEHOLDER_REWRITES: list[tuple[str, str]] = [
    ("_Nenhum Graphify registrado ainda._", "_No Graphify scopes registered yet._"),
    ("_Nenhum escopo Graphify registrado ainda._", "_No Graphify scopes registered yet._"),
    ("### <nome-curto>", "### <short-name>"),
    ("`<caminho/relativo>`", "`<relative/path>`"),
]

_INDEX_FILES = (
    "mempalace-index.md",
    "graphify-index.md",
    "project-cache.md",
)


@dataclass
class MigrateOptions:
    dry_run: bool = False
    run_import: bool = True
    global_rule: bool = False
    install_hooks: bool = False
    write_report: bool = True


@dataclass
class MigrateResult:
    actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def extend(self, items: list[str]) -> None:
        self.actions.extend(items)


def _rewrite_labels(text: str) -> tuple[str, int]:
    n = 0
    out = text
    for pat, repl in _FIELD_LABEL_REWRITES:
        out2, c = re.subn(pat, repl, out, flags=re.IGNORECASE)
        out = out2
        n += c
    for old, new in _PLACEHOLDER_REWRITES:
        if old in out:
            out = out.replace(old, new)
            n += 1
    return out, n


def normalize_english_labels(project: Path, *, dry_run: bool = False) -> list[str]:
    """Rewrite Portuguese Atlas field labels to English in index markdown files."""
    actions: list[str] = []
    cursor = project / ".cursor"
    for name in _INDEX_FILES:
        path = cursor / name
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        rewritten, n = _rewrite_labels(original)
        if n and rewritten != original:
            if not dry_run:
                path.write_text(rewritten, encoding="utf-8")
            actions.append(f"{'would normalize' if dry_run else 'normalize'} {name} ({n} label(s))")
    return actions


def _move_legacy_rules(project: Path, *, dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    cursor = project / ".cursor"
    renames = {
        cursor / "agent-memory-stack.mdc": cursor / "rules" / "atlas.mdc",
        cursor / "rules" / "agent-memory-stack.mdc": cursor / "rules" / "atlas.mdc",
        cursor / "rules" / "memoria-agente.mdc": cursor / "rules" / "atlas.mdc",
        cursor / "rules" / "agent-memory.mdc": cursor / "rules" / "atlas.mdc",
    }
    for src, dest in renames.items():
        if src.exists() and not dest.exists():
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
            actions.append(
                f"{'would move' if dry_run else 'moved'} {src.relative_to(project)} -> {dest.relative_to(project)}"
            )
    return actions


def _ensure_agents_section(project: Path, *, dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    agents = project / "AGENTS.md"
    marker = "<!-- atlas-memory -->"
    blurb = (
        f"{marker}\n"
        "## Atlas\n\n"
        "Follow Atlas order: mempalace-index → MemPalace → graphify-index → "
        "Graphify|MindMap → project-cache. Run `atlas doctor`.\n"
        "Migrate or refresh with `atlas migrate` / `atlas onboard`.\n"
    )
    cursor_rules = project / ".cursor" / "rules"
    if agents.exists():
        text = agents.read_text(encoding="utf-8", errors="replace")
        if marker not in text:
            if not dry_run:
                agents.write_text(text.rstrip() + "\n\n" + blurb, encoding="utf-8")
            actions.append(f"{'would append' if dry_run else 'append'} AGENTS.md Atlas section")
    elif cursor_rules.exists():
        if not dry_run:
            agents.write_text(f"# Agent instructions\n\n{blurb}", encoding="utf-8")
        actions.append(f"{'would create' if dry_run else 'create'} AGENTS.md")
    return actions


def _normalize_cache_header(project: Path, *, dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    cache = project / ".cursor" / "project-cache.md"
    if not cache.exists():
        return actions
    t = cache.read_text(encoding="utf-8", errors="replace")
    if not t.lstrip().startswith("#"):
        if not dry_run:
            cache.write_text(
                "# Project Source Cache\n\n"
                "Atlas layer 5. File inventory: name → path → description.\n"
                "Search this file; never read it end-to-end. Partial updates only after each change.\n\n"
                + t,
                encoding="utf-8",
            )
        actions.append(f"{'would normalize' if dry_run else 'normalize'} project-cache header")
    return actions


def _detect_sources(project: Path) -> list[str]:
    """Human-readable hints about what can feed Atlas memory."""
    hints: list[str] = []
    checks = [
        ("README.md", "seed project-cache + context"),
        ("docs/adr", "ADR → decision drawer stubs via import"),
        ("adr", "ADR → decision drawer stubs via import"),
        ("AGENTS.md", "agent instructions (Atlas section)"),
        ("CLAUDE.md", "optional: mirror Atlas blurb manually"),
        (".cursor/rules", "Cursor rules → atlas.mdc via init/migrate"),
        ("mempalace.yaml", "MemPalace already configured"),
    ]
    for rel, note in checks:
        p = project / rel
        if p.exists():
            hints.append(f"{rel} — {note}")
    return hints


def _write_report(project: Path, result: MigrateResult, opts: MigrateOptions) -> None:
    if opts.dry_run or not opts.write_report:
        return
    report = project / ".cursor" / "atlas-migrate-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Atlas migration report",
        "",
        f"Generated: `{ts}`",
        f"Project: `{project}`",
        "",
        "## Actions",
    ]
    if result.actions:
        lines.extend(f"- {a}" for a in result.actions)
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Detected sources")
    sources = _detect_sources(project)
    if sources:
        lines.extend(f"- {s}" for s in sources)
    else:
        lines.append("- (none)")
    if result.warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.extend(f"- {w}" for w in result.warnings)
    lines.extend(
        [
            "",
            "## Next steps",
            "1. Run `atlas doctor`",
            "2. Review `.cursor/atlas-import/*.drawer.md` and file with `atlas checkpoint --write --mine`",
            "3. Register graph scopes: `atlas graph add <name> --scope <dir>`",
            "4. Optional adapters: MemPalace and Graphify **or** Mind Map (never both)",
            "",
            "See the Atlas Memory README **Migration guide** or `docs/migration.md`.",
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")
    result.actions.append(f"create {report.relative_to(project)}")


def migrate_project(
    project: Path,
    *,
    dry_run: bool = False,
    run_import: bool = True,
    global_rule: bool = False,
    install_hooks: bool = False,
    write_report: bool = True,
) -> list[str]:
    """
    Migrate an existing project into the Atlas Memory layout.

    Steps:
    1. Move legacy Cursor memory rules to ``atlas.mdc``
    2. Bootstrap missing indexes / rule / skill (``atlas init``)
    3. Normalize Portuguese field labels to English
    4. Ensure ``AGENTS.md`` Atlas section
    5. Normalize ``project-cache`` header
    6. Optionally seed cache/drawers from README/ADRs (``atlas import``)
    7. Optionally install git hooks / global Cursor rule
    8. Write ``.cursor/atlas-migrate-report.md``
    """
    project = project.resolve()
    opts = MigrateOptions(
        dry_run=dry_run,
        run_import=run_import,
        global_rule=global_rule,
        install_hooks=install_hooks,
        write_report=write_report,
    )
    result = MigrateResult()

    if not dry_run:
        (project / ".cursor").mkdir(exist_ok=True)

    result.extend(_move_legacy_rules(project, dry_run=dry_run))

    if dry_run:
        missing = [
            rel
            for rel in (
                ".cursor/mempalace-index.md",
                ".cursor/graphify-index.md",
                ".cursor/project-cache.md",
                ".cursor/rules/atlas.mdc",
                ".cursor/skills/atlas/SKILL.md",
            )
            if not (project / rel).exists()
        ]
        for rel in missing:
            result.actions.append(f"would create {rel}")
    else:
        result.extend(init_project(project, force=False, global_rule=global_rule))

    result.extend(normalize_english_labels(project, dry_run=dry_run))
    result.extend(_ensure_agents_section(project, dry_run=dry_run))
    result.extend(_normalize_cache_header(project, dry_run=dry_run))

    if run_import:
        if dry_run:
            result.actions.append("would run atlas import (README/ADRs → cache + drawer stubs)")
        else:
            result.extend(import_docs(project))

    if install_hooks and not dry_run:
        try:
            result.extend(install_git_hooks(project))
        except Exception as exc:  # pragma: no cover - defensive
            result.warnings.append(f"hooks install failed: {exc}")

    if not result.actions:
        result.actions.append("nothing to migrate — already on Atlas layout")

    _write_report(project, result, opts)
    metrics.record(project, "migrate", count=len(result.actions), dry_run=dry_run)
    return result.actions
