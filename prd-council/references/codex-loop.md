# Codex Council Loop (Phase 3)

**WHEN TO READ:** at Phase 3 (the debate), or at Phase 0 if Codex setup/availability
is in question. Not needed for Phases 1, 2, 4, 5.

This is the heart of prd-council: the PRD is debated with OpenAI Codex
round-by-round until **mutual approval**. The engine is the **codex-server** skill
(ChatGPT-subscription auth, multi-turn threads, structured output). codex-server is
the source of truth for the invocation surface — if a flag below has drifted,
consult its SKILL.md.

## Availability & setup

1. Prefer the stable entry point `~/.codex-server/lib/chat.ts`.
2. If it is absent, the codex-server first-run setup has not run. Resolve its
   `setup.ts` portably (do NOT hardcode a version or marketplace name):

   ```bash
   ls ~/.codex-server/lib/chat.ts 2>/dev/null \
     || ls ~/.claude/plugins/cache/*/codex-server/*/skills/codex-server/assets/lib/setup.ts 2>/dev/null
   ```

   Run that `setup.ts` once with deno (see codex-server's "First-run setup"), then
   use `~/.codex-server/lib/chat.ts`.
3. Auth: requires `~/.codex/auth.json` (the user ran `codex login`). If missing,
   either tell the user to run `codex login`, or proceed **degraded** (below).

## Invocation pattern

Per codex-server's contract, each `chat.ts` call runs through deno with scoped
flags. **`--allow-run` must permit BOTH the codex binary AND deno itself**:
`new`/`continue` fork a *detached deno worker* (the decoupled-async design), and
that worker in turn spawns codex. The codex path is pinned in
`~/.codex-server/config.json`; the deno path is `command -v deno`. (codex-server's
own SKILL.md under-documents this as codex-path-only — the authoritative form is in
the header of `chat.ts`: `--allow-run=<codex-path>,<deno-path>`. Verified by smoke
test: codex-path-only fails the first `new` with `NotCapable: Requires run access
to .../deno`.)

```bash
CODEX="$(deno eval 'console.log(JSON.parse(Deno.readTextFileSync(Deno.env.get("HOME")+"/.codex-server/config.json")).codexPath)')"
DENO="$(command -v deno)"

# Round 1 — open the thread, request a structured verdict.
deno run --allow-read --allow-write \
  --allow-env=PATH,HOME,USERPROFILE \
  --allow-run="$CODEX,$DENO" \
  --allow-net=api.openai.com \
  ~/.codex-server/lib/chat.ts new "<review request + PRD body>" \
  --schema <verdict-schema.json> --cwd <project> --skip-git-check
# → returns {turn_id, out_path} in <1s. A detached worker runs the turn.

# Later rounds — same thread, send changelog + revised PRD.
… --allow-run="$CODEX,$DENO" … ~/.codex-server/lib/chat.ts continue --last "<changelog + revised PRD>" --schema <verdict-schema.json>
```

> Shell note: pass `--allow-run="$CODEX,$DENO"` as one quoted token. Do not collapse
> the whole deno flag list into a single unquoted variable — zsh does not word-split
> it, and deno will reject it as one argument.

**Source of truth = the `done` / `error` marker files + `out.txt`.** Detect
completion by Monitoring the turn dir for the `done` marker (success) or `error`
marker (failure); then read `out.txt` — with `--schema` it is the structured JSON
verdict. Parse that JSON; do not scrape prose.

> **Do not trust `chat.ts wait`'s exit code right after `new`.** codex-server's
> `turnState` classifies a turn as `abandoned` when there is no marker yet and the
> recorded pid is not alive — but `new` writes `pid: 0` and the worker records its
> real pid a beat later, so a poll in that startup gap returns `abandoned` even
> though the turn then completes normally (confirmed by smoke test: `wait` reported
> `abandoned` while the `done` marker + a valid verdict appeared seconds later). If
> you use `wait` and it reports `abandoned`/`failed`, **re-check the `done` marker
> and `out.txt` before treating it as a real failure.** Prefer marker-based
> detection over `wait`.

## Verdict schema

Write this to a temp file and pass via `--schema`:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["verdict", "rationale"],
  "properties": {
    "verdict": { "type": "string", "enum": ["approve", "revise"] },
    "blocking_issues": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "title", "detail"],
        "properties": {
          "id": { "type": "string" },
          "title": { "type": "string" },
          "detail": { "type": "string" },
          "severity": { "type": "string", "enum": ["blocker", "major", "minor"] }
        }
      }
    },
    "suggestions": { "type": "array", "items": { "type": "string" } },
    "rationale": { "type": "string" }
  }
}
```

The Codex prompt should instruct: act as a critical staff engineer reviewing this
PRD; return `verdict: revise` with concrete `blocking_issues` while anything is
unclear, infeasible, untestable, or risky; only `approve` when you would stake
your name on it.

## Default mode — algorithm

```
round = 0
loop:
  round += 1
  send PRD (new on round 1, continue --last after) → parse verdict
  append round to debate-log.md
  if verdict == "approve":
      # MUTUAL: Claude must also be satisfied, not rubber-stamp.
      if Claude has an unresolved objection to a Codex suggestion that was
         incorporated, OR Claude still has its own doubt → push back one round
      else → MUTUAL APPROVAL, break
  else:  # revise
      resolve every blocking_issue, revise prd.md, write a changelog line
  if round >= rounds_cap:   # default 4
      ESCALATE: stop, surface the open disagreements to the user, let them decide
      break
```

**Mutual approval** = Codex returns `approve` AND Claude has no unresolved
objection. Claude is a peer in the debate, not a stenographer — if Codex pushes a
change Claude believes is wrong, Claude argues it in the next `continue` turn
rather than silently complying.

## Heavy mode (`--council heavy`)

Each round gathers more than one perspective before deciding:

- **Codex verdict** (as above), plus
- **Claude self-critique across lenses**: correctness/feasibility, security,
  testability, UX, scope-creep. Optionally spawn these lenses as parallel
  subagents (Agent tool) for independence, then synthesize.

A round passes only when **Codex approves AND every lens approves**. Same round
cap and escalation apply. Use for large or high-risk PRDs; it costs more tokens.

## Graceful degradation (no Codex)

If `~/.codex/auth.json` is missing, `codex` is not installed, or `--no-codex` is
set: run a **Claude-only self-critique council** across the same lenses, round by
round, until Claude has no remaining blocking issue (or the cap is hit). Mark the
log header clearly and recommend enabling the real council:

```
# PRD Council — Debate Log
> DEGRADED: Codex unavailable — Claude-only self-critique. Run `codex login`
> for a true two-party council.
```

Never silently skip the loop — a PRD that was never challenged is the failure mode
this skill exists to prevent.

## debate-log.md format

```markdown
# PRD Council — Debate Log
- Feature: <slug>
- Mode: default | heavy | degraded(claude-only)
- Codex model: <model or "n/a">
- Result: approved in <N> rounds | escalated after <N> rounds

## Round 1
**Claude → Codex:** <prompt / changelog summary>
**Codex verdict:** revise
- [blocker] <id> <title> — <detail>
- suggestions: <…>
- rationale: <…>
**Claude response:** <what was changed / what was pushed back on>

## Round 2
…

## Final
<Mutual approval reached.> | <Escalated. Open disagreements: …>
```
