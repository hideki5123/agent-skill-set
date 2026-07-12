---
name: well-arch-reliability
version: 1.0.0
description: >
  Review local git changes or an architecture document against the
  Reliability pillar of Google's Cloud Well-Architected Framework.
  Identifies gaps across 8 principles (SLOs aligned to UX, recovery
  targets, HA via redundancy, horizontal scalability, observability,
  graceful degradation, tested recovery, postmortems), and for each
  non-trivial risk asks the user to decide Accept / Mitigate / Defer /
  Block — producing a documented risk register, not just a finding list.
  GCP-principle-based but cloud-agnostic. Use when the user asks for a
  reliability review, resilience / SRE review, SLO assessment, failure-mode
  analysis, or recovery readiness check. Trigger phrases include
  "well architected reliability", "GCP reliability review",
  "reliability pillar review", "SLO review", "resilience review",
  "信頼性レビュー", "Well-Architected 信頼性", "可用性レビュー",
  "障害耐性レビュー".
---

# Well-Architected Reliability Review

Review changes or an architecture doc against Google's Cloud Well-Architected
**Reliability** pillar. Surface risks, then ask the user to make an explicit
Accept / Mitigate / Defer / Block decision per risk.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--staged-only` | `false` | Review only staged changes (`git diff --cached`) |
| `--doc <path>` | none | Review an architecture document instead of git diff |
| `--file` | none | Write report to `well-arch-reliability-YYYY-MM-DD-HHmm.md` |

## Workflow

```
1. Collect Input ──► 2. Read Context ──► 3. Pillar Analysis
                ──► 4. Risk Decision Loop ──► 5. Report
```

### Phase 1: Collect Input

If `--doc <path>` is set, read the document. Otherwise gather local changes:

```bash
# Staged changes (always collected)
git diff --cached

# Unstaged changes (skip if --staged-only)
git diff

# Untracked files (skip if --staged-only)
git status --porcelain | grep '^??'
```

If all produce empty results (or the doc is empty / missing), inform the user
"Nothing to review." and exit.

### Phase 2: Read Context

For each changed file (or referenced section of the doc), read the full
content. Skim related context that informs reliability: IaC files, service
manifests, autoscaling / HPA config, retry / circuit-breaker libraries in
use, observability config (dashboards, alerts), runbooks, and any existing
SLO definitions.

### Phase 3: Pillar Analysis

Walk the 8 principles in `references/reliability-review-guide.md`. For each
principle, use the review questions to identify findings. Tag each finding
with severity (Critical / Important / Nice-to-have) and an ID prefix `R-`:

- Critical → `R-C1`, `R-C2`, ...
- Important → `R-I1`, `R-I2`, ...
- Nice-to-have → `R-N1`, `R-N2`, ...

### Phase 4: Risk Decision Loop

Read `references/risk-decision-protocol.md`. For every Critical and Important
finding, call `AskUserQuestion` with the 4-option decision: **Accept /
Mitigate / Defer / Block**. Nice-to-have findings are listed in the report
without prompting. Batch up to 4 findings per `AskUserQuestion` call.

Capture each decision and any free-text rationale into the risk register.

### Phase 5: Report

Render the report from `references/report-template.md`. If `--file` is set,
write to `well-arch-reliability-YYYY-MM-DD-HHmm.md` in the current working
directory and confirm the path. Otherwise present the report inline.

The overall verdict is **Hold** if any Critical risk was Blocked, **Proceed
with caveats** if any risk was Accepted or Deferred, otherwise **Proceed**.

## Behavior Scenarios

```gherkin
Scenario: Git mode review with risk prompts
  Given the user has local changes
  When /well-arch-reliability is invoked
  Then changes are analyzed against the 8 reliability principles
  and the user is asked Accept/Mitigate/Defer/Block per Critical or Important risk
  and a report with a populated risk register is presented

Scenario: Architecture document review
  Given the user has an architecture doc at docs/architecture.md
  When /well-arch-reliability --doc docs/architecture.md is invoked
  Then the document is analyzed against the 8 reliability principles
  and the same risk decision loop and report flow runs

Scenario: Staged-only review
  Given the user has staged changes ready to commit
  When /well-arch-reliability --staged-only is invoked
  Then only staged changes are analyzed

Scenario: Write report to file
  Given the user wants a persistent record
  When /well-arch-reliability --file is invoked
  Then the report is written to well-arch-reliability-YYYY-MM-DD-HHmm.md
  and the file path is confirmed

Scenario: All risks accepted
  Given findings exist and the user selects Accept for every risk
  When the report is rendered
  Then the verdict is "Proceed with caveats"
  and each accepted risk is captured in the risk register

Scenario: One risk blocked
  Given the user selects Block on at least one Critical finding
  When the report is rendered
  Then the verdict is "Hold"

Scenario: Nothing to review
  Given no local changes and no --doc argument
  When /well-arch-reliability is invoked
  Then the user is told "Nothing to review." and the skill exits
```

## References

- `references/reliability-review-guide.md` — 8 reliability principles with
  focus, review questions, output format, and severity guidance per principle
- `references/risk-decision-protocol.md` — how to drive `AskUserQuestion`
  per risk and capture decisions into the register
- `references/report-template.md` — exact markdown format including the
  risk register and overall verdict
