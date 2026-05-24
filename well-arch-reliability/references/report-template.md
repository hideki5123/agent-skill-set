# Reliability Review Report Template

Use this exact format for the Well-Architected Reliability review report.

```markdown
# Well-Architected Reliability Review
**Date**: YYYY-MM-DD HH:mm
**Mode**: git diff | architecture doc <path>
**Scope**: All changes | Staged only | Document
**Files / sections reviewed**: N
**Overall Verdict**: Proceed | Proceed with caveats | Hold

## Executive Summary

[2-3 sentences: current reliability posture, top risks the user accepted or
deferred, and the overall verdict with the dominant reason.]

## Pillar Analysis

### 1. Reliability Goals Aligned to UX
[Assessment per the guide. If no concerns, write "No concerns identified."]

### 2. Realistic Recovery Targets
[...]

### 3. High Availability via Redundancy
[...]

### 4. Horizontal Scalability
[...]

### 5. Observability for Failure Detection
[...]

### 6. Graceful Degradation
[...]

### 7. Tested Recovery
[...]

### 8. Incident Postmortems
[...]

## Risk Register

| ID | Severity | Finding (file:line — summary) | User Decision | Rationale | Owner / Follow-up |
|----|----------|-------------------------------|---------------|-----------|-------------------|
| R-C1 | Critical | infra/db.tf:14 — Single-zone primary DB | Mitigate | Will add zonal replica before launch | @bob / #2102 |
| R-I1 | Important | services/api/retry.go:33 — Unbounded retry | Defer | Tracking for next sprint | TODO(reliability) |

If there are no Critical or Important findings, write "No risks requiring
explicit decision." instead of an empty table.

## Nice-to-have (informational, not prompted)

- [R-N1] file:line — short note
- [R-N2] ...

If none: "No nice-to-have findings."

## Overall Verdict

**Proceed** — all Critical and Important findings will be mitigated.
**Proceed with caveats** — N risks Accepted, M Deferred. See register.
**Hold** — risk R-C1 was Blocked; resolve before proceeding.
```

## Numbering

- Critical: `R-C1`, `R-C2`, ...
- Important: `R-I1`, `R-I2`, ...
- Nice-to-have: `R-N1`, `R-N2`, ...

## Empty principles

If a principle has nothing to flag, keep the section header with "No
concerns identified." underneath. This proves the principle was reviewed
rather than skipped.

## When writing to file

If `--file` is set, write the report to `well-arch-reliability-YYYY-MM-DD-HHmm.md`
in the current working directory. Confirm the file path to the user after
writing.
