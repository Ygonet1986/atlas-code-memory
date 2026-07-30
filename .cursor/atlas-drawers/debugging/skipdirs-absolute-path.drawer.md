[type:bugfix] [status:active]
summary: Skipped directory names were matched against the absolute path, so any project living under build/, dist/, vendor/ or site-packages/ was invisible to the cache builder and the bench baseline.
why: Only surfaced when installing the wheel in a clean venv: atlas bench --fixture reported a 0-token baseline because the bundled fixture sits under site-packages. Fix: match SKIP_DIRS against the path relative to the project root. Also added atlas init cache build so a fresh project routes on the first question, and made bench --real fail with instructions instead of benchmarking whatever directory it resolved to.
branch: -
commit: -
pr: -
files: src/atlas_memory/commands_cache.py, src/atlas_memory/commands_bench.py, src/atlas_memory/commands_init.py, src/atlas_memory/paths.py, tests/test_installed_layout.py
room: debugging
