# Contributing

## Dev setup

```bash
pip install -e ".[dev]"
pytest -q
```

## Release checklist

1. Bump version in `pyproject.toml` and `src/atlas_memory/__init__.py`
2. Update `CHANGELOG.md`
3. `pytest` + `atlas eval` on a fresh `mktemp -d` project
4. Tag `vX.Y.Z`

## Design rules

- Keep Graphify and Mind Map mutually exclusive in docs and `atlas doctor`
- Never require a cloud API for core CLI
- Secret scanner must fail closed on `atlas checkpoint`
