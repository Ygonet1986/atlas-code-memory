# Publishing Atlas

## GitHub

```bash
cd /path/to/atlas-memory
gh repo create atlas-memory --public --source=. --remote=origin --push
gh release create v0.2.0 -t v0.2.0 --generate-notes
```

## PyPI

The distribution is published as **`atlas-code-memory`** (the `atlas-memory` name was
already taken on PyPI by an unrelated project). The import package is still
`atlas_memory` and the commands are still `atlas` / `atlas-mcp`.

```bash
pip install -e ".[dev]"
python -m build
twine check dist/*
twine upload dist/*   # requires a PyPI token
```

GitHub Actions workflow `.github/workflows/publish.yml` runs on version tags `v*` and
authenticates with the `PYPI_API_TOKEN` repository secret.

To switch to Trusted Publishing instead, add a publisher on pypi.org for owner
`Ygonet1986`, repository `atlas-memory`, workflow `publish.yml`, then drop the
`password:` input and restore `permissions: id-token: write`.
