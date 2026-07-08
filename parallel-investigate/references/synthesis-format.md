# Synthesis Format

WHEN TO READ: during Step 3 (Launch the Workflow), when writing the Synthesize-phase
agent's prompt.

The Synthesize agent receives every Explore-phase finding (each with its own
file:line citations) and must turn them into one ranked, defensible answer. Give
it these exact instructions:

1. **Cross-reference, don't just concatenate.** Merge findings into a single
   ranked list, most-likely-cause/most-relevant-answer first. For each item: a
   one-line summary, the mechanism (why this explains the symptom, and why it
   would affect *some* cases and not others if that distinction matters), and the
   supporting file:line evidence pulled from the Explore findings.
2. **Tag confidence per item:**
   - `CONFIRMED` — verified by reading the actual code/logic/config; not
     speculation.
   - `PLAUSIBLE` — a reasonable mechanism the code allows, but not independently
     verified (e.g. it would require runtime/DB/log inspection to confirm).
3. **Resolve contradictions.** If two Explore agents disagree, do not just report
   both — reason about which is better-supported (e.g. one agent traced actual
   code, the other speculated) and say so explicitly. If genuinely unresolved,
   say that too, rather than picking arbitrarily.
4. **Note convergence.** If multiple independent Explore agents arrived at the
   same answer without being told to look for it, say so — independent
   convergence is itself evidence and should raise confidence.
5. **Give a next step.** End with the single most useful next action to nail
   down any item still tagged PLAUSIBLE (e.g. "check the DB for which accounts
   are configured this way").
6. **Cap length.** Keep the synthesis under ~900 words — it is relayed directly
   to the user in chat, not stored as a report file.

This mirrors the format that worked well in practice: independently-arrived-at
convergence across a majority of Explore agents was what justified tagging the
top answer CONFIRMED instead of PLAUSIBLE, and the ranked-with-evidence structure
let the final chat answer stay skimmable despite covering 5+ independent findings.
