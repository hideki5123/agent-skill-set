---
name: my-gdrive
version: 1.0.1
description: >
  Operate ONLY the user's private (personal) Google Drive via `rclone`, scoped
  to a single pinned remote (default `my-gdrive:`, override with the
  `MY_GDRIVE_REMOTE` env var). A safety wrapper around the `gdrive-cli` skill:
  refuses other remotes (e.g., the user's work/Workspace `tx-gdrive:`),
  strips Shared Drive and shared-with-me paths, and walks first-time users
  through OAuth setup with a personal Gmail account — including how to add
  a *second* rclone remote alongside an existing company one. Use whenever
  the user wants to act on their *private* / *personal* Drive specifically —
  not their work or shared Drive. Trigger phrases include "my gdrive",
  "my-gdrive", "my google drive", "my private google drive", "personal
  google drive", "personal gdrive", "private google drive", "private gdrive",
  "my private drive", "my personal drive", "personal drive", "private drive",
  "upload to my drive", "download from my drive", "backup to my google drive",
  "list my drive", "search my drive", "my drive quota", "sync to my gdrive",
  "use my personal google drive", "use my private google drive", "/my-gdrive".
---

# My Google Drive Skill (Private / Personal)

A scoped wrapper around the `gdrive-cli` skill that operates **only on the
user's private (personal) Google Drive**. The remote is pinned to a single
name (default `my-gdrive:`); operations on any other remote — work,
Workspace, Shared Drive, "shared with me" — are refused and redirected to
the base `gdrive-cli` skill.

The underlying tool is still `rclone`; this skill adds (a) a single pinned
remote, (b) refusal of out-of-scope remotes and flags, and (c) a setup path
explicitly aimed at adding a personal Gmail remote *alongside* an existing
company / Workspace remote.

When the user wants the full Drive surface — multiple accounts, Shared
Drives, shared-with-me — use `gdrive-cli` instead.

## Constraints

- `rclone` must be installed (see Authentication).
- The remote name is **pinned**. Default: `my-gdrive`. Override per session
  by setting `MY_GDRIVE_REMOTE` (without trailing `:`) — for example
  `MY_GDRIVE_REMOTE=personal` makes `personal:` the pinned remote.
- The pinned remote must be a **personal Google account (`@gmail.com`)**,
  not a Google Workspace / corporate account. Workspace Drives carry Shared
  Drives and admin policies that defeat the "private" framing.
- **Out-of-scope, refused by this skill**:
  - Any remote name other than the pinned one (e.g., `tx-gdrive:`,
    `work-gdrive:`).
  - `--drive-shared-with-me` (those files don't live in *your* Drive).
  - `--drive-team-drive <ID>` and `rclone backend drives` (Shared Drives are
    a Workspace feature; private accounts don't have them).
  - Reconfiguring the remote as a Shared Drive.
  When the user asks for any of the above, refuse politely and recommend the
  base `gdrive-cli` skill.
- Destructive operations (`sync`, `move`, `delete`, `purge`,
  `backend drop`, `backend untrash`) follow the same `--dry-run` + confirm
  rules as `gdrive-cli`. The pinned-remote scoping does not relax that.

## Authentication: Add a Personal Remote Alongside an Existing Company One

This is the most common setup case for this skill: the user already has a
company / Workspace remote (e.g., `tx-gdrive:`) authorized in rclone, and now
wants a **separate** remote pointing at a personal `@gmail.com` account. You
do **not** edit or replace the company remote — you add a second one.

### Preflight

```bash
rclone version          # confirm install; on macOS: brew install rclone
rclone listremotes      # see what's already configured
```

If the user only has `tx-gdrive:` (or any company remote) and no `my-gdrive:`,
proceed with the steps below.

### The browser-OAuth gotcha (read this first)

When `rclone config` opens a browser to authorize the new remote, Google's
account picker will quietly default to **whichever Google account is already
signed in to that browser**. If the user is signed in to their company Gmail,
the new "personal" remote will end up pointing at the company Drive — which
is exactly the failure this skill is supposed to prevent.

Pick **one** of these strategies before you start `rclone config`:

1. **Best (recommended): Use a separate browser profile or incognito window.**
   - Chrome: `⋮` → New Incognito Window, or create a new profile.
   - Safari: File → New Private Window.
   - Firefox: File → New Private Window, or use a containers profile.
   In the new private window, sign in to the personal `@gmail.com` first,
   *then* run `rclone config`.

2. **Alternative: Sign out of the company Gmail in the default browser**
   before running setup. Go to gmail.com → click avatar → Sign out of all
   accounts. After setup, sign back in.

3. **If you have only one Gmail in the browser already and it's the personal
   one**: nothing extra to do — the picker will land on it.

If you do not pick a strategy, the picker will at minimum show a chooser
*if* multiple Google accounts are signed in. Pick the personal one
explicitly. Never click "Continue as <company>".

### Run rclone config

```bash
rclone config
```

Walk through these answers — every line matters:

| Prompt | Answer | Why |
|--------|--------|-----|
| `e/n/d/r/c/s/q>` | `n` (new remote) | Create a *second* remote; do not edit the existing one |
| `name>` | `my-gdrive` (or whatever `MY_GDRIVE_REMOTE` is set to) | Pin name |
| `Storage>` | type `drive` and Enter | Google Drive (NOT `google cloud storage`) |
| `client_id>` | (leave blank) | Use rclone's shared OAuth client; fine for personal use |
| `client_secret>` | (leave blank) | ditto |
| `scope>` | `1` (full) | Read+write. Use `2` (read-only) only for backup-only setups |
| `service_account_file>` | (leave blank) | Service accounts are Workspace-only |
| `Edit advanced config?` | `n` | No |
| `Use auto config?` | `y` | Opens the browser for OAuth |
| **(browser)** | **Sign in with the *personal* `@gmail.com` account.** Use the strategy from "The browser-OAuth gotcha" above to ensure the right account is picked. Click `Allow`. | This is where private vs company is actually decided |
| `Configure this as a Shared Drive (Team Drive)?` | `n` | **Always `n`.** If the user types `y`, abort and start over — Shared Drives put this skill out of scope |
| `Yes this is OK / Edit this remote / Delete this remote` | `y` (Yes this is OK) | Save |
| `e/n/d/r/c/s/q>` | `q` (quit) | Done |

### Verify the new remote points at the right account

```bash
rclone listremotes
# Expected: BOTH lines now appear:
#   tx-gdrive:
#   my-gdrive:

rclone about my-gdrive:
# Look at the "Total:" line. Personal Gmail accounts typically show ~15 GiB
# of total storage (or whatever Google One plan the user has). If you see
# Workspace-style limits (e.g., 2 TiB+ pooled), the wrong account got
# authorized — see "Recovery" below.
```

Cross-check by listing the root:

```bash
rclone lsd my-gdrive: | head
# Expected: personal folders (e.g., your own "Photos", "Family", etc.).
# If you see company folder names, the wrong account got authorized.
```

You can also visit https://myaccount.google.com/permissions while signed in
to the personal Gmail and confirm "rclone" appears in the authorized apps
list.

### Recovery: I authorized the wrong account

If `rclone about my-gdrive:` shows the company account:

```bash
# 1. Revoke rclone's access from the wrong account:
#    Visit https://myaccount.google.com/permissions while signed in
#    to that account, find "rclone", click "Remove Access".

# 2. Delete the misconfigured remote:
rclone config delete my-gdrive

# 3. Sign out of the wrong account in your browser, or use an incognito
#    window for the next try (see "The browser-OAuth gotcha").

# 4. Re-run `rclone config` and follow the steps above.
```

The existing `tx-gdrive:` (company) remote is untouched throughout.

### When the auth token later expires

Personal Drive remotes need to be reauthorized periodically (Google
expires refresh tokens after long inactivity, account password changes,
etc.):

```bash
rclone config reconnect my-gdrive:
```

Same browser strategy applies — make sure the personal Gmail is the one
the picker lands on.

## Resolving the Pinned Remote (preflight for every operation)

```bash
# 1. Resolve the pinned remote name
R="${MY_GDRIVE_REMOTE:-my-gdrive}"

# 2. Confirm it exists in rclone config
if ! rclone listremotes | grep -qx "${R}:"; then
  echo "Pinned private remote '${R}:' is not configured."
  echo "Run the Authentication walkthrough in this skill, or export"
  echo "MY_GDRIVE_REMOTE to match an existing personal-account remote in:"
  rclone listremotes
  exit 1
fi

# 3. Sanity-check it's reachable
rclone about "${R}:" >/dev/null 2>&1 || \
  { echo "Remote ${R}: is not reachable; run 'rclone config reconnect ${R}:'"; exit 1; }
```

After this, every command in the workflow uses `${R}:` and nothing else.

## Refusal Protocol

If the user's request would force the skill outside the pinned-private scope,
do not execute it. Respond with a short message of this shape:

> This skill is scoped to your private Google Drive (`<remote>:`) only.
> What you're asking — *<reason: other remote / Shared Drive /
> shared-with-me / Workspace account>* — is out of scope. For that, use the
> base `gdrive-cli` skill (which supports the full multi-account surface),
> or rerun with `MY_GDRIVE_REMOTE=<name>` if you want this skill pinned to a
> different *personal* remote.

Concrete triggers for refusal:

| Request | Why refused | Redirect |
|---------|-------------|----------|
| User names another remote (`tx-gdrive:`, `work:`) | Out of scope | `gdrive-cli` |
| `--drive-shared-with-me` | Not in user's own Drive | `gdrive-cli` |
| `--drive-team-drive <ID>` / `rclone backend drives` | Shared Drives are Workspace-only | `gdrive-cli` |
| "Reconfigure as Shared Drive" during setup | Defeats private scope | `gdrive-cli` setup |
| Pinned remote points at a Workspace account | Mismatch with "private" framing | Reconfigure (see Recovery) or `gdrive-cli` |

## Inherited Surface

Everything the base `gdrive-cli` skill does — list, upload, download, search,
sync (with safety), export Google Workspace files, mount, trash management,
share links, bandwidth control — is available here, **with every command
substituting the pinned remote** for the example `gdrive:` placeholder.

For the full command catalog (with the substitution applied), read
`references/scoped-commands.md`.

For deeper rclone flag reference, read the base `gdrive-cli` skill's
`references/command-reference.md`.

## Quick Reference (pinned-remote form)

Assume `R="${MY_GDRIVE_REMOTE:-my-gdrive}"` is exported.

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
| Mount | `rclone mount "${R}:" ~/mnt/my-gdrive --vfs-cache-mode full --daemon` |
| Reauthorize | `rclone config reconnect "${R}:"` |

Disallowed by this skill (refuse and redirect to `gdrive-cli`):

- `rclone backend drives "${R}:"` — Shared Drives.
- Any command with `--drive-shared-with-me`.
- Any command with `--drive-team-drive`.
- Any command targeting a remote name other than `${R}:`.

## Common Workflows

### Quota sanity check

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
rclone about "${R}:"
```

### Upload one file or a folder

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
rclone copy ~/report.pdf "${R}:Reports/" -P

rclone copy ~/project "${R}:Backups/project" \
  --exclude ".git/**" --exclude "node_modules/**" -P
```

`copy` is non-destructive — it never deletes on the destination. No extra
confirmation needed.

### Download

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
rclone copy "${R}:Reports/report.pdf" ~/Downloads/ -P
```

### Mirror a local folder to the private Drive (DESTRUCTIVE)

Always two steps:

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"

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
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
rclone copy "${R}:Notes" ~/local/notes \
  --drive-export-formats "md,csv,pdf" -P
```

### Trash management

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"

rclone ls "${R}:" --drive-trashed-only
rclone backend untrash "${R}:path/to/file"

# Empty trash (PERMANENT) — confirm with user first
rclone backend drop "${R}:" --dry-run
rclone backend drop "${R}:"
```

### Mount

```bash
R="${MY_GDRIVE_REMOTE:-my-gdrive}"
mkdir -p ~/mnt/my-gdrive
rclone mount "${R}:" ~/mnt/my-gdrive --vfs-cache-mode full --daemon
```

## Error Handling

Inherits everything from `gdrive-cli`'s error table. Skill-specific cases:

| Symptom | Cause | Fix |
|---------|-------|-----|
| Pinned remote missing | Never set up | Run the Authentication walkthrough above, or export `MY_GDRIVE_REMOTE` |
| `rclone about ${R}:` shows ~15 GiB total | Personal account ✓ | All good |
| `rclone about ${R}:` shows Workspace-style pooled limits (TiB+) | Wrong account got authorized | Recovery section above (revoke, `rclone config delete`, retry in incognito) |
| `Failed to get oauth token` after weeks of working | Expired refresh token | `rclone config reconnect ${R}:` (same browser strategy) |
| OAuth browser opens but auto-picks company Gmail | Default browser profile signed into company | Use incognito/private window or sign out of company first |

## Behavior Scenarios

```gherkin
Scenario: Resolve pinned remote on first call
  Given MY_GDRIVE_REMOTE is unset and `my-gdrive:` exists in rclone config
  When the user asks for any private-Drive operation
  Then the skill resolves the pinned remote to `my-gdrive:` and proceeds

Scenario: Override via environment variable
  Given the user has exported MY_GDRIVE_REMOTE=personal and `personal:` exists
  When the user asks to upload a file to their private Drive
  Then the skill targets `personal:` and never `my-gdrive:` or any other remote

Scenario: First-time setup alongside an existing company remote
  Given rclone is installed and `tx-gdrive:` (company) is the only configured remote
  When the user asks to "set up my private google drive" or runs any private op
  Then the skill walks through `rclone config` to ADD a new `my-gdrive:` remote
       without touching `tx-gdrive:`, warns about the browser-OAuth gotcha
       (account picker defaulting to the already-signed-in company Gmail),
       and verifies the result with `rclone about my-gdrive:` and a root listing

Scenario: Wrong account got authorized during setup
  Given the user finished `rclone config` but `rclone about my-gdrive:` shows
        Workspace-style storage limits or company folders appear in the root
  When the skill detects the mismatch (or the user reports it)
  Then it walks through Recovery: revoke rclone access at
       myaccount.google.com/permissions, `rclone config delete my-gdrive`,
       retry in an incognito window with the personal Gmail signed in

Scenario: Pinned remote not configured
  Given neither `my-gdrive:` nor `${MY_GDRIVE_REMOTE}:` exists in rclone config
  When the user asks any private-Drive operation
  Then the skill refuses the operation, lists existing remotes, and runs the
       Authentication walkthrough (which adds a new remote without touching
       any existing ones)

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

Scenario: Reauthorize after token expiry
  Given `my-gdrive:` was working but now returns "Failed to get oauth token"
  When the user runs an operation
  Then the skill instructs `rclone config reconnect my-gdrive:` and reminds
       the user to use incognito / sign-out so the personal Gmail is picked
```

## References

- `references/scoped-commands.md` — Full command catalog with the
  pinned-remote variable substituted in, side-by-side with the disallowed
  flags so the refusal protocol is enforceable mechanically.
- The base `gdrive-cli` skill's `references/command-reference.md` — Deep
  rclone flag reference. Read it when this skill's own docs don't cover a
  flag.

## Retrospective

After completing the user's task, reflect on the session:

1. Consider: were there mid-session corrections (the user had to re-state the
   private scope, or a refusal turned out to be wrong)? Did the pinned-remote
   resolution misfire? Did the OAuth setup land on the wrong account?
2. Ask the user (in Japanese):
   「今回のフィードバック (1-5の評価、気になった点、または何もなければEnter)」
3. If the user provides feedback OR if corrections/issues actually occurred:
   a. Resolve the skill's source dir via
      `git rev-parse --show-toplevel` then `/my-gdrive/feedback/`. Create
      the directory if it does not exist.
   b. Read `feedback/log.md` (create it with `# Feedback Log` header
      followed by a blank line and
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
