import json
from pathlib import Path

from atlas_memory.commands_bench import (
    BenchCase,
    default_bench_cases_dir,
    load_bench_cases,
    run_bench,
)


def make_project(tmp_path: Path) -> Path:
    (tmp_path / ".cursor").mkdir(parents=True)
    (tmp_path / ".cursor" / "project-cache.md").write_text(
        "# Project Source Cache\n\n"
        "### auth.py\n- **path:** `src/auth.py`\n- **description:** Handles the user login flow.\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login():\n    return True\n" * 200, encoding="utf-8")
    (src / "billing.py").write_text("def charge():\n    return 1\n" * 200, encoding="utf-8")
    return tmp_path


def write_case(cases: Path, data: dict) -> None:
    cases.mkdir(parents=True, exist_ok=True)
    (cases / f"bench-{data['id']}.json").write_text(json.dumps(data), encoding="utf-8")


def test_negative_case_passes_when_router_stays_silent(tmp_path: Path):
    project = make_project(tmp_path / "proj")
    cases = tmp_path / "cases"
    write_case(cases, {"id": "quiet", "question": "kubernetes ingress sharding", "expect_no_hits": True, "min_savings_pct": 0})

    report = run_bench(project, cases_dir=cases)
    assert report["ok"]
    assert report["negative_cases"] == 1
    assert report["negative_passed"] == 1


def test_negative_case_fails_when_router_leaks(tmp_path: Path):
    project = make_project(tmp_path / "proj")
    cases = tmp_path / "cases"
    write_case(cases, {"id": "leak", "question": "user login flow", "expect_no_hits": True, "min_savings_pct": 0})

    report = run_bench(project, cases_dir=cases)
    assert not report["ok"]
    assert report["negative_passed"] == 0


def test_expect_path_absent_catches_a_wrong_hit(tmp_path: Path):
    project = make_project(tmp_path / "proj")
    cases = tmp_path / "cases"
    write_case(
        cases,
        {
            "id": "decoy",
            "question": "user login flow",
            "expect_path_contains": ["src/auth.py"],
            "expect_path_absent": ["src/auth.py"],
            "min_savings_pct": 0,
        },
    )
    report = run_bench(project, cases_dir=cases)
    assert not report["ok"], "a hit that is both required and forbidden must fail"


def test_savings_average_excludes_negative_cases(tmp_path: Path):
    project = make_project(tmp_path / "proj")
    cases = tmp_path / "cases"
    write_case(cases, {"id": "pos", "question": "user login flow", "expect_path_contains": ["src/auth.py"], "min_savings_pct": 0})
    write_case(cases, {"id": "neg", "question": "kubernetes ingress sharding", "expect_no_hits": True, "min_savings_pct": 0})

    report = run_bench(project, cases_dir=cases)
    assert report["positive_cases"] == 1
    assert report["negative_cases"] == 1
    positive = next(r for r in report["results"] if r["kind"] == "positive")
    assert report["avg_savings_pct"] == positive["savings_pct"]


def test_case_kind_classification():
    assert BenchCase("a", "q", [], expect_no_hits=True).negative
    assert BenchCase("a", "q", [], expect_path_absent=["x/"]).negative
    # Both required and forbidden paths: still a positive case with a precision guard.
    assert not BenchCase("a", "q", ["y/"], expect_path_absent=["x/"]).negative


def test_shipped_real_repo_cases_are_loadable():
    real = default_bench_cases_dir().parent / "bench-real"
    if not real.is_dir():
        return
    cases = load_bench_cases(real)
    assert cases
    assert any(c.negative for c in cases), "real suite must include a precision case"
