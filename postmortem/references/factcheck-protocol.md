# Fact-check Protocol

**WHEN TO READ**: Phase 5, after the draft and the claims file exist on disk.

The draft is currently a plausible story assembled from three compressed summaries. Nothing in it has
been checked against a source since the collectors ran, and a collector could have mis-read a
timestamp or over-compressed an event. This phase is where the document earns the right to be
published.

## Why the fact-checkers do not get the evidence cards

Checking the draft against the cards it was built from tests whether the writer copied correctly. It
cannot catch a collector's error: a mis-converted epoch timestamp, verified against the card that
contains that same mis-converted timestamp, comes back CONFIRMED and lands in a published document.

So the fact-checkers **re-fetch from the original sources** and are deliberately not shown the cards.
That is what makes this verification rather than proofreading. It also preserves the context
guarantee — the re-fetched bulk lives in the fact-checker's disposable context, and only verdicts
cross back.

## What gets fact-checked

**Facts only.** A claim qualifies if a source can settle it: a timestamp, a number, what changed, who
acted, what someone actually said.

The **root cause**, the **contributing factors**, and the **lessons** are not claims — they are
interpretation. No source confirms them, so a fact-checker can only return UNSUPPORTED and hedge them
into mush, which reads as doubt about the analysis rather than the honest statement of an inference.
They are verified by the user in Phase 6, where judgement belongs.

Cap the claim list at 30, prioritising: signal timestamps → TTD/TTM/TTR → impact figures → the
trigger → timeline rows carrying a number or an attribution. "Investigation continued" needs no
verification.

## Dispatch

1. **Group the claims by the source domain they cite** — slack / code / tracker. A claim citing a
   Slack permalink goes to slack; a claim citing a PR goes to code.

2. **Derived claims** (TTD, TTM, TTR, durations) go to the domain that owns their *inputs*. Most
   derive from `first_impact_at` and `detected_at`, which usually come from Slack. When a derived
   claim's inputs **span two domains** (TTR from a Slack `first_impact_at` and a Jira `resolved_at`),
   send it to the domain owning the input most likely to be wrong — normally the softer one,
   `first_impact_at` — and write both inputs and both source links into the claim row. The
   fact-checker verifies what it can reach, recomputes, and flags in its correction which input it
   could not verify. A half-checked metric that says so is fine; one that pretends to be fully
   checked is not.

3. **Dispatch one `postmortem:factchecker` per non-empty domain, in parallel** (multiple Agent calls
   in a single message). Pass each the **path to the claims file** and its domain — not the claims
   themselves. The file is already on disk; re-typing it into the prompt copies it into the main
   session's context a second time for no benefit.

4. Each returns a count line plus rows for **only the non-CONFIRMED claims**. Nothing else crosses
   back.

## Applying verdicts

Edit the draft **file**, section by section. Never re-emit the document.

| Verdict | Action |
|---------|--------|
| **CONTRADICTED** | Apply the correction, or delete the claim. **Never publish a CONTRADICTED claim.** |
| **UNSUPPORTED** | Attribute it, hedge it, or drop it. An unmarked UNSUPPORTED claim reads as established fact — exactly the failure this phase exists to prevent. |

**Corrections cascade.** A corrected `first_impact_at` invalidates TTD, TTM, TTR, the impact-window
row in the Overview, and possibly a phrase like "9 minutes before impact" in Root Cause. Walk every
claim that depends on a corrected value; do not fix only the row the verdict named.

## The re-collect threshold

**If more than a third of the claims come back CONTRADICTED, stop patching.** That rate does not mean
the draft has a few errors — it means the Phase 3 merge was built on a bad reading of the sources.
Usually a timezone offset applied to the whole timeline, or the wrong thread collected. Patching claim
by claim leaves a document that is individually correct and collectively wrong.

Re-run Stage A collection, tell the user why, and rebuild the timeline.

## Reporting

Carry a one-line summary into Phase 6 so the user knows how much to trust the draft:

```
Fact-check: 24 claims — 20 confirmed, 3 corrected, 1 unconfirmed (the customer count).
```

Name the unconfirmed ones. They are the interesting ones, and they are what the user is uniquely able
to settle.
