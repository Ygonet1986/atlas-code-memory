# Example: pnpm monorepo

```text
packages/web
packages/api
```

Register **per package** graphs — never the monorepo root.

```bash
atlas onboard -C examples/pnpm-monorepo
atlas graph add web --escopo packages/web
atlas graph add api --escopo packages/api
```
