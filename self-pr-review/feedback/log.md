# Feedback Log

<!-- Append new entries at the top. Do not edit previous entries. -->

## 2026-06-24T00:00:00+09:00
- **Skill Version**: 1.1.0 → 1.3.0 (skill-improvement, not a review run; 1.2.0 was taken by the concurrent auto-resolve feature)
- **Task**: User reported "output is wrong" across summary counts, GitHub replies, and mid-run behavior. Audited against the two prior feedback entries.
- **Outcome**: fixed — root cause was the Copilot login mismatch documented on 2026-06-13. All read-side jq filters (Step 2 already-reviewed check, Step 3 polling, Step 4 fetch + follow-up, and the matching recipes in `references/gh-comment-api.md`) now match BOTH `Copilot` and `copilot-pull-request-reviewer[bot]`; request/re-request calls still use the `[bot]` handle. Also fixed the worktree branch-divergence issue from 2026-06-14 (Step 1 resolves `REMOTE`/`REMOTE_BRANCH` from `@{u}` and uses `gh pr list --head`; Step 6 pushes `HEAD:$REMOTE_BRANCH`), and documented the blocked-foreground-`sleep` constraint (run poll loop via `run_in_background`). Relocated this feedback log from the gitignored generated artifact into the source skill so it survives reinstalls.
- **Rating**: —
- **Rating reason**: —
- **Corrections**: none
- **Issues**: The two prior entries had identified all root causes but the fixes were never applied to the skill source — the lesson sat only in the log. Reinforces keeping `feedback/log.md` in source (not in the generated copy) and acting on logged issues promptly.
- **User Note**: —
---

## 2026-06-14T00:00:00+09:00
- **Skill Version**: 1.1.0
- **Task**: Self-review loop on PR #809 (OperatorApp macOS build config), one review round, run as forked subagent
- **Outcome**: success — 8 comments (1 Gemini, 7 Copilot), all auto-applied, committed (57bc80fd3), pushed, all 8 replied
- **Rating**: —
- **Rating reason**: —
- **Corrections**: (1) Step 1 `gh pr view` by branch returned "no PR" because the worktree's local branch name (`worktree-operator-osx-build`) differs from the PR head branch; the PR (#809) existed and was only found when `gh pr create` errored with the existing-PR URL. (2) Step 6 bare `git push` was rejected because local branch name != upstream remote branch name (`hideki/feat/operatorapp-macos-cloud-build`); had to push explicitly via `git push origin HEAD:<remote-branch>`.
- **Issues**: In a git worktree the local branch name often diverges from the PR head ref. Two spots assume they match: (a) resolving the PR via `gh pr view` on the current branch, and (b) `git push` with no args. Suggest: resolve the upstream/remote branch up front (`git rev-parse --abbrev-ref @{u}` -> strip `origin/`) and use that for both PR lookup (`gh pr list --head <remote-branch>`) and push (`git push origin HEAD:<remote-branch>`). Also confirmed Copilot login is `Copilot` (matched both, per prior entry — worked).
- **User Note**: —
---

## 2026-06-13T00:00:00+09:00
- **Skill Version**: 1.1.0
- **Task**: Self-review loop on PR #1787, one review round
- **Outcome**: success
- **Rating**: —
- **Rating reason**: —
- **Corrections**: none
- **Issues**: Copilot posts line review comments with `user.login == "Copilot"`, not `"copilot-pull-request-reviewer[bot]"` — the skill's documented jq filter in Step 4 and references/gh-comment-api.md silently dropped Copilot's comment; only caught by cross-checking the unfiltered comment list. Same mismatch in the polling jq (pending reviewer login is `Copilot`). Filters should match both logins. Also: foreground polling with `sleep` is blocked by the Bash tool; had to run the poll loop via run_in_background.
- **User Note**: —
---
