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
authenticates with [Trusted Publishing](https://docs.pypi.org/trusted-publishers), so
there is no PyPI token stored anywhere. The publisher is registered on pypi.org for
owner `Ygonet1986`, repository `atlas-memory`, workflow `publish.yml`.

The workflow refuses to run when the tag disagrees with the version in
`pyproject.toml`, which is what makes `skip-existing` safe: a re-run cannot silently
publish nothing because someone forgot to bump the version. It also accepts
`workflow_dispatch`, so the pipeline can be exercised without cutting a release.

### Cutting a release

1. Bump `version` in `pyproject.toml` and add the section to `CHANGELOG.md`.
2. Commit, then `git tag -a vX.Y.Z -m "Atlas Memory X.Y.Z"` and push the tag.
3. `gh release create vX.Y.Z --title ... --notes ...`
