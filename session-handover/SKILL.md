---
name: session-handover
description: >
  Generate a HANDOVER.md session handover document that captures everything done in the current session
  for seamless context transfer to the next session. Use when the user says "handover", "end session",
  "wrap up", "session summary", "context handover", or when context window is filling up.
  Produces a structured handover note covering: completed work, decisions, abandoned approaches,
  bugs/fixes, lessons learned, next steps, and key file map.
---

# Session Handover

Generate a `HANDOVER.md` at the project root to hand off session context to the next AI session.
Think of it as a shift-change report -- it tells the next session exactly where things stand
so nothing gets lost between sessions.

**Key distinction**: `CLAUDE.md` / project rules = permanent project-wide guidance.
`HANDOVER.md` = ephemeral session-to-session handover note. Keep them separate.

## When to Generate

- User explicitly requests handover (`/handover`, "wrap up", "end session")
- Context window is filling up and the session is about to end
- Before switching to a different task or project area

## Workflow

1. Review everything done in this session (files changed, conversations, decisions)
2. Generate `HANDOVER.md` at the project root using the template below
3. If `HANDOVER.md` already exists, **overwrite it** (previous session's handover is no longer needed)
4. Inform the user that the handover document is ready

## HANDOVER.md Template

Generate the document with the following structure. Omit sections that have no content.

~~~markdown
# Session Handover

Generated: {timestamp}

## What Was Done

- {Completed work items as bullet points}
- {Include progress status for each item}

## Decisions Made

- {Design decisions, policy choices, architecture calls}
- {Include the reasoning behind each decision}

## Abandoned Approaches

- {Approaches considered but not taken}
- {Why they were rejected -- saves the next session from re-exploring dead ends}

## Bugs & Fixes

- {Bugs encountered and how they were resolved}
- {Include root cause if identified}

## Lessons Learned

- {Gotchas, quirks, non-obvious behaviors discovered}
- {Workarounds that were needed}

## Next Steps

- [ ] {Prioritized task list for the next session}
- [ ] {Be specific and actionable}

## Key Files

| File | Role |
|------|------|
| {path} | {brief description of what it does / why it matters} |
~~~

## Guidelines

- **Be concise**: Bullet points, not paragraphs. The next session needs to scan quickly.
- **Be specific**: Include file paths, function names, line numbers when relevant.
- **Prioritize next steps**: The most important section -- tell the next session exactly what to do first.
- **Include context the AI wouldn't infer from code alone**: Why decisions were made, what was tried and failed, verbal agreements with the user.

## Resuming from a Handover

When starting a new session, if `HANDOVER.md` exists at the project root:

1. Read it immediately
2. Acknowledge what was done previously
3. Confirm the next steps with the user before proceeding
4. Delete or overwrite `HANDOVER.md` once the new session's work is underway
