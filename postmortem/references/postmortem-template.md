# Postmortem Template

**WHEN TO READ**: Phase 4, when drafting the document.

Section order follows Google SRE's postmortem practice. Write in **English**. Write blamelessly.

## The document

```markdown
# Postmortem: <short incident title>

**Status**: Draft | Reviewed | Final
**Incident date**: 2026-07-10
**Authors**: <who wrote this>
**Severity**: <see rubric below>
**Source thread**: [#incident-2026-07-10](<slack permalink>)

## Overview

<Three to five sentences. What broke, who it affected, how long, how it was found, what fixed it,
and the one-line root cause. A reader who stops here should still know what happened.>

| | |
|---|---|
| **Impact window** | 2026-07-10 14:01–14:41 JST |
| **Time to detect (TTD)** | 2 min |
| **Time to mitigate (TTM)** | 40 min ← how long users actually hurt |
| **Time to resolve (TTR)** | 71 min (includes post-impact cleanup) |
| **Detected by** | `alert` / `customer report` / `internal user` / `engineer, incidentally` |
| **Recurrence** | First occurrence \| Recurrence of [PROJ-0987](<url>) (2026-03-02) |
| **Root cause** | <one line> |

<**Detected by** must come from a source, not from vibes — the slack-collector returns `detected_via`
for exactly this row. If it is `customer report` or `engineer, incidentally`, monitoring did not
catch this, and that is a finding: it belongs in "What went badly" and it needs a *detection* action
item. Say so explicitly; a customer-detected incident with no detection action item is a postmortem
that learned nothing.>

## Impact

- **Who**: <affected customers, segments, internal users — a number if a source has one,
  "unquantified" if not. Never invent a figure.>
- **What**: <how the system misbehaved. Not only up/down — pick what actually happened:
  full outage, elevated latency, partial errors, **data loss**, **data corruption**, or
  **silently wrong results**. The last three are the ones people forget to look for, and they are
  the ones that keep hurting after the service is green again. If wrong data was written, say what,
  how much, and whether it was repaired.>
- **How long**: <duration; continuous or intermittent.>
- **Business consequence**: <failed transactions, missed SLA, support load — or "not quantified".>

## Communications

| | |
|---|---|
| **Customers told?** | Yes / No / Partially |
| **When** | 14:20 JST (19 min after impact began) |
| **Channel** | status page / email / in-app / support only |
| **Correction or follow-up sent?** | Yes — 15:30 JST / No |

<Delete this section only if the incident had no external impact. If customers were affected and were
*not* told, that is itself a finding — put it in "What went badly". Silence toward customers is a
decision, not a non-event.>

## Root Cause & Contributing Factors

**Trigger**: <the proximate change or event that started it — a deploy, a traffic spike, a
certificate expiry. Link the commit/PR.>

**Root cause**: <why the system was *vulnerable* to that trigger. Not the same as the trigger.
"PR #456 was merged" is a trigger; "the checkout client had no retry budget and no circuit breaker,
so a single upstream blip became a user-visible outage" is a root cause.>

**Contributing factors**: <the honest part. Incidents are almost never mono-causal — the trigger
lands on a system that was already primed. List each factor that made this incident possible, longer,
or worse, even when none of them alone would have caused it:>

- <e.g. the staging environment has one upstream replica, so the failure mode was unreachable in tests>
- <e.g. the alert threshold was set at 5% during a noisy quarter and never revisited>
- <e.g. the rollback path required a full pipeline run, which is why mitigation took 33 minutes>

<Each contributing factor is a candidate action item, and they are usually better action items than
the root cause — they are smaller, independently fixable, and each one shortens the *next* incident,
including the ones with a different trigger entirely.>

<Ask "why" until you reach something the team can change — a missing guardrail, an untested path, an
alert that did not exist. **Stop when the next "why" would be a person's mistake**; that is the signal
you have left blameless territory. A root cause you cannot write an action item against is not yet a
root cause.>

## Timeline

All times JST. Every row cites its source. Max 40 rows — collapse consecutive investigation chatter.

| Time | Event | Source |
|------|-------|--------|
| 13:52 | PR #456 merged to main — removes retry budget in checkout client | [PR #456](<url>) |
| 14:01 | Checkout error rate begins climbing | [dashboard](<url>) |
| 14:03 | `checkout-5xx` alert fires | [Slack](<permalink>) |
| 14:05 | On-call acknowledges, begins investigating | [Slack](<permalink>) |
| 14:20 | Status page updated | [Slack](<permalink>) |
| 14:38 | Rollback of PR #456 deployed | [PR #461](<url>) |
| 14:41 | Error rate returns to baseline — impact ends | [dashboard](<url>) |
| 15:12 | Incident declared resolved | [Slack](<permalink>) |

<A row with no source is an assumption. Find the source, or move it to "Open questions".>

## Lessons

**What went well**
- <e.g. the alert fired within 2 minutes and paged the right person>

**What went badly**
- <e.g. the rollback took 33 minutes because the deploy pipeline had no fast path>

**Where we got lucky**
- <the most valuable subsection, and the one people skip. What made this *not worse*? Off-peak
  traffic? A single region? An engineer who happened to be online? Each lucky break is a latent SEV1
  waiting for a day when the luck runs out — and each one usually deserves an action item.>

<Before moving on, check the closure: does every item in "What went badly" and "Where we got lucky"
have a corresponding action item below, or an explicit decision to accept the risk? A lesson with no
action item and no accepted-risk note is a lesson the organisation did not actually learn.>

## Action Items

| # | Action | Category | Priority | Owner | Ticket |
|---|--------|----------|----------|-------|--------|
| 1 | Replace the rollback with a retry budget + circuit breaker in the checkout client | remediation | High | Payments | [PROJ-1240](<url>) |
| 2 | Alert on checkout error rate at 1%, not 5% | detection | High | SRE | [PROJ-1241](<url>) |
| 3 | Add a one-click rollback path to the deploy pipeline | mitigation | High | Platform | [PROJ-1242](<url>) |
| 4 | Add an upstream-failure case to the staging environment | prevention | Medium | Payments | [PROJ-1243](<url>) |
| 5 | Page the comms owner automatically on any SEV1 | process | Medium | SRE | [PROJ-1244](<url>) |

**Category** — one of:

- **remediation** — the durable fix that replaces the temporary mitigation. If the incident was
  stopped by a rollback, a feature-flag flip, or a restart, the system is still broken and something
  here must actually fix it. This is the item most often missing, because the incident *feels* over.
- **prevention** — stops this class of incident from happening again.
- **detection** — finds it faster next time (attacks TTD).
- **mitigation** — reduces the damage when it does happen anyway (attacks TTM).
- **process** — the human side: response, escalation, on-call, customer comms, runbooks.

A postmortem whose items are all *prevention* assumes it can foresee every future failure. Attack TTD
and TTM too — those pay off across the incidents nobody imagined.

Every action item must be concrete enough that its owner knows when it is done. "Improve monitoring"
is not an action item; "alert on checkout error rate at 1%" is. Prefer a named owner; a team name is
acceptable, "TBD" is not — an unowned action item is a wish.

## Open questions

- <anything the sources could not establish and the user could not answer — including "we cannot tell
  when impact began". Being explicit here is what keeps the rest of the document trustworthy.>
```

