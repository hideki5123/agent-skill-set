# Risk Decision Protocol

Well-Architected reviews rarely end with "everything passes." The deliverable
is **explicit risk acceptance**, recorded in the risk register so future
readers can see what was knowingly accepted and why.

## When to prompt

| Severity | Behavior |
|----------|----------|
| Critical | Always prompt via `AskUserQuestion` |
| Important | Always prompt via `AskUserQuestion` |
| Nice-to-have | List in the report only — do not prompt (would be too noisy) |

## How to prompt

Use the `AskUserQuestion` tool. It accepts up to 4 questions per call, so
batch findings into groups of 4 (last batch may have fewer).

### Question shape

For each finding:

- `header`: the finding ID, up to 12 chars (e.g. `C-C1`, `C-I3`)
- `question`: `[severity] file:line — one-sentence summary of the risk`
- `multiSelect`: `false`
- `options` (exactly 4):

| Label | Description shown to the user |
|-------|-------------------------------|
| Mitigate (Recommended) | Fix this before merge / deploy. |
| Defer | Acknowledge now, track as a follow-up (issue or TODO). |
| Accept | Acknowledge the risk as-is; record rationale. |
| Block | Treat this as a hard stop — the change should not proceed. |

The "Recommended" label goes on whichever option the analysis suggests is
the right default for that finding (typically Mitigate for Critical, Defer
or Mitigate for Important). Place the recommended option first.

The user can also type a free-text "Other" response — capture that as the
rationale.

## Capturing the decision

For every prompted finding, record into the risk register:

| Field | Source |
|-------|--------|
| ID | The finding ID (`C-C1`, ...) |
| Severity | Critical / Important |
| Finding | `file:line — summary` (and short detail) |
| User Decision | One of Mitigate / Defer / Accept / Block / Other |
| Rationale | Any free-text the user added, or the standard rationale for the chosen option |
| Owner / Follow-up | Owner name, issue link, or TODO marker if Defer / Mitigate; blank if Accept / Block |

If the user picks **Other**, treat the free-text as both the decision and the
rationale, and ask a short follow-up only if it is unclear which of the 4
standard buckets it maps to.

## Verdict rules

After every Critical and Important finding has a decision, compute the
overall verdict:

- **Hold** — if any finding has decision `Block`.
- **Proceed with caveats** — if no `Block`, but at least one `Accept` or
  `Defer`.
- **Proceed** — all findings are `Mitigate` (i.e. will be fixed) or there
  are no Critical / Important findings at all.

Render the verdict at the top of the report's Executive Summary and again at
the bottom.

## Skipping the loop

If the user explicitly says "skip risk prompts", do not call
`AskUserQuestion`. Instead render the report with all decisions set to
`(no decision)` and the verdict as `Proceed with caveats — undecided`. This
is a degraded mode; warn the user once.
