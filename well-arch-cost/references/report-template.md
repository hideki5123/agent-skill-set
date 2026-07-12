# Cost Optimization Review Report Template

Use this exact format for the Well-Architected Cost Optimization review
report.

```markdown
# Well-Architected Cost Optimization Review
**Date**: YYYY-MM-DD HH:mm
**Mode**: git diff | architecture doc <path>
**Scope**: All changes | Staged only | Document
**Files / sections reviewed**: N
**Overall Verdict**: Proceed | Proceed with caveats | Hold

## Executive Summary

[2-3 sentences: current cost posture, top risks the user accepted or
deferred, and the overall verdict with the dominant reason.]

## Pillar Analysis

### 1. Spend Aligned to Business Value
[Assessment per the guide. If no concerns, write "No concerns identified."]

### 2. Cost-Aware Culture
[...]

### 3. Resource Utilization Efficiency
[...]

### 4. Continuous Optimization
[...]

### 5. Architectural Cost Drivers
[...]

### 6. Workload-Specific Cost Patterns
[...]

## Risk Register

| ID | Severity | Finding (file:line — summary) | User Decision | Rationale | Owner / Follow-up |
|----|----------|-------------------------------|---------------|-----------|-------------------|
| C-C1 | Critical | infra/cluster.tf:21 — Always-on GPU pool for inference | Mitigate | Move to per-request inference endpoint | @carol / #3201 |
| C-I1 | Important | infra/storage.tf:55 — Logs in hot storage indefinitely | Defer | Will add lifecycle policy next sprint | TODO(cost) |

If there are no Critical or Important findings, write "No risks requiring
explicit decision." instead of an empty table.

## Nice-to-have (informational, not prompted)

- [C-N1] file:line — short note
- [C-N2] ...

If none: "No nice-to-have findings."

## Overall Verdict

**Proceed** — all Critical and Important findings will be mitigated.
**Proceed with caveats** — N risks Accepted, M Deferred. See register.
**Hold** — risk C-C1 was Blocked; resolve before proceeding.
```

## Numbering

- Critical: `C-C1`, `C-C2`, ...
- Important: `C-I1`, `C-I2`, ...
- Nice-to-have: `C-N1`, `C-N2`, ...

## Empty principles

If a principle has nothing to flag, keep the section header with "No
concerns identified." underneath. This proves the principle was reviewed
rather than skipped.

## When writing to file

If `--file` is set, write the report to `well-arch-cost-YYYY-MM-DD-HHmm.md`
in the current working directory. Confirm the file path to the user after
writing.
