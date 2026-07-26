# Publishing Atlas

## GitHub

```bash
cd /path/to/atlas-memory
gh repo create atlas-memory --public --source=. --remote=origin --push
gh release create v0.2.0 -t v0.2.0 --generate-notes
```

## PyPI

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
twine upload dist/*   # requires PYPI token
```

GitHub Actions workflow `.github/workflows/publish.yml` runs on version tags `v*`.
