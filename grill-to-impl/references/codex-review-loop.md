# Codex Review Loop (pre-flight brief hardening)

Goal: harden the brief with an **adversarial Codex review** BEFORE the spawned
session runs `prd-council` (which does its own heavy PRD debate). Keep this light —
it reviews the *brief*, not a full PRD. Loop until Codex approves or `--rounds`.

## Engine

Use the **codex-server** skill (the user's ChatGPT subscription via `codex login`).
It is the same engine `prd-council` uses. See the codex-server skill's `SKILL.md`
for the exact entrypoint (it spawns the system `codex` binary; prd-council shells
out to `~/.codex-server/lib/chat.ts`). Prefer structured (JSON-schema) output.

## Verdict schema — ALL properties REQUIRED

codex-server uses **strict** schema validation: every property declared in
`properties` MUST also appear in `required`, or round 1 returns HTTP 400. Do not
mark anything optional.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "approved":        { "type": "boolean" },
    "blocking_issues": { "type": "array", "items": { "type": "string" } },
    "suggestions":     { "type": "array", "items": { "type": "string" } },
    "summary":         { "type": "string" }
  },
  "required": ["approved", "blocking_issues", "suggestions", "summary"]
}
```

## Reviewer instruction (system / first turn)

> You are a skeptical staff engineer reviewing an IMPLEMENTATION BRIEF that will be
> handed to an autonomous coding agent with NO other context. Approve only if a cold
> agent could execute it correctly and safely. Check: (1) are all decisions and
> non-goals unambiguous; (2) does every step have a real file/path anchor; (3) are
> acceptance criteria checkable; (4) is scope bounded so the agent won't wander;
> (5) is the branch setup safe (never main/doc branch); (6) any missing platform,
> data, or dependency assumption. Return the structured verdict. Set approved=false
> if ANY blocking issue remains.

## Loop

```
round = 1
while round <= rounds:
    verdict = codex_review(brief, schema)        # structured
    if verdict.approved: break
    brief = revise(brief, verdict.blocking_issues)   # address each blocker concretely
    round += 1
mark brief: "Codex review: APPROVED (round <r>)"  or, if not approved within cap,
            "Codex review: NOT APPROVED after <rounds> rounds — proceeding with
             unresolved: <blocking_issues>"  (surface this to the user)
```

- Feed each round the CURRENT brief plus the still-open issues; do not re-litigate
  resolved ones.
- Apply `suggestions` at your discretion; `blocking_issues` must be addressed or
  explicitly waived with a one-line reason in the brief.

## Graceful degradation

If `--no-codex`, or Codex is unavailable (`~/.codex/auth.json` missing, `codex`
not installed, or the call errors), DO NOT silently skip. Instead run a
**Claude-only self-critique** using the same reviewer rubric above (one or two
passes), revise the brief, and mark it:

```
> Codex review: DEGRADED (Claude-only self-critique) — Codex was unavailable.
```

Never present a degraded brief as Codex-approved.
