# Security

## Principles

- Atlas runs locally; no required cloud.
- Memory backends must not receive secrets.
- `atlas checkpoint` scans drawer text before you file it.

## Deny list (non-exhaustive)

- `.env`, `.env.*`
- `credentials.json`, `service-account.json`
- PEM/private keys
- GitHub PATs, Slack tokens, OpenAI `sk-…`
- Connection strings with embedded passwords

## `.atlasignore`

Copied by `atlas init` from `.atlasignore.example`. Keep build artifacts and secret filenames out of import/cache suggestions.

## Local daemon

`atlas daemon` and `atlas life serve` expose personal memories, spend DeepSeek
credits and can trigger git pushes. Binding to `127.0.0.1` is **not** a security
boundary: every page in your browser can reach a loopback port. Three controls
close that gap.

**Token.** Every request needs the daemon token, in `Authorization: Bearer <token>`,
in the `X-Atlas-Token` header, or as `?token=`. It is generated on first use and
stored in `~/.atlas/daemon-token` with owner-only permissions.

```bash
atlas token             # print it
atlas token --rotate    # revoke and issue a new one
ATLAS_DAEMON_TOKEN=...  # override, e.g. in CI
```

The single exception is `GET /api/health`, which answers without a token so that
clients can probe liveness. Unauthenticated it returns only `{"ok": true, ...}` —
no version, no paths, no memory.

**Origins.** No wildcard CORS. The daemon echoes `Access-Control-Allow-Origin`
only for the desktop app's own origin (`tauri://localhost`). Any other page gets
no CORS headers, so the browser refuses to hand it the response body.

**Host.** Requests whose `Host` header does not name the loopback interface are
rejected with 403, which blocks DNS rebinding.

`atlas daemon --no-auth` disables the token. It prints a warning and should only
be used on a machine where you already trust every local process.

## Team bundles

`atlas sync import` extracts a tarball produced by someone else, so it is
untrusted input by design. Extraction refuses absolute paths, `..` traversal,
symlinks, hard links and device files, and writes nothing at all if any member
fails the check. File modes are normalised, so setuid bits never survive a
bundle.

## Incident

If a secret was pasted into a drawer: rotate the credential, supersede/delete the drawer, and treat the palace as compromised for that secret.
