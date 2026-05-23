# Report Template

Use this exact format for the consolidated review report.

```markdown
# Local Review Report

**Date**: YYYY-MM-DD HH:mm
**Scope**: All changes | Staged only
**Perspectives**: [list of perspectives that reviewed]
**Files reviewed**: N

## Summary

| Severity | Count |
|----------|-------|
| Critical | X |
| Important | Y |
| Nice-to-have | Z |

## Critical Findings

### [C1] file:line — Summary of finding
**Perspective(s)**: Architecture, Security
**Details**: Description of the issue, why it's critical, and what to do about it.

### [C2] file:line — Summary of finding
...

## Important Findings

### [I1] file:line — Summary of finding
**Perspective(s)**: QA/QC
**Details**: Description and recommendation.

...

## Nice-to-have

### [N1] file:line — Summary of finding
**Perspective(s)**: Devil's Advocate
**Details**: Suggestion for future improvement.

...
```

## Numbering

- Critical findings: `[C1]`, `[C2]`, `[C3]`, ...
- Important findings: `[I1]`, `[I2]`, `[I3]`, ...
- Nice-to-have findings: `[N1]`, `[N2]`, `[N3]`, ...

## When Writing to File

If `--file` is set, write the report to `review-local-YYYY-MM-DD-HHmm.md` in the current working directory. Confirm the file path to the user after writing.

## Empty Sections

If a severity level has zero findings, include the section header with "No findings." underneath. This confirms the team reviewed for issues at that severity and found none.
