from pathlib import Path

from atlas_memory.commands_bench import format_bench_markdown, run_bench, token_proxy


def test_token_proxy():
    assert token_proxy(0) == 0
    assert token_proxy(7) == 1
    assert token_proxy(400) == 100


def test_bench_fixture_saves_tokens():
    report = run_bench(min_avg_savings=40.0)
    assert report["ok"], format_bench_markdown(report)
    assert report["avg_savings_pct"] >= 40.0
    assert report["token_proxy_atlas_total"] < report["token_proxy_baseline_total"]
    for r in report["results"]:
        assert r["found_target"], r["id"]
        assert r["savings_pct"] >= r["min_savings_pct"], r
