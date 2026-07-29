"""A/B token-proxy bench: blind grep vs Atlas recall_route."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import metrics
from .paths import data_dir, repo_root_from_pkg
from .routing import recall_route


SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "coverage",
    "vendor",
}


@dataclass
class BenchCase:
    id: str
    question: str
    expect_path_contains: list[str]
    min_savings_pct: float = 40.0


def token_proxy(chars: int) -> int:
    """Deterministic proxy: ~4 chars per token (no LLM required)."""
    return max(chars, 0) // 4


def load_bench_cases(cases_dir: Path) -> list[BenchCase]:
    cases: list[BenchCase] = []
    for path in sorted(cases_dir.glob("bench-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cases.append(
            BenchCase(
                id=data.get("id", path.stem),
                question=data["question"],
                expect_path_contains=list(data.get("expect_path_contains", [])),
                min_savings_pct=float(data.get("min_savings_pct", 40.0)),
            )
        )
    return cases


def _tokens(question: str) -> list[str]:
    stop = {"the", "and", "for", "where", "what", "how", "is", "are", "with", "from"}
    return [t for t in re.findall(r"[a-z0-9_./]+", question.lower()) if len(t) > 2 and t not in stop]


def _iter_source_files(project: Path) -> list[Path]:
    out: list[Path] = []
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        # Indexes themselves are cheap navigation — exclude from baseline "read" cost
        if ".cursor" in p.parts and p.name.endswith((".md", ".json")):
            continue
        if p.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".md", ".json", ".toml", ".yml", ".yaml"}:
            out.append(p)
    return out


def _read_chars(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def baseline_explore(project: Path, question: str, *, max_files: int = 40) -> dict[str, Any]:
    """Simulate blind grep: open every source file whose content matches a query token."""
    toks = _tokens(question)
    opened: list[dict[str, Any]] = []
    chars = 0
    for path in _iter_source_files(project):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        low = text.lower()
        if not toks or any(t in low or t in str(path).lower().replace("\\", "/") for t in toks):
            opened.append({"path": str(path.relative_to(project)).replace("\\", "/"), "chars": len(text)})
            chars += len(text)
            if len(opened) >= max_files:
                break
    return {
        "arm": "baseline",
        "files_opened": len(opened),
        "chars": chars,
        "token_proxy": token_proxy(chars),
        "paths": [o["path"] for o in opened],
    }


def atlas_explore(project: Path, question: str, *, max_files: int = 8) -> dict[str, Any]:
    """Follow recall_route: read only ranked cache hits (+ optional graph scope samples)."""
    route = recall_route(project, question)
    paths: list[str] = []
    for hit in route.get("cache_hits") or []:
        p = hit.get("path") or hit.get("endereco") or ""
        if p and p not in paths:
            paths.append(p)
    # Include drawer files from mempalace room if present under atlas-drawers
    drawers = project / ".cursor" / "atlas-drawers"
    room = (route.get("mempalace") or {}).get("room")
    if drawers.exists() and room:
        room_dir = drawers / room
        if room_dir.is_dir():
            for f in sorted(room_dir.glob("*.drawer.md"))[:2]:
                rel = str(f.relative_to(project)).replace("\\", "/")
                if rel not in paths:
                    paths.append(rel)

    opened: list[dict[str, Any]] = []
    chars = 0
    # Always count index navigation cost (small, honest)
    for idx in (
        project / ".cursor" / "mempalace-index.md",
        project / ".cursor" / "graphify-index.md",
        project / ".cursor" / "project-cache.md",
    ):
        if idx.exists():
            c = _read_chars(idx)
            chars += c
            opened.append({"path": str(idx.relative_to(project)).replace("\\", "/"), "chars": c, "kind": "index"})

    for rel in paths[:max_files]:
        path = project / rel
        if not path.is_file():
            continue
        c = _read_chars(path)
        chars += c
        opened.append({"path": rel, "chars": c, "kind": "target"})

    return {
        "arm": "atlas",
        "files_opened": len([o for o in opened if o.get("kind") == "target"]),
        "chars": chars,
        "token_proxy": token_proxy(chars),
        "paths": [o["path"] for o in opened if o.get("kind") == "target"],
        "indexes_read": [o["path"] for o in opened if o.get("kind") == "index"],
        "route": {
            "wing": (route.get("mempalace") or {}).get("wing"),
            "room": (route.get("mempalace") or {}).get("room"),
            "cache_hits": route.get("cache_hits") or [],
        },
    }


def _hit_expected(paths: list[str], expect: list[str]) -> bool:
    if not expect:
        return True
    blob = " ".join(paths).lower().replace("\\", "/")
    return all(e.lower().replace("\\", "/") in blob for e in expect)


def run_bench_case(project: Path, case: BenchCase) -> dict[str, Any]:
    base = baseline_explore(project, case.question)
    atlas = atlas_explore(project, case.question)
    b_tok = base["token_proxy"]
    a_tok = atlas["token_proxy"]
    if b_tok <= 0:
        savings = 0.0
    else:
        savings = max(0.0, (b_tok - a_tok) / b_tok * 100.0)
    found = _hit_expected(atlas["paths"], case.expect_path_contains)
    # Also accept if baseline somehow found it but atlas must still find target
    ok = found and savings >= case.min_savings_pct
    return {
        "id": case.id,
        "question": case.question,
        "baseline": base,
        "atlas": atlas,
        "token_proxy_baseline": b_tok,
        "token_proxy_atlas": a_tok,
        "savings_pct": round(savings, 1),
        "min_savings_pct": case.min_savings_pct,
        "found_target": found,
        "pass": ok,
    }


def default_fixture_root() -> Path:
    candidates = [
        repo_root_from_pkg() / "eval" / "fixture-monorepo",
        data_dir("eval", "fixture-monorepo"),
    ]
    return next((c for c in candidates if c.is_dir()), candidates[0])


def default_bench_cases_dir() -> Path:
    candidates = [
        repo_root_from_pkg() / "eval" / "cases" / "bench",
        data_dir("eval", "cases", "bench"),
    ]
    return next((c for c in candidates if c.is_dir()), candidates[0])


def run_bench(
    project: Path | None = None,
    *,
    cases_dir: Path | None = None,
    min_avg_savings: float = 40.0,
) -> dict[str, Any]:
    project = (project or default_fixture_root()).resolve()
    cases_dir = cases_dir or default_bench_cases_dir()
    cases = load_bench_cases(cases_dir)
    if not cases:
        return {
            "ok": False,
            "error": f"no bench-*.json cases in {cases_dir}",
            "project": str(project),
            "results": [],
        }
    results = [run_bench_case(project, c) for c in cases]
    avg = sum(r["savings_pct"] for r in results) / len(results) if results else 0.0
    passed = sum(1 for r in results if r["pass"])
    ok = passed == len(results) and avg >= min_avg_savings
    report = {
        "ok": ok,
        "project": str(project),
        "cases": len(results),
        "passed": passed,
        "avg_savings_pct": round(avg, 1),
        "min_avg_savings_pct": min_avg_savings,
        "token_proxy_baseline_total": sum(r["token_proxy_baseline"] for r in results),
        "token_proxy_atlas_total": sum(r["token_proxy_atlas"] for r in results),
        "results": results,
        "note": "token_proxy = chars//4 (deterministic; no LLM).",
    }
    metrics.record(
        project,
        "bench",
        ok=ok,
        avg_savings_pct=report["avg_savings_pct"],
        passed=passed,
        total=len(results),
    )
    return report


def format_bench_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Atlas bench (token proxy)",
        "",
        f"Project: `{report.get('project')}`",
        f"Average savings: **{report.get('avg_savings_pct')}%** "
        f"(baseline {report.get('token_proxy_baseline_total')} -> atlas {report.get('token_proxy_atlas_total')} tokens)",
        f"Cases: {report.get('passed')}/{report.get('cases')} passed",
        "",
        "| Case | Savings | Baseline tokens | Atlas tokens | Target |",
        "|------|---------|-----------------|--------------|--------|",
    ]
    for r in report.get("results") or []:
        flag = "PASS" if r.get("pass") else "FAIL"
        lines.append(
            f"| {flag} {r['id']} | {r['savings_pct']}% | {r['token_proxy_baseline']} | "
            f"{r['token_proxy_atlas']} | {'yes' if r.get('found_target') else 'no'} |"
        )
    lines.append("")
    lines.append(str(report.get("note") or ""))
    return "\n".join(lines) + "\n"
