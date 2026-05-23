# State Matrix — agents-init

**WHEN TO READ:** only when you encounter an unfamiliar edge case or want to verify a branch's intended behavior. Routine `/agents-init` invocations should not load this file — the table in SKILL.md is sufficient for the happy paths.

## Detection inputs

The script inspects:

- Does `./CLAUDE.md` exist? Is it a symlink (`Path.is_symlink()`)?
- If symlink, what is the literal target (`os.readlink`)?
- Does `./AGENTS.md` exist as a regular file?
- If both exist as files, are they byte-identical (`filecmp.cmp(..., shallow=False)`)?
- Platform: `sys.platform` → `linux`, `darwin`, `win32`.

Note: a "real file" means `is_file() and not is_symlink()`. A symlink pointing at a file does not count as `claude_real_file`.

## States and their semantics

| State | Trigger condition | LLM response |
| --- | --- | --- |
| `needs-init` | Neither CLAUDE.md nor AGENTS.md exists. | Invoke `/init` to populate CLAUDE.md, then run `--wire`. |
| `ready-claude` | Only CLAUDE.md exists (real file). | Ask user to confirm; on yes, `--wire`. Do NOT re-run `/init` — the user already has content. |
| `ready-agents` | Only AGENTS.md exists. | Run `--wire` (just adds the symlink, no confirmation needed). |
| `identical` | Both files exist, byte-identical. | Run `--wire`; script removes the duplicate CLAUDE.md and symlinks. |
| `conflict` | Both files exist, different content. | Diff is printed to stderr by `--detect`. Show it, ask the user, then `--wire --prefer=agents` or `--wire --prefer=claude`. |
| `wired` | CLAUDE.md is a symlink whose target is `AGENTS.md` (or `./AGENTS.md`), and AGENTS.md exists. | No-op. |
| `foreign-symlink` | CLAUDE.md is a symlink whose target is anything else (or whose target is `AGENTS.md` but AGENTS.md does not exist — a dangling link). | STOP. Show target. Ask before repointing. On confirm, `--wire --force`. |

## Conflict resolution semantics

- `--wire --prefer=agents`: deletes CLAUDE.md, keeps AGENTS.md untouched, then symlinks CLAUDE.md → AGENTS.md.
- `--wire --prefer=claude`: backs up the displaced AGENTS.md to `AGENTS.md.bak.<unix-ts>` (never deleted by the script), renames CLAUDE.md → AGENTS.md, then symlinks. The user can `diff AGENTS.md AGENTS.md.bak.*` afterwards and `rm` when satisfied.

## Platform notes

- **Linux / macOS**: real symlink, relative target (`AGENTS.md` not an absolute path), so the repo stays portable across clones.
- **Windows**: file copy via `shutil.copyfile`. The script's stdout `actions` list includes `WARNING: file copy used; re-run /agents-init after edits to AGENTS.md`. The skill body must surface that warning. Drift is on the user to manage by re-running the skill after every AGENTS.md edit.

## Safety properties (enforced by the script)

- Operates only on `./CLAUDE.md` and `./AGENTS.md` in the script's cwd — never recurses, never touches anything else.
- Atomic renames via `os.replace` (atomic on POSIX).
- Refuses to run outside a git repo. Override with `--allow-non-git` if the user explicitly asks (e.g. for testing).
- Warns (but does not fail) when either file matches a top-level entry in `.gitignore` (`CLAUDE.md` or `/CLAUDE.md`, same for AGENTS.md).
- Does NOT modify `.gitignore`. Does NOT commit. Does NOT push. Does NOT prompt interactively — those concerns belong to the LLM via `AskUserQuestion`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success (or `--detect` always succeeds with 0). |
| 2 | `--wire` called when state is `needs-init` — caller must run `/init` first. |
| 3 | `--wire` called when state is `conflict` and `--prefer` was not passed. |
| 4 | `--wire` called when state is `foreign-symlink` and `--force` was not passed. |
| 5 | Invalid `--prefer` value. |
| 10 | Not a git repo and `--allow-non-git` was not passed. |
