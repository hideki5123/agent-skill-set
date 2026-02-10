# Commit Guide

## Conventional Commit Format

```
<type>: <short description>
```

### Types

| Type | When to use |
|------|------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `chore` | Maintenance (deps, config, cleanup) |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `ci` | CI/CD pipeline changes |

### Rules

- Lowercase after prefix
- No period at end
- Max ~72 chars for first line
- If a body is needed, add a blank line then a brief explanation
- Never add `Co-Authored-By` lines
- Never add long descriptions when the diff is self-explanatory

### Creating Reviewable Commits

Strategy for splitting changes into focused commits:

1. `git stash` all uncommitted changes
2. For each logical group:
   a. `git checkout stash -- <file(s)>` to restore specific files
   b. If a file has multiple logical changes, apply edits manually then stage
   c. `git add <file(s)>` and `git commit`
3. `git stash drop` when done

Logical grouping examples:
- Config/env changes → one commit
- New dependency + its usage code → one commit
- Cleanup/removal of dead code → one commit
- New endpoint/feature → one commit
- CI changes → one commit
- CD changes → one commit
- Test changes → one commit

### Commit Message via HEREDOC

Always use HEREDOC for commit messages to handle special characters:

```bash
git commit -m "$(cat <<'EOF'
feat: add health check endpoint
EOF
)"
```

For multi-line messages:

```bash
git commit -m "$(cat <<'EOF'
feat: add health check endpoint

Adds /healthz for liveness probes and configures Blazor circuit retention.
EOF
)"
```
