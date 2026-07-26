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

## Incident

If a secret was pasted into a drawer: rotate the credential, supersede/delete the drawer, and treat the palace as compromised for that secret.
