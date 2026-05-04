# Scoped Command Reference

Every command in this file uses the pinned-remote variable. Resolve it once
per shell:

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
```

Then `"${R}:"` is the only remote prefix the skill is allowed to use.

## Allowed (Private-Drive Scope)

### Listing & inspection

| Command | Purpose |
|---------|---------|
| `rclone about "${R}:"` | Quota: total / used / free / trashed |
| `rclone listremotes` | Sanity check that the pinned remote exists (preflight only) |
| `rclone lsd "${R}:"` | Top-level folders |
| `rclone lsd "${R}:path"` | Subfolders at a path |
| `rclone ls "${R}:path"` | Flat file list with sizes |
| `rclone lsl "${R}:path"` | Long format with modtime |
| `rclone lsf "${R}:path"` | Path-only, one per line — pipe-friendly |
| `rclone lsf "${R}:" -R --include "*.pdf"` | Recursive search by name |
| `rclone lsjson "${R}:path"` | JSON, pair with `jq` |
| `rclone tree "${R}:path"` | Tree view |
| `rclone size "${R}:path"` | Folder size |
| `rclone ncdu "${R}:"` | Interactive TUI (user-driven) |
| `rclone cat "${R}:path/file.txt"` | Read a single file |

### Transfers (non-destructive)

| Command | Purpose |
|---------|---------|
| `rclone copy ~/local "${R}:remote" -P` | Upload (no deletes on remote) |
| `rclone copy "${R}:remote" ~/local -P` | Download |
| `rclone copy "${R}:src" "${R}:dst" -P` | Server-side copy within the same private Drive |
| `rclone check ~/local "${R}:remote"` | Hash-compare local vs remote |
| `rclone check ~/local "${R}:remote" --size-only` | Faster, less accurate compare |

### Transfers (destructive — require dry-run + confirm)

| Command | Why destructive |
|---------|-----------------|
| `rclone sync SRC DST` | Deletes anything on DST not in SRC |
| `rclone move SRC DST` | Deletes from SRC after copy |
| `rclone delete "${R}:path"` | Removes files matching filters |
| `rclone purge "${R}:path"` | Removes folder + everything under it |
| `rclone backend drop "${R}:"` | Empties Drive trash — irrecoverable |
| `rclone backend untrash "${R}:path"` | Recovers from trash (mostly safe but state-changing) |

For all of these:
1. Run with `--dry-run -v` first.
2. Show the plan to the user.
3. Get explicit confirmation.
4. For `sync`, prefer `--backup-dir "${R}:Backups/_versions/$(date +%Y-%m-%d)"`
   and `--max-delete N` as a safety cap.

### Google Workspace export

| Command | Purpose |
|---------|---------|
| `rclone copy "${R}:Notes" ~/local/notes --drive-export-formats "md,csv,pdf"` | Export Docs/Sheets/Slides |

Supported targets: `docx`, `odt`, `rtf`, `pdf`, `txt`, `html`, `epub`, `xlsx`,
`ods`, `csv`, `tsv`, `pptx`, `odp`, `svg`, `jpg`, `png`.

### Trash & restore

| Command | Purpose |
|---------|---------|
| `rclone ls "${R}:" --drive-trashed-only` | List trashed items |
| `rclone backend untrash "${R}:path/to/file"` | Restore from trash |
| `rclone backend drop "${R}:" --dry-run` | Preview emptying trash |
| `rclone backend drop "${R}:"` | Empty trash (PERMANENT) |

### Mount

| Command | Purpose |
|---------|---------|
| `rclone mount "${R}:" ~/mnt/my-gdrive --vfs-cache-mode full --daemon` | Mount as filesystem |
| `umount ~/mnt/my-gdrive` (mac) / `fusermount -u ~/mnt/my-gdrive` (linux) | Unmount |

### Sharing & links

| Command | Purpose |
|---------|---------|
| `rclone link "${R}:path/file.pdf"` | Generate a share link |

### Auth maintenance

| Command | Purpose |
|---------|---------|
| `rclone config reconnect "${R}:"` | Refresh OAuth when token expired |
| `rclone config show "${R}:"` | Inspect remote config (no secrets logged) |

### Bandwidth & rate control (private-account-friendly)

| Command | Purpose |
|---------|---------|
| `rclone copy ... --bwlimit 5M -P` | Cap throughput |
| `rclone copy ... --bwlimit "08:00,1M 18:00,off" -P` | Schedule |
| `rclone copy ... --tpslimit 10` | Cap API calls per second |
| `rclone copy ... --transfers 8 --checkers 16` | Faster on good links |

## Disallowed (Refuse and Redirect to `gdrive-cli`)

These are blocked by this skill's scope. If the user asks for any of them,
respond with the refusal template in SKILL.md and recommend `gdrive-cli`.

| Pattern | Why disallowed |
|---------|----------------|
| Any remote name other than `${R}:` | Out of pinned scope |
| `rclone backend drives "${R}:"` | Shared Drives are Workspace-only |
| `--drive-team-drive <ID>` | Targets a Shared Drive |
| `--drive-shared-with-me` | Files not in the user's own Drive |
| Setup answer `y` to "Configure as Shared Drive?" | Defeats private framing |
| Adding a second remote during setup | This skill manages exactly one |

## Detection Patterns

Use these greps to detect disallowed usage in a candidate command before
running it:

```bash
CMD="rclone copy gdrive: ~/local --drive-shared-with-me"

# Refuse if any remote other than ${R}: appears
echo "$CMD" | grep -oE '[A-Za-z0-9_-]+:' | grep -vx "${R}:" && echo "REFUSE: other remote"

# Refuse if disallowed flags appear
echo "$CMD" | grep -E -- '--drive-shared-with-me|--drive-team-drive|backend +drives' && echo "REFUSE: out-of-scope flag"
```

If either grep matches, do not execute. Refuse with the template message.

## jq Recipes (private-Drive scope)

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"

# Files modified in the last 24 hours
rclone lsjson "${R}:" -R | \
  jq '.[] | select(.ModTime > (now - 86400 | todate))'

# Top 10 largest files
rclone lsjson "${R}:" -R | \
  jq 'sort_by(.Size) | reverse | .[:10] | .[] | {name: .Name, mb: (.Size/1048576 | round)}'

# All Google Docs (export-only files have empty Size and a googleapis MimeType)
rclone lsjson "${R}:" -R | \
  jq '.[] | select(.MimeType | startswith("application/vnd.google-apps."))'
```
