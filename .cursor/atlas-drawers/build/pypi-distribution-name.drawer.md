[type:decision] [status:active]
summary: The PyPI distribution is atlas-code-memory, not atlas-memory, and the publish workflow authenticates with the PYPI_API_TOKEN secret rather than Trusted Publishing.
why: PyPI rejected the 0.4.0 upload with 403 because atlas-memory has been registered since 2023 by an unrelated project (Mitch Carter, v0.1.1). Only the distribution name changed: the import package is still atlas_memory, the entry points are still atlas and atlas-mcp, the GitHub repo is still Ygonet1986/atlas-memory, and the MCP server key in editor configs is still atlas-memory. Trusted Publishing was the first attempt and failed too, because it has to be configured on pypi.org before the workflow runs and the project did not exist yet; the workflow now passes password from the PYPI_API_TOKEN secret and drops the id-token permission. Now that the project exists on PyPI, switching to Trusted Publishing is one form on pypi.org (owner Ygonet1986, repo atlas-memory, workflow publish.yml) plus removing the password input.
branch: main
commit: 43a2d7f
pr: -
files: pyproject.toml, .github/workflows/publish.yml, docs/publishing.md, README.md, docs/quickstart.md, CHANGELOG.md
room: build
