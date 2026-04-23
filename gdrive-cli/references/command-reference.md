# rclone Drive Command Reference

Flag-by-flag reference for `rclone` subcommands used with Google Drive. Load
this when you need non-obvious flags or edge cases not covered in SKILL.md.

Official docs:
- rclone general: https://rclone.org/docs/
- rclone Drive backend: https://rclone.org/drive/

## Path syntax

- Local path: `/absolute/path` or `./relative/path` or `~/home/path`
- Drive path: `<remote-name>:<path>` (the colon is required)
- Drive root: `<remote-name>:` (empty path)

## Global flags (apply to most subcommands)

### Transfer control

| Flag | Purpose | Default |
|------|---------|---------|
| `--transfers N` | Parallel file transfers | 4 |
| `--checkers N` | Parallel file checkers | 8 |
| `--bwlimit RATE` | Bandwidth cap, e.g. `1M`, `10M:1M`, or time-scheduled | unlimited |
| `--tpslimit N` | Cap transactions per second (Drive API) | unlimited |
| `--tpslimit-burst N` | Burst size for tpslimit | 1 |
| `--buffer-size SIZE` | Per-file read buffer | 16M |
| `--multi-thread-streams N` | Parallel streams for a single file | 4 |
| `--multi-thread-cutoff SIZE` | Only use multi-thread above this size | 250M |

### Filtering

| Flag | Purpose |
|------|---------|
| `--include PATTERN` | Include only matching paths |
| `--exclude PATTERN` | Skip matching paths |
| `--include-from FILE` | Include patterns from file |
| `--exclude-from FILE` | Exclude patterns from file |
| `--filter RULE` | `+ pattern` or `- pattern` rules (processed in order) |
| `--filter-from FILE` | Filter rules from file |
| `--max-size SIZE` | Skip files larger than SIZE |
| `--min-size SIZE` | Skip files smaller than SIZE |
| `--max-age DURATION` | Only files newer than DURATION (`7d`, `2h`, etc.) |
| `--min-age DURATION` | Only files older than DURATION |
| `--files-from FILE` | Process only files listed in FILE (one path per line) |

### Safety

| Flag | Purpose |
|------|---------|
| `--dry-run` / `-n` | Simulate, do not modify anything |
| `--interactive` / `-i` | Prompt before each change |
| `--backup-dir PATH` | Move overwritten/deleted files here instead of deleting |
| `--suffix STRING` | Append to backed-up files (e.g., `.bak`) |
| `--max-delete N` | Abort if more than N files would be deleted |

### Logging / output

| Flag | Purpose |
|------|---------|
| `-q` / `--quiet` | No normal output |
| `-v` / `--verbose` | INFO-level logging |
| `-vv` | DEBUG-level logging |
| `--log-file FILE` | Write log to file |
| `--log-level LEVEL` | `ERROR`, `NOTICE`, `INFO`, `DEBUG` |
| `--stats DURATION` | Print stats every DURATION (e.g., `1s`, `10s`) |
| `--stats-one-line` | Single-line stats |
| `-P` / `--progress` | Interactive progress display |

### Modification-time handling

| Flag | Purpose |
|------|---------|
| `--checksum` / `-c` | Use checksum instead of modtime+size for change detection |
| `--size-only` | Use size only (fast but least accurate) |
| `--update` / `-u` | Skip files newer on destination |
| `--ignore-existing` | Skip any file that exists on destination |
| `--ignore-size` | Don't compare file sizes |

## Drive-specific flags

These apply whenever the source or destination is a Drive remote.

