---
name: gdrive-cli
description: >
  Operate Google Drive from the terminal via `rclone` — list, upload, download,
  search, sync, mount, check quota, export Google Docs/Sheets/Slides, browse
  Shared Drives, and manage trash. Use whenever the user mentions Google Drive,
  Drive folders, or anything stored in Google Workspace files from the command
  line. Trigger phrases include "google drive", "g drive", "gdrive", "drive cli",
  "upload to drive", "download from drive", "list drive", "search drive",
  "sync to drive", "backup to drive", "mount google drive", "mount drive",
  "check drive quota", "drive storage", "drive space", "google docs export",
  "shared drive", "shared with me", "drive trash", "empty drive trash",
  "google workspace files", "drive folder", "rclone drive", "rclone gdrive".
---

# Google Drive CLI Skill

Interact with Google Drive via `rclone`. This skill covers listing, uploading,
downloading, searching, syncing, mounting, exporting Google Workspace files
(Docs/Sheets/Slides), and handling Shared Drives and trash.

The underlying tool is `rclone` — a cloud storage swiss-army knife — but this
skill is scoped to Google Drive. For other providers (S3, Dropbox, OneDrive, etc.)
don't use this skill; run `rclone` directly with the appropriate remote.

## Constraints

- `rclone` must be installed (`brew install rclone` on macOS).
- A Google Drive remote must be configured via `rclone config`. OAuth is
  browser-based and cannot be automated — the user must run `rclone config`
  themselves.
- Remote names are user-chosen (e.g., `gdrive:`, `tx-gdrive:`, `personal:`).
  Always run `rclone listremotes` first — never assume a name.
- **Destructive operations** (`sync`, `move`, `delete`, `purge`) can permanently
  erase Drive data. Run with `--dry-run` first and confirm before executing.
- Daily upload quota on Google Drive is **750 GB per user**. Plan accordingly.
- Google Docs/Sheets/Slides have no file size and can't be downloaded as-is
  unless you pass `--drive-export-formats` to convert them.

## Preflight Check

Before any Drive operation:

```bash
rclone version          # confirm install
rclone listremotes      # find the Drive remote name
```

If `rclone` is missing:
- macOS: `brew install rclone`
- Linux: `sudo -v ; curl https://rclone.org/install.sh | sudo bash`
- Windows: `winget install Rclone.Rclone`

If no remote is configured, guide the user through `rclone config`:

1. `n` → new remote
2. Name: e.g., `gdrive`
3. Storage type: type `drive` (NOT `google cloud storage` — different product)
4. `client_id` / `client_secret` — leave blank
5. Scope: `1` (full) or `2` (read-only) or `3` (file-only)
6. Leave `service_account_file` blank
7. Edit advanced config: `n`
8. Use auto config: `y` — opens browser for OAuth
9. Configure as Shared Drive: `n` (unless using a Team/Shared Drive)
10. Confirm `y`, quit with `q`

To verify: `rclone about <remote>:` should return quota info.

## Safety Rules for Destructive Operations

| Command | What it does | Risk |
|---------|--------------|------|
| `rclone sync SRC DST` | Makes DST identical to SRC | Deletes files on DST not in SRC |
| `rclone move SRC DST` | Copies then deletes from SRC | Data loss if DST write fails |
| `rclone delete REMOTE:PATH` | Deletes files matching filters | Permanent |
| `rclone purge REMOTE:PATH` | Deletes folder + contents | Permanent, recursive |
| `rclone backend drop REMOTE:` | Empties Drive trash | Irrecoverable |

**Always:**
1. Run with `--dry-run` first and show the plan to the user.
2. Get explicit confirmation before running for real.
3. For `sync`, prefer `--backup-dir` to retain deleted versions.
4. Never chain destructive commands with `&&` without review.

Non-destructive operations (`copy`, `ls`, `lsd`, `lsf`, `lsjson`, `about`,
`check`, `cat`, `tree`, `size`, `ncdu`) proceed without extra confirmation.

