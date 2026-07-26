from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from . import metrics
from .commands_stale import parse_graphify_index


@dataclass
class EvalCase:
    id: str
    question: str
    expect_layer: str  # mempalace|graphify|cache
    expect_contains: list[str]


def load_cases(cases_dir: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for path in sorted(cases_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cases.append(
            EvalCase(
                id=data.get("id", path.stem),
                question=data["question"],
                expect_layer=data["expect_layer"],
                expect_contains=list(data.get("expect_contains", [])),
            )
        )
    return cases


def _search_md(path: Path, needles: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    return all(n.lower() in text for n in needles)


def run_eval(project: Path, cases_dir: Path | None = None) -> list[dict]:
    """
    Offline harness: checks whether Atlas indexes contain the expected anchors.
    Does not call an LLM — scores index readiness for each question type.
    """
    project = project.resolve()
    if cases_dir is None:
        # bundled or repo eval/cases
        from .paths import data_dir, repo_root_from_pkg

        candidates = [
            project / "eval" / "cases",
            repo_root_from_pkg() / "eval" / "cases",
            data_dir("eval", "cases"),
        ]
        cases_dir = next((c for c in candidates if c.is_dir()), candidates[0])

    cases = load_cases(cases_dir)
    results = []
    mpi = project / ".cursor" / "mempalace-index.md"
    gfi = project / ".cursor" / "graphify-index.md"
    cache = project / ".cursor" / "project-cache.md"

    for case in cases:
        ok = False
        detail = ""
        if case.expect_layer == "cache":
            ok = _search_md(cache, case.expect_contains)
            detail = "project-cache"
        elif case.expect_layer == "graphify":
            # Index file must mention scope machinery; entries may still be empty.
            ok = _search_md(gfi, case.expect_contains)
            detail = "graphify-index"
        elif case.expect_layer == "mempalace":
            ok = _search_md(mpi, case.expect_contains)
            detail = "mempalace-index"
        else:
            detail = f"unknown layer {case.expect_layer}"

        results.append(
            {
                "id": case.id,
                "question": case.question,
                "expect_layer": case.expect_layer,
                "pass": ok,
                "detail": detail,
            }
        )
    metrics.record(project, "eval", passed=sum(1 for r in results if r["pass"]), total=len(results))
    return results