| Flag | Purpose |
|------|---------|
| `--drive-shared-with-me` | Restrict listing to items shared with the authenticated user |
| `--drive-trashed-only` | Only show items in trash |
| `--drive-include-trashed` | Include trashed items alongside normal listing |
| `--drive-team-drive ID` | Access a specific Shared Drive by ID |
| `--drive-export-formats FORMATS` | Export format priority for Google Docs/Sheets/Slides (comma-separated) |
| `--drive-import-formats FORMATS` | Format priority for converting uploads to Google formats |
| `--drive-use-trash` | Send deletes to trash instead of permanent (default: true) |
| `--drive-skip-gdocs` | Skip Google Workspace files in listings |
| `--drive-skip-checksum-gphotos` | Skip checksums for Google Photos (they don't match) |
| `--drive-stop-on-upload-limit` | Stop on quotaExceeded (vs. skip and continue) |
| `--drive-server-side-across-configs` | Allow server-side copy between different Drive configs |
| `--drive-acknowledge-abuse` | Download "abuse" files (requires file to be shared with you) |
| `--drive-allow-import-name-change` | Allow upload to change filename when converting to Google format |
| `--drive-use-created-date` | Use created date instead of modified for change detection |
| `--drive-impersonate EMAIL` | Impersonate a user (service-account setups only) |
| `--drive-chunk-size SIZE` | Upload chunk size (default 8M) — larger uses more RAM, fewer API calls |

## Export and import formats

Google Workspace files have no native binary — they must be converted on
download via `--drive-export-formats` (comma-separated priority list).

Supported export targets:

| Type | Formats |
|------|---------|
| Docs | `docx`, `odt`, `rtf`, `pdf`, `txt`, `html`, `md`, `epub` |
| Sheets | `xlsx`, `ods`, `csv`, `tsv`, `pdf`, `html` |
| Slides | `pptx`, `odp`, `pdf`, `html`, `txt` |
| Drawings | `svg`, `png`, `jpg`, `pdf` |

rclone picks the first format in the list that matches the source type:

```bash
# Docs→docx, Sheets→xlsx, Slides→pptx (MS Office parity)
rclone copy gdrive:src ~/dst --drive-export-formats "docx,xlsx,pptx"

# PDF for everything
rclone copy gdrive:src ~/dst --drive-export-formats "pdf"

# Markdown for Docs, CSV for Sheets
rclone copy gdrive:src ~/dst --drive-export-formats "md,csv"
```

`--drive-import-formats` controls the reverse — auto-converting uploads into
Google formats (off by default, requiring conversion is rarely what you want).

## Copy / sync / move

### `rclone copy SRC DST`

Non-destructive file copy. Common patterns:

```bash
rclone copy ~/folder gdrive:path -P
rclone copy gdrive:path ~/folder -P
rclone copy gdrive1: gdrive2: -P                          # cross-account Drive
rclone copy ~/folder gdrive:path --exclude ".git/**" --exclude "node_modules/**"
rclone copy ~/folder gdrive:path --max-age 24h            # only recent files
rclone copy gdrive:Docs ~/local --drive-export-formats "docx,xlsx,pptx"
```

### `rclone sync SRC DST`

**DESTRUCTIVE** — makes DST identical to SRC; deletes files on DST not in SRC.

```bash
rclone sync ~/folder gdrive:backup --dry-run -v
rclone sync ~/folder gdrive:backup --backup-dir gdrive:backup-history/$(date +%F) -P
rclone sync ~/folder gdrive:backup --max-delete 100 -P    # safety cap
```

### `rclone move SRC DST`

Copies then deletes from SRC.

```bash
rclone move ~/local-cache gdrive:archive --delete-empty-src-dirs --dry-run
```

### `rclone copyto` / `rclone moveto`

Treat destination as a file, not a directory (use for single-file renames).

```bash
rclone copyto ~/foo.txt gdrive:dst/renamed.txt
```

## Listing

### `rclone ls gdrive:PATH`

Recursive file list with size.

### `rclone lsl gdrive:PATH`

Long format: size, modtime, path.

### `rclone lsd gdrive:PATH`

Directories only (not recursive by default). Useful for top-level folder discovery.

### `rclone lsf gdrive:PATH`

Just paths, one per line. Use `-R` for recursive.

```bash
rclone lsf gdrive: -R --include "*.pdf"
rclone lsf gdrive: --files-only
rclone lsf gdrive: --dirs-only
rclone lsf gdrive: --format "tsp"   # t=time, s=size, p=path
```

Format codes: `p` path, `s` size, `t` modtime, `h` hash, `i` object ID, `o`
original ID, `m` MIME type, `e` encrypted name, `T` tier.

### `rclone lsjson gdrive:PATH`

JSON output — best for Claude processing.

```bash
rclone lsjson gdrive:Projects
rclone lsjson gdrive: -R                    # recursive
rclone lsjson gdrive: --hash                # include hashes
rclone lsjson gdrive: --files-only
rclone lsjson gdrive: --drive-shared-with-me
rclone lsjson gdrive: --no-modtime          # faster for big listings
```

Each object has: `Path`, `Name`, `Size`, `MimeType`, `ModTime`, `IsDir`, `ID`, `Hashes`.

### `rclone tree gdrive:PATH`

Tree view.

```bash
rclone tree gdrive:Projects -L 2     # depth limit
rclone tree gdrive:Projects --size
rclone tree gdrive:Projects -d       # dirs only
```

### `rclone size gdrive:PATH`

Total size and object count.

```bash
rclone size gdrive:Projects
rclone size gdrive:Projects --json
```

### `rclone ncdu gdrive:PATH`

Interactive TUI. Arrow keys navigate, `d` delete, `q` quit.

## File operations

### `rclone cat gdrive:PATH`

Stream a file to stdout.

```bash
rclone cat gdrive:notes/todo.md
rclone cat gdrive:big.log --head 1k
rclone cat gdrive:big.log --tail 1k
rclone cat gdrive:big.log --offset 1k --count 2k
```

### `rclone rcat gdrive:PATH`

Read stdin, write to Drive.

```bash
echo "hello" | rclone rcat gdrive:notes/hello.txt
tar czf - ~/project | rclone rcat gdrive:backups/project.tgz
```

### `rclone delete gdrive:PATH`

Delete files matching filters (does NOT delete directories by default).

```bash
rclone delete gdrive:tmp --include "*.log" --dry-run
rclone delete gdrive:tmp --min-age 30d
```

By default, deleted items go to Drive trash (`--drive-use-trash` is true). To
permanently delete, add `--drive-use-trash=false`.

### `rclone purge gdrive:PATH`

Delete directory + all contents. **DESTRUCTIVE, recursive.**

```bash
rclone purge gdrive:old-backup --dry-run
```

### `rclone rmdir gdrive:PATH`

Delete an empty directory.

### `rclone rmdirs gdrive:PATH`

Remove empty directories recursively.

### `rclone mkdir gdrive:PATH`

Create a directory.

### `rclone touch gdrive:PATH`

Create empty file or update modtime.

```bash
rclone touch gdrive:placeholder.txt
rclone touch gdrive:existing.txt --timestamp "2025-01-15 10:00:00"
```

## Comparison and integrity

### `rclone check SRC DST`

Compare SRC and DST by hash.

```bash
rclone check ~/local gdrive:path
rclone check ~/local gdrive:path --one-way            # only check SRC files on DST
rclone check ~/local gdrive:path --size-only          # faster, less accurate
rclone check ~/local gdrive:path --download           # download both sides and compare
rclone check ~/local gdrive:path \
  --differ diff.txt \
  --missing-on-dst missing-dst.txt \
  --missing-on-src missing-src.txt \
  --match match.txt \
  --error error.txt
```

### `rclone hashsum HASH gdrive:PATH`

Compute hashes. Drive supports `md5`, `sha1`, `sha256`, `crc32`.

```bash
rclone hashsum md5 gdrive:file.txt
rclone hashsum sha1 gdrive:Projects --download
```

### `rclone md5sum` / `rclone sha1sum`

Convenience aliases.

### `rclone dedupe gdrive:PATH`

Find and remove duplicate files. Drive allows multiple files to share a name
under the same folder (unusual), so this is especially useful here.

```bash
rclone dedupe gdrive:Projects --dry-run
rclone dedupe gdrive:Projects --dedupe-mode newest
rclone dedupe gdrive:Projects --dedupe-mode largest
rclone dedupe gdrive:Projects --dedupe-mode interactive
```

Modes: `interactive`, `skip`, `first`, `newest`, `oldest`, `largest`, `smallest`, `rename`.

## Mount and serve

### `rclone mount gdrive:PATH /local/mountpoint`

Mount Drive as a local filesystem. Requires FUSE (macFUSE on macOS, fuse/fuse3
on Linux, WinFsp on Windows).

**Note (macOS Homebrew):** The Homebrew formula excludes `mount` because it
depends on FUSE. Install from https://rclone.org/install/ or use `nfsmount`.

```bash
# Basic mount with VFS cache
rclone mount gdrive: ~/mnt/gdrive --vfs-cache-mode full --daemon

# Read-only
rclone mount gdrive: ~/mnt/gdrive --read-only --daemon

# Unmount
umount ~/mnt/gdrive                # macOS
fusermount -u ~/mnt/gdrive         # Linux
```

VFS cache modes:
- `off` — no cache (reads fetch each time, writes poorly supported)
- `minimal` — cache reads that fit in memory
- `writes` — cache for writes, uncached reads
- `full` — cache everything (recommended)

Important mount flags:

| Flag | Purpose |
|------|---------|
| `--vfs-cache-mode MODE` | `off`/`minimal`/`writes`/`full` |
| `--vfs-cache-max-size SIZE` | Max cache size on disk |
| `--vfs-cache-max-age DURATION` | Evict entries older than this |
| `--vfs-read-chunk-size SIZE` | Read chunk size |
| `--dir-cache-time DURATION` | How long to cache directory listings |
| `--poll-interval DURATION` | Poll for Drive changes |
| `--allow-other` | Let other users access |
| `--read-only` | Mount read-only |
| `--daemon` | Run in background |
| `--drive-export-formats FORMATS` | Set export formats for Google Workspace files |

### `rclone serve PROTOCOL gdrive:PATH`

Serve Drive over a protocol: `http`, `webdav`, `ftp`, `sftp`, `dlna`, `nfs`.

```bash
# HTTP (read-only by default)
rclone serve http gdrive: --addr :8080

# WebDAV with basic auth
rclone serve webdav gdrive: --addr :8080 --user alice --pass $(rclone obscure secret)
```

## Config management

### `rclone config`

Interactive menu. Sub-commands:

```bash
rclone config show                     # show all remotes
rclone config show gdrive              # show one remote
rclone config file                     # print config file path
rclone config touch                    # create empty config
rclone config dump                     # JSON dump of all remotes
rclone config create gdrive drive \
  scope=drive                          # non-interactive create (skips OAuth)
rclone config update gdrive key=value  # modify existing
rclone config password gdrive key=val  # set obscured password
rclone config delete gdrive            # remove remote
rclone config reconnect gdrive:        # re-OAuth (browser)
rclone config disconnect gdrive:       # revoke token locally
rclone config userinfo gdrive:         # show logged-in user
```

### `rclone authorize drive`

Get an OAuth token for a Drive remote (useful for headless config — run on a
desktop with browser, paste token to the server).

## Utility commands

### `rclone about gdrive:`

Report Drive quota.

```bash
rclone about gdrive:
rclone about gdrive: --json
rclone about gdrive: --full            # full precision
```

### `rclone link gdrive:PATH`

Generate a share link.

```bash
rclone link gdrive:shared/file.pdf
rclone link gdrive:shared/file.pdf --expire 24h   # Drive supports expiring links for some account types
```

### `rclone copyurl URL gdrive:PATH`

Download a URL directly to Drive (no local landing).

```bash
rclone copyurl https://example.com/big.iso gdrive:iso/
rclone copyurl https://example.com/big.iso gdrive:iso/big.iso --print-filename
```

### `rclone version`

Show version. `--check` to check for updates.

```bash
rclone version --check
rclone selfupdate      # self-upgrade (only if installed via curl script, not Homebrew)
```

## Drive-specific backend commands

`rclone backend <subcommand> gdrive:` — provider-specific operations.

| Subcommand | Purpose |
|------------|---------|
| `rclone backend drives gdrive:` | List Shared Drives available |
| `rclone backend shared-with-me gdrive:` | List items shared with the user |
| `rclone backend untrash gdrive:[path]` | Restore items from trash (recursive under path) |
| `rclone backend drop gdrive:` | Empty trash (PERMANENT) |
| `rclone backend set gdrive: -o <key>=<value>` | Set backend options dynamically |
| `rclone backend copyid gdrive: <fileID> <dst>` | Copy by Google file ID |
| `rclone backend exportformats gdrive:` | List supported export formats |
| `rclone backend importformats gdrive:` | List supported import formats |

Examples:

```bash
# List Shared Drives with IDs
rclone backend drives gdrive:

# Restore all trashed items under a path
rclone backend untrash gdrive:Projects --dry-run
rclone backend untrash gdrive:Projects

# Empty trash permanently
rclone backend drop gdrive: --dry-run
rclone backend drop gdrive:

# Copy a file by its Drive ID (useful when path navigation is awkward)
rclone backend copyid gdrive: 1ABC123xyz ~/local/
```

## Filtering pattern syntax

- `*` matches any sequence of non-separator characters
- `**` matches any sequence including separators
- `?` matches a single non-separator character
- `[abc]` character class
- `{a,b,c}` alternatives

Examples:

```
*.tmp              # any .tmp in current level
**/*.log           # any .log anywhere
node_modules/**    # everything under node_modules
/README.md         # only root README (leading / anchors)
```

Path matching is relative to the root of SRC or DST, not absolute.

## Drive API quotas and rate limits

Google Drive enforces:

- **750 GB per user per day** for uploads. Exceeding this returns `quotaExceeded`
  and blocks further uploads for 24 hours. `rclone copy` resumes correctly on
  re-run (skips already-uploaded files).
- **Queries per user per 100 seconds**: ~10,000. Hitting this returns
  `userRateLimitExceeded` (403). Mitigate with `--tpslimit 10`.
- **Max upload size**: 5 TB per file.
- **Doc export size limit**: ~10 MB for Google Docs (larger ones fail export;
  use `pdf` as a fallback).

Workarounds for heavy usage:

```bash
# Cap API rate
rclone copy ~/large gdrive:backup --tpslimit 10 --tpslimit-burst 10

# Reduce parallel transfers
rclone copy ~/large gdrive:backup --transfers 2 --checkers 4

# Stop cleanly when upload quota is hit (vs. trying forever)
rclone copy ~/large gdrive:backup --drive-stop-on-upload-limit
```
