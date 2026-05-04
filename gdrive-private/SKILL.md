---
name: gdrive-private
version: 1.0.0
description: >
  Operate ONLY the user's private (personal) Google Drive via `rclone`, scoped
  to a single pinned remote (default `gdrive-private:`, override with the
  `GDRIVE_PRIVATE_REMOTE` env var). A safety wrapper around the `gdrive-cli`
  skill: refuses other remotes (e.g., work/Workspace accounts), strips Shared
  Drive and shared-with-me paths, and walks first-time users through OAuth
  setup with a personal Gmail account. Use whenever the user wants to act on
  their *private* / *personal* Drive specifically — not their work or shared
  Drive. Trigger phrases include "private google drive", "private gdrive",
  "personal google drive", "personal gdrive", "my private drive", "my personal
  drive", "my gdrive", "private drive", "personal drive", "upload to my
  private drive", "download from my personal drive", "backup to private
  google drive", "list my private drive", "search my personal drive",
  "private drive quota", "sync to my private gdrive", "private gdrive only",
  "use my personal google drive", "/gdrive-private".
---

# Private Google Drive Skill

A scoped wrapper around the `gdrive-cli` skill that operates **only on the
user's private Google Drive**. The remote is pinned to a single name (default
`gdrive-private:`); operations on any other remote — work, Workspace, Shared
Drive, "shared with me" — are refused and redirected to the base `gdrive-cli`
skill.

The underlying tool is still `rclone`; this skill adds (a) a single pinned
remote, (b) refusal of out-of-scope remotes and flags, and (c) a setup path
explicitly aimed at a personal Gmail account.

When the user wants the full Drive surface — multiple accounts, Shared Drives,
shared-with-me — use `gdrive-cli` instead.

## Constraints

- `rclone` must be installed (see Preflight). The setup path is
  inherited from `gdrive-cli`; nothing about install changes here.
- The remote name is **pinned**. Default: `gdrive-private`. Override per
  session by setting `GDRIVE_PRIVATE_REMOTE` (without trailing `:`) — for
  example `GDRIVE_PRIVATE_REMOTE=personal` makes `personal:` the pinned
  remote.
- The pinned remote must be a **personal Google Drive (`@gmail.com`)**, not a
  Google Workspace / corporate account. Workspace Drives carry Shared Drives
  and admin policies that defeat the "private" framing.