## Output Format Guidance

| Command | Output | Best for |
|---------|--------|----------|
| `rclone ls` | `<size> <path>` per line | Flat file list |
| `rclone lsd` | Directories only | Top-level folder overview |
| `rclone lsl` | Long format with modtime | Human browsing |
| `rclone lsf` | Path only, one per line | Shell pipelines |
| `rclone lsjson` | JSON objects | Claude processing, jq filtering |
| `rclone tree` | Tree view | Visual structure |
| `rclone ncdu` | Interactive TUI | User-driven exploration |

When Claude needs to process output, prefer `rclone lsjson` with `jq`:

```bash
# Good — filtered JSON, minimal tokens
rclone lsjson gdrive:Projects | jq '.[] | select(.IsDir==false and .Size > 1000000)'

# Avoid — verbose table output wastes context
rclone lsl gdrive:Projects
```

## Quick Reference

| Action | Command |
|--------|---------|
| List remotes | `rclone listremotes` |
| Check quota | `rclone about gdrive:` |
| Top-level folders | `rclone lsd gdrive:` |
| Files in folder | `rclone ls gdrive:path` |
| List as JSON | `rclone lsjson gdrive:path` |
| Interactive browser | `rclone ncdu gdrive:` |
| Read a file | `rclone cat gdrive:path/file.txt` |
| Upload | `rclone copy ~/local gdrive:remote -P` |
| Download | `rclone copy gdrive:remote ~/local -P` |
| Search by name | `rclone lsf gdrive: -R --include "*.pdf"` |
| Compare local/remote | `rclone check ~/local gdrive:remote` |
| Folder size | `rclone size gdrive:path` |
| Mirror (DESTRUCTIVE) | `rclone sync ~/src gdrive:dst --dry-run` |
| Share link | `rclone link gdrive:path/file.pdf` |
| List Shared Drives | `rclone backend drives gdrive:` |
| Shared-with-me items | `rclone lsd gdrive: --drive-shared-with-me` |
| Trashed items | `rclone ls gdrive: --drive-trashed-only` |
| Empty trash | `rclone backend drop gdrive:` |
| Mount | `rclone mount gdrive: ~/mnt/gdrive --vfs-cache-mode full --daemon` |
| Reauthorize | `rclone config reconnect gdrive:` |

Global flags worth knowing:

| Flag | Purpose |
|------|---------|
| `-P` / `--progress` | Show transfer progress |
| `--dry-run` | Simulate without changes |
| `-v` / `-vv` | Verbose / debug logging |
| `--transfers N` | Parallel file transfers (default 4) |
| `--exclude "*.tmp"` | Skip matching files |
| `--include "*.pdf"` | Include only matching files |
| `--max-age 7d` | Only files newer than 7 days |
| `--backup-dir PATH` | Keep overwritten/deleted files |
| `--tpslimit 10` | Cap Drive API calls per second |

## Common Workflows

### Check quota and browse

```bash
rclone about gdrive:
rclone lsd gdrive:
rclone ncdu gdrive:          # interactive
```

### Upload files or folders

```bash
# Single file with progress
rclone copy ~/report.pdf gdrive:Reports/ -P

# Whole folder, skipping junk
rclone copy ~/project gdrive:Backups/project \
  --exclude ".git/**" --exclude "node_modules/**" -P
```

`rclone copy` is safe — it never deletes on the destination.

### Download from Drive

```bash
rclone copy gdrive:Reports/report.pdf ~/Downloads/ -P
rclone copy gdrive:Reports ~/Downloads/reports -P
```

### Search across Drive

```bash
# All PDFs recursively
rclone lsf gdrive: -R --include "*.pdf"

# Files modified in last 24 hours
rclone lsjson gdrive: -R | jq '.[] | select(.ModTime > (now - 86400 | todate))'

# Largest 10 files
rclone lsjson gdrive: -R | jq 'sort_by(.Size) | reverse | .[:10] | .[] | {name: .Name, mb: (.Size/1048576 | round)}'
```

