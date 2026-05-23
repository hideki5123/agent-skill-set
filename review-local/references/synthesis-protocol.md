# Synthesis Protocol

After all teammates complete their reviews, synthesize findings into a single consolidated report.

## Steps

1. **Collect** all findings from each teammate's review output
2. **Categorize** each finding by severity using the table below
3. **Deduplicate** — if multiple perspectives flag the same issue, merge into one finding and note which perspectives identified it
4. **Prioritize** within each severity level by risk (likelihood x impact) then effort to fix
5. **Present** using the format in `report-template.md`

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **Critical** | Blocks commit — security risk, architectural flaw, data loss risk, broken contracts | Must fix before committing |
| **Important** | Should address for quality — not blocking but significantly impacts maintainability, performance, or correctness | Address before push or in same PR |
| **Nice-to-have** | Improvements that can be deferred — style, minor optimizations, future-proofing | Document for future consideration |

## Deduplication Rules

- Same file + same line range + same concern = merge, list all perspectives that found it
- Same concern in different files = keep separate but note the pattern
- Conflicting findings between perspectives = present both viewpoints, let user decide

## Clean Up

After synthesis is complete and the report is presented, clean up the team.
