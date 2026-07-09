Sync this project's skills locally (Claude marketplace + Codex) and to one or more SSH hosts.

Source of truth lives in each `<skill>/SKILL.md` at the repo root. The materialized plugin tree under `my-marketplace/plugins/*/skills/*` and the Codex tree under `~/.codex/` are generated artifacts. This command keeps both in lockstep across machines.

## What $ARGUMENTS means

`$ARGUMENTS` is interpreted left-to-right as a mix of flags and host targets. Anything starting with `--` is a flag; everything else is an SSH host alias (resolved against the user's `~/.ssh/config` — key-based auth is assumed).

Supported flags:

- `--local` — run the local sync only; skip every remote host. This is the default when no hosts are given AND `--all` is not set.
- `--all` — read targets from `.claude/sync-targets` (see "Target file format" below) and sync to every one.
- `--validate` — pass `--validate` through to `sync_skills.py` on every leg (no writes; exits non-zero on drift). Use for CI-style drift checks.
- `--dry-run` — pass `-n` to `rsync` and `--validate` to remote `sync_skills.py`. Show what would change without writing on remote. Local leg still runs normally unless combined with `--validate`.
- `--skills <name> [<name> ...]` — pass through to `sync_skills.py --skills` so only the named skills are synced. Forwarded to remote legs too.
- `--no-local` — skip the local sync entirely and only push to remote hosts. Useful if the local tree is already in sync and you just want to fan out.

Anything else is taken as an SSH host. Example invocations:

```
/sync-skills                          # local only
/sync-skills --all                    # local + every host in .claude/sync-targets
/sync-skills work-laptop beefy-dev    # local + two ad-hoc hosts
/sync-skills --validate --all         # drift check everywhere
/sync-skills --skills agents-init dev-workflow work-laptop
/sync-skills --no-local --all         # fan out without re-syncing local
```

## Workflow

### 1. Parse `$ARGUMENTS` and confirm the plan

Split `$ARGUMENTS` into flags and hosts. Resolve the host set:

- If `--all` is set, read `.claude/sync-targets` (relative to the repo root, resolved via `git rev-parse --show-toplevel`). Skip blank lines and lines starting with `#`. Each non-comment line is `<host>[:<remote-path>]`.
- If explicit hosts are passed on the command line, those win — **explicit hosts override `--all`** to avoid surprising fan-out.
- If neither hosts nor `--all`, treat as local-only.

Print a one-screen plan summarizing:

- Whether the local leg will run (yes unless `--no-local`)
- The list of remote hosts and their resolved remote paths
- The flags being forwarded (`--validate`, `--dry-run`, `--skills ...`)

For runs that touch more than one host and are **not** `--dry-run` or `--validate`, pause and confirm before proceeding. For a single-host run or any `--dry-run`/`--validate` run, just proceed.

### 2. Verify preconditions

Before any sync:

- `python3 --version` must succeed locally (the sync scripts target Python 3).
- Resolve the repo root via `git rev-parse --show-toplevel` and use that for every path in this command. Do **not** hardcode absolute paths.
- For each remote leg: `ssh -o BatchMode=yes -o ConnectTimeout=5 <host> true` should succeed. If a host fails, surface the failure and ask whether to skip it or abort the whole run.

### 3. Run the local sync (unless `--no-local`)

From the repo root:

```bash
python3 scripts/sync_skills.py [--validate] [--skills <name> ...]
```

Stream the output. On non-zero exit, **stop the whole run** — do not push a broken local tree to remote machines.

After the local leg succeeds, Claude Code's installed cache at `~/.claude/plugins/cache/hideki-plugins/<plugin>/<version>/` is only refreshed when the user runs `/plugin update <plugin>@hideki-plugins` from a Claude Code session. This command cannot trigger that slash command for them — just call it out in the final summary so they know.

### 4. For each remote host: push the source tree

Resolve the remote path for each host:

1. If the host entry in `.claude/sync-targets` had `:<path>`, use that.
2. Else, default to `~/private/repos/agent-skill-set`. The user can override per-host in the config file.

Run rsync from the repo root. The `--filter=:- .gitignore` flag makes rsync honor the project's `.gitignore`, so generated junk (`node_modules/`, `deno.lock`, materialized plugin trees under `my-marketplace/plugins/*/skills/*`, etc.) stays local:

```bash
rsync -avz --delete \
  --filter=':- .gitignore' \
  --exclude='.git' \
  --exclude='.claude/worktrees/' \
  --exclude='node_modules/' \
  [-n if --dry-run] \
  ./ \
  "<host>:<remote-path>/"
```

Notes:

- `--delete` is intentional — the remote tree must mirror local exactly. If a remote host has uncommitted experimental skills you want to preserve, do not run this command against it.
- `--exclude='.git'` has **no trailing slash** — this is deliberate, not a typo. A trailing slash (`.git/`) matches only *directories* named `.git`. In a normal checkout `.git` is a directory, but if this command is ever run **from inside a git worktree** (e.g. `.claude/worktrees/<name>/`), the worktree's `.git` is a plain *file* containing a `gitdir:` pointer back to the main checkout's `.git/worktrees/<name>` path on the local machine. A directory-only exclude does not match that file, so rsync ships it — and with `--delete`, it silently overwrites the remote's real `.git` directory with a broken pointer to a path that only exists on the machine that ran the sync, corrupting the remote repo. The unslashed form matches `.git` whether it's a file or a directory, at any depth (this also correctly protects submodule checkouts, e.g. `multi-agent-council/.git`, which are files for the same reason). We ship source state, not history — the remote can `git fetch` separately if it needs history.
- Prefer running this command from the **main checkout**, not a worktree, when syncing to remote hosts. The exclude fix above makes a worktree-sourced run safe either way, but running from the main checkout avoids relying on that fix.
- `.claude/worktrees/` is excluded because those are per-machine ephemeral worktrees.

### 5. For each remote host: re-materialize the marketplace

After rsync finishes for a host, run the sync script on that host in the same shell session:

```bash
ssh <host> "cd <remote-path> && python3 scripts/sync_skills.py [--validate] [--skills <name> ...]"
```

Stream the remote output. If a remote leg fails, **record the failure and continue** to the next host — do not abort the whole fan-out because of one bad host. Collect all failures and surface them in the final summary.

### 6. Summarize

End with a compact report:

- Local leg: `sync_skills.py` exit status and which skills it touched (read from its stdout).
- Per host: rsync transfer summary (files changed) + remote `sync_skills.py` result.
- If any remote needs first-time marketplace registration, point the user at "Remote prerequisites" below.
- Reminder about `/plugin update <plugin>@hideki-plugins` if they want the local cache bumped now.

## Target file format

`.claude/sync-targets` is a plain-text file, one host per line:

```
# Comments and blank lines are ignored
work-laptop
beefy-dev:~/code/agent-skill-set
ci-runner:/srv/agent-skill-set
```

If a line has no `:<path>`, the default `~/private/repos/agent-skill-set` is used.

The file is checked into the repo as `.claude/sync-targets`. If it does not exist when `--all` is requested, treat that as a user error: print a one-paragraph hint showing the format above and exit cleanly without syncing.

## Remote prerequisites (one-time per host)

This command does not bootstrap a remote's Claude Code marketplace registration. Each remote needs, once:

1. The repo cloned at the configured `<remote-path>`.
2. Python 3 available on `PATH`.
3. (Only if the remote will actually use the skills from Claude Code) the marketplace registered: from a Claude Code session on the remote, run `/plugin marketplace add <remote-path>/my-marketplace`, then `/plugin install <plugin>@hideki-plugins` for the plugins they want.

If preflight detects the repo missing on a remote, surface that as the failure and stop for that host — do **not** try to `git clone` from this command. Cloning has credential implications that belong to the user.

## Edge cases and guardrails

- **Uncommitted local changes**: Fine — the goal is to ship the working tree, not just committed history. The summary should include `git status --short` output so the user sees what they pushed.
- **Different OS on remote**: `sync_skills.py` is pure Python 3 and POSIX-pathed, so Linux ↔ macOS works. Windows remotes will fail on `~/.codex/` symlink semantics; do not target Windows hosts from this command.
- **Host alias collisions**: If a host appears in both `$ARGUMENTS` and `.claude/sync-targets`, sync it once (de-dupe by host string).
- **Partial failure**: The local leg is a hard precondition — if it fails, abort. Each remote leg is independent — log failures, continue, report at the end.
- **Network flake**: Do not retry automatically. Surface the rsync/ssh error and let the user re-invoke `/sync-skills <host>` for the failed host.

Now do the work for: $ARGUMENTS
