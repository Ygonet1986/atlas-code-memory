[type:bugfix] [status:active]
summary: recall_route returned confident hits for unrelated questions because function words like "the" matched any cache entry.
why: A negative bench case (kubernetes ingress question against an auth/billing fixture) exposed it. Fix: shared query_tokens with English and Portuguese stopwords, plus dropping tokens present in more than 60% of entries in indexes of 10+ blocks, since those cannot discriminate. The bench baseline also now honours .atlasignore, which moved measured savings on a real repo from an inflated 98% to an honest 78%.
branch: -
commit: -
pr: -
files: src/atlas_memory/routing.py, src/atlas_memory/commands_bench.py, eval/cases/bench-real, tests/test_routing_precision.py
room: architecture
