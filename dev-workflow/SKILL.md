---
name: dev-workflow
description: >
  Create an agent team to explore this from different angles: one teammate on architecture, one on security, one considering edge device resource, one playing devil's advocate and any other team mate who need to be on this task.
  End-to-end development workflow: plan, implement, commit, and optionally PR.
  Use when the user asks to implement a feature, fix a bug, refactor code, or any multi-step development task. Triggers on requests like "implement X", "build Y", "add feature Z", "fix bug", "refactor", or when the user invokes /dev-workflow.
  Orchestrates: branch creation, plan-mode iteration, team-based implementation, self-review, structured commits (conventional commits), and optional PR creation using the repo's PR template.
---

# Dev Workflow

End-to-end development workflow from planning through PR creation.

## Arguments

Parse these from the user's invocation. All are optional with defaults:

| Argument | Default | Description |
|----------|---------|-------------|
| `--base-branch` | repo default branch (e.g. `develop`) | Branch to create feature branch from |
| `--branch` | auto-generated from task description | Feature branch name |
| `--pr` | `false` | Create a PR after commits |
| `--skip-approval` | `false` | Skip owner approval step after implementation |
| `--team` | `true` | Use multi-agent team for implementation |

## Workflow

### Phase 1: Setup

1. Detect the repo's default branch via `git remote show origin | grep 'HEAD branch'` or fall back to `develop`/`main`
2. Use `--base-branch` if provided, otherwise use the default branch
3. Create a new branch: `git checkout -b <branch-name> <base-branch>`
   - If `--branch` not provided, derive from task description (e.g. `tim/feature-description`)

### Phase 2: Plan

1. Enter plan mode with `EnterPlanMode`
2. Explore the codebase to understand the scope
3. Write a clear implementation plan
4. Present the plan via `ExitPlanMode` for user approval
5. If rejected, iterate on the plan until approved

### Phase 3: Implement

If `--team` is enabled:
1. Create a team with `TeamCreate` to parallelize independent work
2. Spawn teammates as needed for the task
3. Coordinate implementation across teammates
4. Self-review: each teammate reviews their own work, then cross-review with the team
5. Resolve all review comments before proceeding

If `--team` is disabled:
1. Implement the plan directly
2. Run build and tests to verify
3. Self-review: re-read all changes and verify correctness

### Phase 4: Approval (skippable with `--skip-approval`)

1. Present a summary of all changes to the user
2. Wait for user approval
3. If rejected, iterate on changes

### Phase 5: Commit

Create focused, reviewable commits. See [references/commit-guide.md](references/commit-guide.md) for conventions.

Key rules:
- One logical change per commit
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`, `ci:`
- Keep messages short and lowercase after prefix
- Never add `Co-Authored-By` or other author attribution
- Never add verbose descriptions - the diff speaks for itself
- Stash all changes, then restore and commit file groups one at a time for clean separation

### Phase 6: PR (optional, `--pr` flag)

Only when `--pr` is enabled:

1. Push the branch: `git push -u origin <branch-name>`
2. Detect and use the repo's PR template. See [references/pr-guide.md](references/pr-guide.md).
3. Create PR with `gh pr create`
4. Return the PR URL to the user
