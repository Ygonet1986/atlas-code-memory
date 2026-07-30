[type:decision] [status:active]
summary: Everything published is named atlas-code-memory - the PyPI distribution and the GitHub repository - while the import package stays atlas_memory.
why: PyPI rejected the 0.4.0 upload with 403 because atlas-memory has been registered since 2023 by an unrelated project (Mitch Carter, v0.1.1), so the distribution became atlas-code-memory. The GitHub repo was then renamed to match, rather than recreated, so the tag, the v0.4.0 release, the Actions history and the redirects from the old URL all survive. What did not change: the import package is still atlas_memory, the entry points are still atlas and atlas-mcp, and the MCP server key in editor configs is still atlas-memory. Publishing uses Trusted Publishing with owner Ygonet1986, repository atlas-code-memory, workflow publish.yml and an empty environment - the repository stores no PyPI token. Two dead ends worth remembering: Trusted Publishing must be registered on pypi.org before the workflow runs and cannot be registered against a project name someone else owns, and the repository field in that form means the GitHub repo name, not the PyPI project name.
branch: main
commit: 43a2d7f
pr: -
files: pyproject.toml, .github/workflows/publish.yml, docs/publishing.md, README.md, docs/quickstart.md, src/atlas_memory/cli.py, CHANGELOG.md
room: build
