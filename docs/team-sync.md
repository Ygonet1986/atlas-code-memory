# Team sync

## Export

```bash
atlas sync export -C . -o atlas-bundle.tar.gz
```

Share the tarball via your normal channel (Drive, git LFS, internal artifactory).  
Bundle contains indexes + drawers + Atlas skill/rule — **not** the MemPalace DB.

## Import

```bash
atlas sync import -C . atlas-bundle.tar.gz
```

Then, if MemPalace is installed:

```bash
mempalace mine .cursor/atlas-drawers --wing <your-wing>
```

## MemPalace remote (optional)

For a shared palace, see MemPalace `serve` / team MCP docs. Atlas indexes stay per-repo; the palace can be shared.
