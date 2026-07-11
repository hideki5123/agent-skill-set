# Evidence Card Schema

**WHEN TO READ**: before merging collector output in Phase 3, or when a collector returns something
malformed / over cap and you need to state the contract back to it.

An **evidence card** is the only thing a collector subagent is allowed to return. It exists to keep
the incident's bulk — Slack history, diffs, issue bodies, logs — inside the subagent's disposable
context while carrying enough into the main session to build a sourced timeline.

The card is **small but citation-complete**: every event keeps its link. A card that compresses away
its permalinks is useless, because the timeline table has a source column and the fact-checker
addresses claims by their source.

## Format

Collectors return exactly one fenced ```yaml block, nothing before or after it.

```yaml
source: slack            # slack | code | tracker
scope: "#incident-2026-07-10 thread p1720... , 2026-07-10 13:00–17:00 JST"

events:                  # chronological, max 40
  - t: 2026-07-10T14:03:00+09:00
    what: "Checkout API 5xx rate crosses alert threshold"   # <= 25 words, factual, no interpretation
    who: "monitoring"                                       # display name, role, or system. Never blame.
    src: "https://team.slack.com/archives/C0123/p172000000000000"

signals:                 # the timestamps that drive TTD/TTM/TTR. Omit a key entirely if unknown.
  first_impact_at: { t: 2026-07-10T14:01:00+09:00, src: "<link>", confidence: medium }
  detected_at:     { t: 2026-07-10T14:03:00+09:00, src: "<link>", confidence: high }
  mitigated_at:    { t: 2026-07-10T14:41:00+09:00, src: "<link>", confidence: high }
  resolved_at:     { t: 2026-07-10T15:12:00+09:00, src: "<link>", confidence: high }

detected_via: alert      # alert | customer-report | internal-user | engineer-incidental | unknown
                         # Fills the document's "Detected by" row, which otherwise gets guessed.
                         # customer-report and engineer-incidental mean monitoring MISSED this —
                         # the main session turns that into a finding and a detection action item.

comms:                   # external communication. Omit entirely if the incident had no user impact.
  customers_informed: true|false|unknown
  first_notice_at: { t: <iso8601>, src: "<link>" }
  channel: "status page | email | in-app | support only | none"

refs:                    # what this source points at — seeds the next collection stage
  jira: ["PROJ-1234"]
  github: ["https://github.com/org/repo/pull/456"]
  commits: ["a1b2c3d"]
  repos: ["org/repo"]
  dashboards: ["<url>"]

quotes:                  # max 5. Only lines that carry a lesson or a decision.
  - text: "we rolled back before we understood it, that's why the second spike surprised us"
    who: "on-call"
    src: "<permalink>"

gaps:                    # what this source could NOT establish, and why
  - "No customer-count figure anywhere in the thread — impact size must come from the user."
```

Not every collector fills every key. Slack owns `detected_via` and `comms`; code owns the deploy
spine; the tracker owns recurrence. A collector omits keys it cannot speak to rather than guessing.

## Hard caps

| Rule | Limit |
|------|-------|
| `events` | 40 entries |
| `what` | 25 words |
| `quotes` | 5 entries, 30 words each |
| Whole card | 120 lines |
| Raw message bodies, diffs, file contents, log lines | **forbidden** — cite the link instead |

If the material exceeds the caps, do not truncate arbitrarily. Prioritise:

1. `signals` — without them there is no TTD/TTM/TTR.
2. Events that **change** the timeline (impact starts, alert fires, deploy, rollback, mitigation, all-clear).
3. `refs` — they seed the next collection stage.
4. Everything else.

Then record the compression in `gaps` (e.g. "collapsed 60 status-update messages into 3 events").

**Self-check before returning.** A subagent's return lands in the main session verbatim — nothing can
filter it after the fact. Count your events and lines *before* you emit the card. The caps are only
real if you enforce them here.

## Rules for every collector

- **Timestamps are ISO-8601 with an explicit offset.** Slack gives epoch seconds; convert. A naked
  `14:03` is useless in a document read across timezones — and a wrong offset silently corrupts every
  metric downstream.
- **Resolve identifiers.** No `<@UXXX>`, `<#CXXX>`, `<!subteam^SXXX>` may leave the subagent.
- **Blameless.** `who` records the actor's role in the event, never a judgement. "deployer merged
  PR #456", not "X broke prod". No counterfactuals ("should have caught it").
- **Facts, not narrative.** `what` states what happened. Causal claims ("this caused the outage")
  belong to the main session's analysis — you saw one source and cannot know.
- **`confidence: low` beats a confident guess.** The main session asks the user about low-confidence
  signals; a fabricated timestamp silently corrupts TTD/TTM/TTR and nobody downstream can catch it.
- **A failed command is a gap, not silence.** If a CLI errors (missing auth, unknown flag, 404), say
  so in `gaps`. An empty card that looks like "nothing happened" is worse than an error.

## Maintenance note

This contract is **duplicated in condensed form in the three collector agents**
(`agents/slack-collector.md`, `agents/code-collector.md`, `agents/tracker-collector.md`), because a
subagent running from the installed plugin cache cannot reliably resolve a path back to this file.
`agents/factchecker.md` does not return a card — it returns verdicts, and has its own contract.
When you change the schema, update the three collectors too.
