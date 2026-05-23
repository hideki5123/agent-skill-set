# PM Review Report Template

Use this exact format for the PM review report.

```markdown
# PM Review Report

**Date**: YYYY-MM-DD HH:mm
**Scope**: All changes | Staged only
**Files reviewed**: N

## Executive Summary

[2-3 sentence high-level assessment: What these changes do from a project management perspective, key concerns, and overall recommendation (proceed / proceed with caveats / hold for discussion).]

## PMBOK Analysis

### Scope Management
[Findings from scope analysis]

### Risk Management
[Findings from risk analysis]

### Stakeholder Impact
[Findings from stakeholder analysis]

### Quality Management
[Findings from quality analysis]

### Integration Management
[Findings from integration analysis]

### Schedule Impact
[Findings from schedule analysis]

### Resource Management
[Findings from resource analysis]

## Action Items

| # | Action | Priority | Area |
|---|--------|----------|------|
| 1 | [Specific action to take] | High/Medium/Low | [PMBOK area] |
| 2 | ... | ... | ... |

## Overall Recommendation

[Proceed / Proceed with caveats / Hold for discussion — with reasoning]
```

## When Writing to File

If `--file` is set, write the report to `pm-review-YYYY-MM-DD-HHmm.md` in the current working directory. Confirm the file path to the user after writing.

## Empty Sections

If a PMBOK area has no findings or concerns, include the section header with "No concerns identified." underneath. This confirms the area was reviewed.
