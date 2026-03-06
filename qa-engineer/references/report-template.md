# QA Report Template

Use this template structure when generating the quality report in Phase 7.
The report is saved as `REPORT.md` inside the evidence package directory.
Replace placeholders (`{...}`) with actual data. Omit sections that don't apply
(e.g., omit "Test Execution" if `--run=false`).

All relative links point to sibling files/directories within the evidence package.

---

```markdown
# QA Report: {project-name}

**Date:** {YYYY-MM-DD HH:mm}
**Scope:** {all | changed | path/glob}
**Lenses:** {comma-separated active lenses}
**Flags:** {--fix, --run=false, etc.}

## Evidence Package

| Directory | Contents | Count |
|-----------|----------|-------|
| `execution/` | Test output + summary | {n} files |
| `failures/` | Per-failure evidence folders | {n} failures |
| `gaps/` | Gap proof files + screenshots | {n} findings |
| `remediation/` | Added tests + diffs | {n} fixes |
| `recordings/` | Terminal/browser/native recordings | {n} artifacts |

## Executive Summary

**Health Verdict:** {HEALTHY | NEEDS ATTENTION | AT RISK | CRITICAL}

| Metric | Value |
|--------|-------|
| Source files in scope | {n} |
| Test files found | {n} |
| Test-to-source ratio | {n:n} |
| Tests run | {n} |
| Passed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Duration | {n}s |
| Gap findings | {n} (critical: {n}, high: {n}, medium: {n}, low: {n}) |
| Tests written (--fix) | {n} |

{One-paragraph summary of the most important findings and recommended actions.}

## Test Execution Results

**Runner:** `{command}`
**Duration:** {n}s
**Full output:** [test-output.txt](execution/test-output.txt)
**Summary data:** [test-summary.json](execution/test-summary.json)

| Status | Count |
|--------|-------|
| Passed | {n} |
| Failed | {n} |
| Skipped | {n} |
| Total | {n} |

### Failure Triage

| # | Test | Category | Confidence | Evidence | Suggested Fix |
|---|------|----------|------------|----------|---------------|
| 1 | {test name} | {env/flaky/defect/test-bug} | {high/med/low} | [evidence](failures/001-{test-name}/) | {one sentence} |
| ... | ... | ... | ... | ... | ... |

## Gap Analysis by Perspective

### {Lens Name} ({n} findings)

| # | Severity | Confidence | Location | Pattern | Proof | Suggested Test |
|---|----------|------------|----------|---------|-------|----------------|
| 1 | {critical} | {high} | {file:line} | {what was detected} | [proof](gaps/gap-001-{lens}-{severity}.md) | {what to test} |
| 2 | {high} | {medium} | {file:line} | {what was detected} | [proof](gaps/gap-002-{lens}-{severity}.md) ![screenshot](gaps/gap-002-screenshot.png) | {what to test} |
| ... | ... | ... | ... | ... | ... | ... |

{Repeat for each active lens with findings. Include screenshot links only for browser apps where screenshots were captured.}

## Gap Analysis by Severity

### Critical ({n})

{List critical findings across all lenses, with lens label and proof links.}

### High ({n})

{List high findings.}

### Medium ({n})

{List medium findings.}

### Low ({n})

{List low findings.}

## Remediation

### Tests Written (--fix)

| # | Test File | Tests Added | Covers | Evidence | Status |
|---|-----------|-------------|--------|----------|--------|
| 1 | {test/foo.test.ts} | {2} | {functional gap in src/foo.ts:42} | [evidence](remediation/001-{test-file}/) | {PASS} |
| ... | ... | ... | ... | ... | ... |

{Omit this section if `--fix` was not used.}

## Recordings

| # | Type | Artifact | Duration | Size |
|---|------|----------|----------|------|
| 1 | Terminal recording | [test-run.gif](recordings/terminal-run.gif) | {n}s | {size} |
| 2 | UI screenshot | [login-fail.png](recordings/ui-screenshot-001-login.png) | — | {size} |
| 3 | UI video | [login-fail.webm](recordings/ui-failure-001-login.webm) | {n}s | {size} |
| 4 | Native screen rec | [app-test.mp4](recordings/native-run-001.mp4) | {n}s | {size} |

{Omit this section if `--evidence=off` or no recordings were captured. Baseline evidence (execution/, failures/, gaps/) is always present regardless of this setting.}

## Coverage Tooling

{One of the following:}

**Detected:** {description of coverage tooling found — e.g., "husky pre-commit hook runs `jest --coverage`; CI pipeline enforces 80% coverage gate via Codecov."}

**Not detected:** No coverage gates or pre-commit hooks found. Recommend setting up:
- **Pre-commit:** husky + lint-staged with coverage threshold check
- **CI gate:** Codecov, Coveralls, or built-in CI coverage reporting with minimum threshold
- **Runner config:** Add coverage thresholds to test runner config (e.g., Jest `coverageThreshold`, pytest `--cov-fail-under`)

## Recommended Next Steps

1. {Highest-priority action item}
2. {Second priority}
3. {Third priority}
4. ...

---

## Navigating This Evidence Package

This report is the index into the evidence package. Use these paths to find specific evidence:

- **Full test output:** `execution/test-output.txt`
- **Parsed test results:** `execution/test-summary.json`
- **Failure N details:** `failures/NNN-<test-name>/` (error, source context, test code, rerun)
- **Gap N proof:** `gaps/gap-NNN-<lens>-<severity>.md` (source snippet + explanation)
- **Gap N screenshot:** `gaps/gap-NNN-screenshot.png` (browser apps only)
- **Remediation N:** `remediation/NNN-<test-file>/` (diff + test output)
- **Recordings:** `recordings/` (terminal GIFs, browser video, native screen capture)

*Generated by qa-engineer skill*
```