- **Out-of-scope, refused by this skill**:
  - Any remote name other than the pinned one (e.g., `tx-gdrive:`,
    `work-gdrive:`).
  - `--drive-shared-with-me` (those files don't live in *your* Drive).
  - `--drive-team-drive <ID>` and `rclone backend drives` (Shared Drives are a
    Workspace feature; private accounts don't have them).
  - Reconfiguring the remote as a Shared Drive.
  When the user asks for any of the above, refuse politely and recommend the
  base `gdrive-cli` skill.
- Destructive operations (`sync`, `move`, `delete`, `purge`,
  `backend drop`, `backend untrash`) follow the same `--dry-run` + confirm
  rules as `gdrive-cli`. The pinned-remote scoping does not relax that.

## Resolving the Pinned Remote

Run this preflight at the start of every operation. It's the only place the
skill is allowed to deviate from the pinned name.

```bash
# 1. Check rclone is present
rclone version >/dev/null 2>&1 || { echo "rclone not installed"; exit 1; }

# 2. Resolve the pinned remote name
PRIVATE_REMOTE="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"

# 3. Confirm it exists in rclone config
if ! rclone listremotes | grep -qx "${PRIVATE_REMOTE}:"; then
  echo "Pinned private remote '${PRIVATE_REMOTE}:' is not configured."
  echo "Either run setup (see SKILL.md), or export GDRIVE_PRIVATE_REMOTE to"
  echo "match an existing personal-account remote in:"
  rclone listremotes
  exit 1
fi

# 4. Sanity-check it points at a personal account, not a Workspace one
rclone about "${PRIVATE_REMOTE}:" >/dev/null 2>&1 || \
  { echo "Remote ${PRIVATE_REMOTE}: is not reachable; run 'rclone config reconnect ${PRIVATE_REMOTE}:'"; exit 1; }
```

After this, every command in the workflow uses `${PRIVATE_REMOTE}:` and
nothing else.

## Refusal Protocol

If the user's request would force the skill outside the pinned-private scope,
do not execute it. Respond with a short message of this shape:

> This skill is scoped to your private Google Drive (`<remote>:`) only.
> What you're asking — *<reason: other remote / Shared Drive / shared-with-me
> / Workspace account>* — is out of scope. For that, use the base
> `gdrive-cli` skill (which supports the full multi-account surface), or
> rerun with `GDRIVE_PRIVATE_REMOTE=<name>` if you want this skill pinned to
> a different *personal* remote.

Concrete triggers for refusal:

| Request | Why refused | Redirect |
|---------|-------------|----------|
| User names another remote (`tx-gdrive:`, `work:`) | Out of scope | `gdrive-cli` |
| `--drive-shared-with-me` | Not in user's own Drive | `gdrive-cli` |
| `--drive-team-drive <ID>` / `rclone backend drives` | Shared Drives are Workspace-only | `gdrive-cli` |
| "Reconfigure as Shared Drive" during setup | Defeats private scope | `gdrive-cli` setup |
| Pinned remote points at a Workspace account | Mismatch with "private" framing | Reconfigure or `gdrive-cli` |

## First-Time Setup (Personal Gmail Only)

If the pinned remote is missing, walk the user through `rclone config` with
these private-account specific choices:

1. `n` → new remote
2. **Name**: `gdrive-private` (or whatever `GDRIVE_PRIVATE_REMOTE` is set to)
3. Storage type: type `drive` (NOT `google cloud storage`)
4. `client_id` / `client_secret` — leave blank (uses rclone's shared client;
   fine for personal use)
5. **Scope**: `1` (full read/write). Use `2` (read-only) if the user
   explicitly wants a hands-off backup-only setup.
6. `service_account_file`: leave blank — service accounts are for Workspace,
   not personal Gmail.
7. Edit advanced config: `n`
8. Auto config: `y` — opens browser. **The user must sign in with their
   personal `@gmail.com` account, not a work account.** Confirm this aloud
   before they click.
9. **"Configure this as a Shared Drive (Team Drive)?"** → `n`. Always. If
   they say yes, abort and explain that Shared Drives put this skill out of
   scope.
10. Confirm `y`, quit with `q`.

Verify with `rclone about gdrive-private:` — quota numbers should appear.

## Inherited Surface

Everything the base `gdrive-cli` skill does — list, upload, download, search,
sync (with safety), export Google Workspace files, mount, trash management,
share links, bandwidth control — is available here, **with every command
substituting the pinned remote** for the example `gdrive:` placeholder.

For the full command catalog (with the substitution applied), read
`references/scoped-commands.md`.

For deeper rclone flag reference, read the base skill's
`references/command-reference.md` (in the `gdrive-cli` skill directory).

## Quick Reference (pinned-remote form)

Assume `R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"` is exported.

| Action | Command |
|--------|---------|
| Check quota | `rclone about "${R}:"` |
| Top-level folders | `rclone lsd "${R}:"` |
| List a folder | `rclone ls "${R}:path"` |
| List as JSON | `rclone lsjson "${R}:path"` |
| Read a file | `rclone cat "${R}:path/file.txt"` |
| Upload | `rclone copy ~/local "${R}:remote" -P` |
| Download | `rclone copy "${R}:remote" ~/local -P` |
| Search by name (recursive) | `rclone lsf "${R}:" -R --include "*.pdf"` |
| Folder size | `rclone size "${R}:path"` |
| Mirror local → Drive (DESTRUCTIVE) | `rclone sync ~/src "${R}:dst" --dry-run` then real run |
| Share link | `rclone link "${R}:path/file.pdf"` |
| Trashed items | `rclone ls "${R}:" --drive-trashed-only` |
| Empty trash (PERMANENT) | `rclone backend drop "${R}:" --dry-run` then real run |
| Mount | `rclone mount "${R}:" ~/mnt/private-gdrive --vfs-cache-mode full --daemon` |
| Reauthorize | `rclone config reconnect "${R}:"` |

Disallowed by this skill (refuse and redirect to `gdrive-cli`):

- `rclone backend drives "${R}:"` — Shared Drives.
- Any command with `--drive-shared-with-me`.
- Any command with `--drive-team-drive`.
- Any command targeting a remote name other than `${R}:`.

## Common Workflows

### Quota sanity check

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"
rclone about "${R}:"
```

### Upload one file or a folder

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"
rclone copy ~/report.pdf "${R}:Reports/" -P

rclone copy ~/project "${R}:Backups/project" \
  --exclude ".git/**" --exclude "node_modules/**" -P
```

`copy` is non-destructive — it never deletes on the destination. No extra
confirmation needed.

### Download

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"
rclone copy "${R}:Reports/report.pdf" ~/Downloads/ -P
```

### Mirror a local folder to the private Drive (DESTRUCTIVE)

Always two steps:

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"

# 1. Dry-run, show output to user
rclone sync ~/project "${R}:Backups/project" --dry-run -v

# 2. After explicit user OK, real run with safety net
rclone sync ~/project "${R}:Backups/project" \
  --backup-dir "${R}:Backups/_versions/$(date +%Y-%m-%d)" \
  --max-delete 100 \
  -P
```

### Export Google Docs / Sheets / Slides

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"
rclone copy "${R}:Notes" ~/local/notes \
  --drive-export-formats "md,csv,pdf" -P
```

### Trash management

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"

rclone ls "${R}:" --drive-trashed-only
rclone backend untrash "${R}:path/to/file"

# Empty trash (PERMANENT) — confirm with user first
rclone backend drop "${R}:" --dry-run
rclone backend drop "${R}:"
```

### Mount

```bash
R="${GDRIVE_PRIVATE_REMOTE:-gdrive-private}"
mkdir -p ~/mnt/private-gdrive
rclone mount "${R}:" ~/mnt/private-gdrive --vfs-cache-mode full --daemon
```

## Error Handling

Inherits everything from `gdrive-cli`'s error table. Two private-skill
specific cases:

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pinned remote missing | Never set up | Run setup above, or export `GDRIVE_PRIVATE_REMOTE` |
| `rclone about ${R}:` returns Workspace-style limits | Pinned remote is a Workspace account | Reconfigure with personal Gmail, or use `gdrive-cli` instead |

## Behavior Scenarios

```gherkin
Scenario: Resolve pinned remote on first call
  Given GDRIVE_PRIVATE_REMOTE is unset and `gdrive-private:` exists in rclone config
  When the user asks for any private-Drive operation
  Then the skill resolves the pinned remote to `gdrive-private:` and proceeds

Scenario: Override via environment variable
  Given the user has exported GDRIVE_PRIVATE_REMOTE=personal and `personal:` exists
  When the user asks to upload a file to their private Drive
  Then the skill targets `personal:` and never `gdrive-private:` or any other remote

Scenario: Pinned remote not configured
  Given neither `gdrive-private:` nor `${GDRIVE_PRIVATE_REMOTE}:` exists in rclone config
  When the user asks any private-Drive operation
  Then the skill refuses the operation, lists existing remotes, and walks
       the user through `rclone config` with personal-Gmail-specific choices

Scenario: User references a different remote
  Given the user types something like "upload to tx-gdrive:Reports"
  When the skill is invoked
  Then it refuses, explains the private-only scope, and points to `gdrive-cli`

Scenario: User asks for a Shared Drive operation
  Given the user asks to list, copy from, or operate on a Shared/Team Drive
  When the skill is invoked
  Then it refuses, notes that Shared Drives are a Workspace feature, and
       points to `gdrive-cli`

Scenario: User asks for shared-with-me items
  Given the user asks for files others shared with them
  When the skill is invoked
  Then it refuses (those files are not in the user's own Drive) and points
       to `gdrive-cli` with `--drive-shared-with-me`

Scenario: Destructive sync with safety net
  Given the user asks to mirror a local folder to their private Drive
  When the skill runs
  Then it first runs `rclone sync ... --dry-run -v`, shows the plan, waits
       for explicit confirmation, and only then runs with `--backup-dir` and
       `--max-delete` set

Scenario: Setup answer "yes" to Shared Drive prompt
  Given the user is in `rclone config` and answers `y` to "Configure as Shared Drive?"
  When the skill is guiding setup
  Then it immediately flags the mistake, has them abort and re-run with `n`,
       and explains why Shared Drives defeat the private scope

Scenario: Pinned remote points at a Workspace account
  Given `gdrive-private:` is configured against an `@company.com` Workspace account
  When the user runs any operation
  Then the skill warns that the remote is not actually personal and offers
       to reconfigure or fall back to `gdrive-cli`
```

## References

- `references/scoped-commands.md` — Full command catalog with the pinned-remote
  variable substituted in, side-by-side with the disallowed flags so the
  refusal protocol is enforceable mechanically.
- The base `gdrive-cli` skill's `references/command-reference.md` — Deep
  rclone flag reference. Read it when this skill's own docs don't cover a
  flag.

## Retrospective

After completing the user's task, reflect on the session:

1. Consider: were there mid-session corrections (the user had to re-state the
   private scope, or a refusal turned out to be wrong)? Did the pinned-remote
   resolution misfire? Did setup hit an unexpected branch?
2. Ask the user (in Japanese):
   「今回のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user provides feedback OR if corrections/issues actually occurred:
   a. Resolve the skill's source dir via
      `git rev-parse --show-toplevel` then `/gdrive-private/feedback/`. Create
      the directory if it does not exist.
   b. Read `feedback/log.md` (create it with `# Feedback Log` header followed
      by a blank line and
      `<!-- Append new entries at the top. Do not edit previous entries. -->`
      if missing).
   c. Prepend a new entry directly after the header:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <frontmatter version>
      - **Task**: <brief task description>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Confirm in one short Japanese sentence.
4. If the user skips AND no corrections or issues occurred, end without
   recording.
