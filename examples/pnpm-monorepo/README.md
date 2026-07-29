# Example: pnpm monorepo

```text
packages/web
packages/api
```

Register **per package** graphs — never the monorepo root.

```bash
atlas onboard -C examples/pnpm-monorepo
atlas graph add web --scope packages/web
atlas graph add api --scope packages/api
```
