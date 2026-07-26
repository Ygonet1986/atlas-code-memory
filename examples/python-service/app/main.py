"""Demo FastAPI-like stub (no deps)."""

def health() -> dict:
    return {"ok": True}


def main() -> None:
    print(health())


if __name__ == "__main__":
    main()
