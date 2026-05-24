# Security Review Report Template

Use this exact format for the Well-Architected Security review report.

```markdown
# Well-Architected Security Review
**Date**: YYYY-MM-DD HH:mm
**Mode**: git diff | architecture doc <path>
**Scope**: All changes | Staged only | Document
**Files / sections reviewed**: N
**Overall Verdict**: Proceed | Proceed with caveats | Hold

## Executive Summary

[2-3 sentences: current security posture, top risks the user accepted or
deferred, and the overall verdict with the dominant reason.]

## Pillar Analysis

### 1. Security by Design
[Assessment per the guide. If no concerns, write "No concerns identified."]

### 2. Zero Trust
[...]

### 3. Shift-Left Security
[...]

### 4. Preemptive Cyber Defense
[...]

### 5. AI Used Securely & Responsibly
[... or "Not applicable — no AI/LLM components."]

### 6. Regulatory, Compliance & Privacy
[...]

### 7. Shared Responsibility
[...]

## Risk Register

| ID | Severity | Finding (file:line — summary) | User Decision | Rationale | Owner / Follow-up |
|----|----------|-------------------------------|---------------|-----------|-------------------|
| S-C1 | Critical | path/to/file.py:42 — Hardcoded API key | Mitigate | Will rotate and move to Secret Manager | @alice / #1234 |
| S-I1 | Important | infra/main.tf:88 — Bucket has uniform public access | Defer | Tracking for next sprint | TODO(security) |

If there are no Critical or Important findings, write "No risks requiring
explicit decision." instead of an empty table.

## Nice-to-have (informational, not prompted)

- [S-N1] file:line — short note
- [S-N2] ...

If none: "No nice-to-have findings."

## Overall Verdict

**Proceed** — all Critical and Important findings will be mitigated.
**Proceed with caveats** — N risks Accepted, M Deferred. See register.
**Hold** — risk S-C1 was Blocked; resolve before proceeding.
```

## Numbering

- Critical: `S-C1`, `S-C2`, ...
- Important: `S-I1`, `S-I2`, ...
- Nice-to-have: `S-N1`, `S-N2`, ...

## Empty principles

If a principle has nothing to flag, keep the section header with "No
concerns identified." underneath. This proves the principle was reviewed
rather than skipped. For AI Used Securely & Responsibly specifically, write
"Not applicable — no AI/LLM components." if the system has none.

## When writing to file

If `--file` is set, write the report to `well-arch-security-YYYY-MM-DD-HHmm.md`
in the current working directory. Confirm the file path to the user after
writing.