### Export Google Docs / Sheets / Slides

Google Workspace files have no native file — you must tell rclone what format to
export them as. `--drive-export-formats` accepts a comma-separated priority list:

```bash
# Export Docs as .docx, Sheets as .xlsx, Slides as .pptx
rclone copy gdrive:Projects ~/local/projects \
  --drive-export-formats "docx,xlsx,pptx" -P

# Prefer PDF for everything
rclone copy gdrive:Projects ~/local/projects \
  --drive-export-formats "pdf" -P

# Markdown for Docs, CSV for Sheets
rclone copy gdrive:Notes ~/local/notes \
  --drive-export-formats "md,csv" -P
```

Supported export targets: `docx`, `odt`, `rtf`, `pdf`, `txt`, `html`, `epub`,
`xlsx`, `ods`, `csv`, `tsv`, `pptx`, `odp`, `svg`, `jpg`, `png`.

### Sync a local folder to Drive (DESTRUCTIVE)

Always two-step:

```bash
# 1. Dry-run
rclone sync ~/project gdrive:Backups/project --dry-run -v

# 2. Show output to user, get confirmation, then real run with safety net
rclone sync ~/project gdrive:Backups/project \
  --backup-dir gdrive:Backups/_versions/$(date +%Y-%m-%d) \
  --max-delete 100 \
  -P
```

### Compare local and remote

```bash
# Hash-based check
rclone check ~/project gdrive:Backups/project

# Size-only (faster, less accurate)
rclone check ~/project gdrive:Backups/project --size-only

# Produce diff reports
rclone check ~/project gdrive:Backups/project \
  --differ diff.txt \
  --missing-on-dst missing-dst.txt \
  --missing-on-src missing-src.txt
```

### Shared Drives

If the user is on Google Workspace, they may have Shared Drives (formerly Team Drives).

```bash
# List Shared Drives available to this account
rclone backend drives gdrive:

# To access one, either:
# (a) Reconfigure the remote with "Configure as Shared Drive? y" in rclone config
# (b) Use --drive-shared-with-me or --drive-team-drive flags ad-hoc

# Example: operate on a specific Shared Drive by ID
rclone ls gdrive: --drive-team-drive 0ABCDEF1234567890
```

### Shared-with-me

Files other users shared with you but that don't live in your My Drive:

```bash
rclone lsd gdrive: --drive-shared-with-me
rclone copy gdrive: ~/shared-downloads --drive-shared-with-me -P
```

### Trash management

```bash
# List trashed items
rclone ls gdrive: --drive-trashed-only

# Restore from trash (rclone backend command)
rclone backend untrash gdrive:path/to/file

# Empty trash (PERMANENT)
rclone backend drop gdrive: --dry-run      # preview first
rclone backend drop gdrive:                # execute
```

### Mount Drive as a filesystem

Requires FUSE. On macOS: `brew install --cask macfuse`. Note that Homebrew's
rclone formula excludes `mount` — install rclone from https://rclone.org/install/
for full mount support, or use `nfsmount` subcommand.

```bash
mkdir -p ~/mnt/gdrive
rclone mount gdrive: ~/mnt/gdrive --vfs-cache-mode full --daemon

# Unmount
umount ~/mnt/gdrive            # macOS
fusermount -u ~/mnt/gdrive     # Linux
```

### Generate a share link

```bash
rclone link gdrive:shared/file.pdf
# Returns: https://drive.google.com/open?id=...
```

### Bandwidth control

Useful on metered connections or to avoid hitting Drive's rate limits:

```bash
rclone copy ~/bigfolder gdrive:backup --bwlimit 5M -P
# Schedule: 1M during work hours, unlimited overnight
rclone copy ~/bigfolder gdrive:backup --bwlimit "08:00,1M 18:00,off" -P
# Cap API transactions per second
rclone copy ~/bigfolder gdrive:backup --tpslimit 10 -P
```

