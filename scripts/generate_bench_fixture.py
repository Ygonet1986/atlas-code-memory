"""Generate eval/fixture-monorepo for atlas bench (run from repo root)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "eval" / "fixture-monorepo"


def main() -> None:
    files: dict[str, str] = {
        "README.md": (
            "# Fixture Monorepo\n\n"
            "Synthetic large project for atlas bench token savings.\n"
        ),
        ".cursor/mempalace-index.md": """# MemPalace Index

### demo wing
- **wing:** `fixture`
- **room:** `architecture`
- **status:** ready

### debugging
- **wing:** `fixture`
- **room:** `debugging`
- **status:** ready
""",
        ".cursor/graphify-index.md": """# Graphify Index

### auth
- **escopo:** `src/auth`
- **grafo:** `src/auth/graphify-out/`
- **status:** ready
- **descricao:** authentication module

### billing
- **escopo:** `src/billing`
- **grafo:** `src/billing/graphify-out/`
- **status:** ready
""",
        ".cursor/project-cache.md": """# Project Cache

### login.py
- **path:** `src/auth/login.py`
- **description:** User login authentication entrypoint — session cookies and password verify.

### session.py
- **path:** `src/auth/session.py`
- **description:** Session store for authenticated users.

### invoice.py
- **path:** `src/billing/invoice.py`
- **description:** Invoice generation and billing totals.

### engine.py
- **path:** `src/core/engine.py`
- **description:** Core rendering engine loop.

### README.md
- **path:** `README.md`
- **description:** Project readme for fixture monorepo.
""",
        ".cursor/atlas-drawers/architecture/use-postgres.drawer.md": """[type:decision] [status:active]
summary: Use Postgres for auth sessions
why: team knows SQL and ACID matters for login
branch: main
commit: abc123
pr: -
files: src/auth/session.py
wing: fixture
room: architecture
""",
        "src/auth/login.py": '''"""User login authentication entrypoint."""

def authenticate(username: str, password: str) -> bool:
    """Verify password and create session."""
    return bool(username and password)

def login_handler(request):
    return authenticate(request.get("user"), request.get("pass"))
''',
        "src/auth/session.py": '''"""Session store for authenticated users (Postgres-backed)."""

class SessionStore:
    def get(self, sid: str):
        return None
''',
        "src/billing/invoice.py": '''"""Invoice generation and billing totals."""

def make_invoice(user_id: str, amount: float) -> dict:
    return {"user_id": user_id, "amount": amount, "currency": "USD"}
''',
        "src/core/engine.py": '''"""Core rendering engine loop."""

def run_engine():
    while True:
        pass
''',
    }

    for rel, content in files.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    pad = ("# decoy noise\n" + ("x" * 200) + "\n") * 20
    for i in range(25):
        for topic in ("auth", "login", "billing", "engine", "session"):
            path = ROOT / "src" / "decoys" / f"module_{i:02d}" / f"{topic}_noise.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f'"""Decoy module mentioning {topic} for grep noise."""\n'
                f"# This file talks about {topic} but is not the real implementation.\n"
                + pad
                + f'def fake_{topic}_{i}():\n    return "{topic}"\n',
                encoding="utf-8",
            )

    n = sum(1 for p in ROOT.rglob("*") if p.is_file())
    print(f"Wrote fixture at {ROOT} ({n} files)")


if __name__ == "__main__":
    main()
