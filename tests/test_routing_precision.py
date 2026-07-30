from pathlib import Path

from atlas_memory.routing import query_tokens, recall_route


def write_cache(tmp_path: Path, entries: list[tuple[str, str, str]]) -> Path:
    (tmp_path / ".cursor").mkdir(exist_ok=True)
    blocks = [
        f"### {name}\n- **path:** `{path}`\n- **description:** {desc}"
        for name, path, desc in entries
    ]
    (tmp_path / ".cursor" / "project-cache.md").write_text(
        "# Project Source Cache\n\n" + "\n\n".join(blocks) + "\n", encoding="utf-8"
    )
    return tmp_path


def test_query_tokens_drop_function_words():
    tokens = query_tokens("Where is the login handler for that user?")
    assert "the" not in tokens
    assert "where" not in tokens
    assert "login" in tokens and "handler" in tokens


def test_query_tokens_drop_portuguese_function_words():
    tokens = query_tokens("Onde que fica o handler de login para o usuario?")
    assert "onde" not in tokens
    assert "que" not in tokens and "para" not in tokens
    assert "handler" in tokens and "login" in tokens


def test_unrelated_question_returns_no_hits(tmp_path: Path):
    project = write_cache(
        tmp_path,
        [
            ("auth.py", "src/auth.py", "Handles the user login flow."),
            ("billing.py", "src/billing.py", "Builds the monthly invoice."),
        ],
    )
    route = recall_route(project, "Where is the kubernetes ingress controller configured?")
    assert route["cache_hits"] == []


def test_relevant_question_still_ranks_the_right_file(tmp_path: Path):
    project = write_cache(
        tmp_path,
        [
            ("auth.py", "src/auth.py", "Handles the user login flow."),
            ("billing.py", "src/billing.py", "Builds the monthly invoice."),
        ],
    )
    hits = recall_route(project, "Where is the user login flow?")["cache_hits"]
    assert hits[0]["path"] == "src/auth.py"


def test_ubiquitous_token_is_ignored_in_large_index(tmp_path: Path):
    # "atlas" appears in every entry, so it cannot discriminate between them.
    entries = [(f"mod{i}.py", f"src/mod{i}.py", "atlas module doing work") for i in range(12)]
    entries.append(("secrets.py", "src/secrets.py", "atlas module scanning for credentials"))
    project = write_cache(tmp_path, entries)

    hits = recall_route(project, "atlas credentials scanning")["cache_hits"]
    assert hits, "a discriminating token should still match"
    assert hits[0]["path"] == "src/secrets.py"