## Error Handling

| Symptom | Cause | Fix |
|---------|-------|-----|
| `command not found: rclone` | Not installed | `brew install rclone` |
| `didn't find section in config file` | Wrong remote name | `rclone listremotes` to check |
| `Failed to get oauth token` | Expired refresh token | `rclone config reconnect gdrive:` |
| `directory not found` | Path typo or missing `:` | Double-check `<remote>:<path>` |
| `quota exceeded` | Drive full or 750 GB/day hit | Wait 24h or free space |
| `userRateLimitExceeded` (403) | Too many API calls | Add `--tpslimit 10` |
| `exportSizeLimitExceeded` | Google Doc too large to export | Split the doc or use `--drive-export-formats pdf` |
| `mount: command not found` | Homebrew rclone lacks mount | Install from rclone.org or use `nfsmount` |
| Slow transfers | Default 4 parallel streams | Try `--transfers 8 --checkers 16` |

## References

For the full flag-by-flag reference of every subcommand, including Drive-specific
flags and advanced usage, read `references/command-reference.md`.

## Behavior Scenarios

### Scenario 1: Check Drive quota

```gherkin
Given rclone is installed and a Drive remote is configured
When the user asks about Drive storage or quota
Then run `rclone about <remote>:`
And report total, used, free, and trashed space
```

### Scenario 2: Upload to Drive

```gherkin
Given a Drive remote is configured
When the user asks to upload a file or folder to Drive
Then run `rclone copy <local> <remote>:<path> -P`
And report files transferred and total size
```

### Scenario 3: Sync local folder to Drive (destructive)

```gherkin
Given the user wants to mirror a local folder to Drive
When the user asks to sync or backup to Drive
Then first run `rclone sync <src> <dst> --dry-run -v`
And show planned deletions/overwrites to the user
And only execute real sync after explicit user confirmation
And prefer `--backup-dir` for recoverability
```

### Scenario 4: Browse Drive interactively

```gherkin
Given a Drive remote is configured
When the user asks to explore or browse Drive
Then prefer `rclone ncdu <remote>:` for interactive use
Or use `rclone lsjson <remote>:<path> | jq` when Claude needs to process output
```

### Scenario 5: Export Google Docs / Sheets / Slides

```gherkin
Given the user wants to download Google Workspace files
When the user asks to export or download Docs/Sheets/Slides
Then pass `--drive-export-formats` with appropriate targets (docx/xlsx/pptx/pdf/md/csv)
And explain that Google-native files have no size and must be exported
```

### Scenario 6: Access Shared Drives

```gherkin
Given the user is on Google Workspace with Shared Drives
When the user asks to list or access a Shared Drive
Then run `rclone backend drives <remote>:` to list available Shared Drives
And either guide reconfiguration or use `--drive-team-drive <ID>` flag
```

### Scenario 7: Shared-with-me items

```gherkin
Given the user wants to access files others shared with them
When the user asks about "shared with me" items
Then add `--drive-shared-with-me` flag to any list/copy command
And explain these items don't live in My Drive
```

### Scenario 8: rclone not installed

```gherkin
Given rclone is not on PATH
When the user asks any Drive operation
Then report the missing install and suggest `brew install rclone` (macOS)
Or the platform-appropriate install command
```

### Scenario 9: No Drive remote configured

```gherkin
Given rclone is installed but no Drive remote exists
When the user asks any Drive operation
Then explain OAuth cannot be automated
And walk through `rclone config`, emphasizing storage type `drive` (not `google cloud storage`)
```

### Scenario 10: Hitting the 750 GB daily upload limit

```gherkin
Given a large upload encounters quota errors
When rclone reports `quotaExceeded` or `userRateLimitExceeded`
Then explain Drive's 750 GB/day per-user upload cap
And suggest resuming the next day, or adding `--tpslimit 10 --transfers 2`
And point out that `rclone copy` resumes correctly on re-run (skips existing)
```