## Severity rubric

Use your team's scale if it has one. If it does not, this is the default — pick by the *worst* row
that applies, and state which row you picked in the header:

| | Impact |
|---|---|
| **SEV1** | Core flow unusable for many users, or any data loss / corruption, or revenue stopped |
| **SEV2** | Significant degradation, a workaround exists, or a subset of users fully blocked |
| **SEV3** | Minor or cosmetic; little user-visible effect; no workaround needed |

Data loss and corruption are SEV1 even when brief and even when few users saw them — the damage
outlives the outage.

## Drafting rules

- **Trigger ≠ root cause ≠ contributing factor.** Keep them in separate sentences. Conflating them
  produces action items that fix exactly one deploy.
- **No unsourced numbers.** If no source has a customer count and the user cannot supply one, write
  "unquantified". A fabricated figure is the fastest way to lose a team's trust in a generated
  document — and it is the one error a reader cannot detect.
- **No counterfactuals.** "If only the on-call had checked the dashboard" is blame wearing an
  analytical costume. Rewrite toward the system: "the dashboard did not surface the retry metric, so
  checking it would not have revealed the cause."
- **Timezone once, at the top.** State it and use it consistently. Mixed offsets are how TTD and TTM
  silently go wrong.
- **Claim IDs** live in the sidecar `.claims.md` file, never in the document. Only factual claims get
  one — the root cause, contributing factors, and lessons are interpretation, verified by the user.
