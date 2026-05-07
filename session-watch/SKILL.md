---
name: session-watch
version: 1.1.1
description: >
  Watch another running Claude Code session in real time and narrate its activity in Japanese
  with detailed term-by-term explanations. By default targets a session active in the current
  working directory; if multiple are active, asks the user to pick. Can also target a specific
  session by ID. Read-only on the watched session. After the watch ends, invokes session-recap;
  any further chain (e.g. recap-to-notion for Notion sync) is configured by session-recap's own
  ~/.claude/session-recaps/.recap-config.json, not this skill. Use when the user says
  "session監視" / "監視して" / "別のClaudeを観察" / "他のセッションを見ていて" /
  "Aliseを観察" / "watch session" / "observe" / "observe claude" / "observe session" /
  "observe the session" / "Observe" / "/session-watch" / "セッションウォッチ" /
  "オブザーブ" / "他のセッション解説" / "別Claudeをモニタ".
---

# session-watch

Watch a running Claude Code session by tailing its transcript JSONL and explain each event
in Japanese, with detailed re-explanation of technical terms every time they appear.

The user is observing another agent's work and needs to understand what is happening. They will
forget terms across events, so re-explanation is mandatory, not optional.

## Workflow

### Feedback Check

If `feedback/log.md` exists alongside this SKILL.md and has 5 or more entries, read the last
10 entries. If a pattern is apparent (the same issue appears in 3+ entries, or average rating
is below 3):

- Tell the user (in Japanese): 「過去のフィードバックで類似パターンを検出: [簡潔に]。`/my-skill-factory improve session-watch` で改善できます。」
- Continue with normal execution.

### Step 1: Identify the target session

Look at the user's invocation message for any of:

- A bare UUID (8-4-4-4-12 hex) — treat as explicit session ID.
- A path or `--cwd` mention — treat that as the working directory to scan instead of `$PWD`.
- Otherwise → scan the current working directory's project transcript folder.

#### If a session ID was given

Locate the file:

```bash
find ~/.claude/projects -maxdepth 2 -name "<session-id>.jsonl" 2>/dev/null
```

If found → use it. If not found → tell the user the ID was not seen anywhere under
`~/.claude/projects/` and stop.

#### If no session ID was given (default)

1. Encode the target cwd: replace every `/` with `-`. Example:
   `/Users/alice/code/foo` → `-Users-alice-code-foo`.

2. The transcript directory is `~/.claude/projects/<encoded>/`.

3. List candidate sessions, ranked by recency:

   ```bash
   ENC=$(echo "$PWD" | sed 's|/|-|g')
   DIR=~/.claude/projects/$ENC
   # list files modified in the last 10 minutes, newest first
   find "$DIR" -maxdepth 1 -name '*.jsonl' -mmin -10 -print0 \
     | xargs -0 ls -lt 2>/dev/null
   ```

4. For each candidate, peek at the latest event to show context:

   ```bash
   for f in <candidates>; do
     echo "=== $(basename $f .jsonl) ==="
     tail -1 "$f" | jq -r '
       (.timestamp // "") + " | " +
       (.type // "?") + " | " +
       ((.message.content // [])
         | if type == "array" then
             map(if .type == "text" then .text
                 elif .type == "tool_use" then "[" + .name + "]"
                 else "" end) | join(" ")
           else (. | tostring) end)
       | .[0:160]
     '
   done
   ```

5. Pick:
   - **0 candidates** → tell the user no session is currently active in this directory; suggest
     either passing a session ID or `cd`-ing to where the target session is running.
   - **1 candidate** → use it; mention the session ID and the slug/title for confirmation.
   - **2+ candidates** → invoke `AskUserQuestion` with the candidate list (session ID + last
     activity timestamp + last event one-liner). Note: one of these is likely THIS session
     itself; do not auto-exclude — let the user pick.

### Step 2: Start the monitor

Use the `Monitor` tool (load schema via ToolSearch if not already loaded). Default filter
captures execution-style tool calls, user-question tool calls, and assistant text:

```bash
tail -F -n 0 <session-file> 2>/dev/null | jq -c --unbuffered '
  . as $r |
  select($r.type == "assistant") |
  ($r.message.content // [])[]? |
  . as $c |
  if $c.type == "tool_use" and ($c.name | test("^(AskUserQuestion|Bash|Edit|Write|NotebookEdit|MultiEdit|Skill|Agent|mcp__)")) then
    {ts: $r.timestamp, sc: $r.isSidechain, kind: "tool", name: $c.name, input: $c.input}
  elif $c.type == "text" then
    {ts: $r.timestamp, sc: $r.isSidechain, kind: "text", text: $c.text}
  else empty end
'
```

Settings: `persistent: true`, `timeout_ms: 3600000`. Description should include the session
ID short form, e.g. `Aliseのsession監視 (ec8dca3f...)`.

`tail -F -n 0` starts from the END so you only observe NEW activity, not the historical replay.

After starting, tell the user: monitor task ID, what is being captured, and how to stop
("監視やめて" / "stop" → you call `TaskStop` with the task ID).

### Step 3: Narrate each event

Each Monitor notification carries one event as compact JSON. For every event, produce a
Japanese explanation. The user wants depth, not translation.

Required style:

1. **Lead with a tag** showing source + kind:
   - `[Alise:text]` — assistant prose to the user
   - `[Alise:Bash]` / `[Alise:Edit]` / `[Alise:Write]` etc. — tool calls
   - Replace `Alise` with whatever name the user has used; if none, use the short session ID.

2. **For tool calls**: quote the command/path, then break down each part:
   - Every CLI flag → name + what it does + why it might be used here.
   - Every shell construct → `&&`, `||`, `|`, `>`, `2>&1`, heredoc, command substitution etc.
     — explain each one as it appears.
   - Background flag (`run_in_background`), timeouts → call them out.
   - For `Edit` / `Write`: summarize what changed and why (infer from diff if visible).

3. **For assistant text**: quote the original (in a blockquote), then translate the meaning
   AND expand every technical term into a brief definition. Do not assume the user remembers
   prior definitions.

4. **Term re-explanation rule**: explain the same technical term every time it appears.
   The user has explicitly asked for this — they will forget across events. Examples of
   terms that always need a one-liner: `derivation`, `flake`, `overlay`, `home-manager`,
   `nix-daemon`, `binary cache`, `synthetic.conf`, GPG signing, heredoc, `tee`, `2>&1`,
   short SHA, `--show-trace`, etc.
   Pick a brief gloss (1-2 sentences); do not lecture.

5. **Notable side effects**: if the event is destructive, network-touching, or modifies
   shared state (push, deploy, kill, sudo, write outside repo), surface that explicitly
   at the top of the explanation.

6. **Sidechain marker**: if `sc: true`, prefix the tag with `[sub-agent]` so the user
   knows this came from one of Alise's spawned agents.

7. **Truncation**: events arrive truncated when long. If you see `...(truncated)`,
   say so and reason about what the missing tail likely contained.

Do NOT send a `PushNotification` for routine events. Only push if the event is something the
user would want to act on right now from outside this chat (e.g., Alise asked them a direct
question, a destructive action just landed, a build they were waiting on finished).

### Step 4: Filter adjustments

If the user asks to widen or narrow the filter (e.g., "Read/Grepも観たい", "テキストはいらない"),
`TaskStop` the current monitor and start a new one with an updated jq filter. Common variants:

- All tool calls (no filter on name) — drop the `test(...)` clause.
- Tools only (no text) — drop the `elif $c.type == "text"` branch.
- Include user messages — add a sibling clause for `$r.type == "user"`.

### Step 5: Stop

When the user says any of "監視やめて" / "止めて" / "stop" / "監視終わり" / "もういい":

1. Call `TaskStop` with the task ID and confirm in Japanese.
2. **Invoke `session-recap`**: use the Skill tool with `skill: "session-recap"` and `args`
   set to the watched session's full UUID. This produces `summary.md` + `note.md` capturing
   the technical knowledge, terminology, and decisions from the watched session — kept as
   a separate skill so the user can also invoke it standalone later.
   - If the user explicitly says "no recap" / "recapいらない" / "サマリー不要" before or
     during the stop, skip this and go straight to the Retrospective.
   - Once `session-recap` returns, surface its output paths to the user in one short
     Japanese line.
3. Then proceed to the Retrospective below (this records feedback on session-watch itself,
   independent of the recap).

### Retrospective

After the monitor is stopped (Step 5), reflect on the session:

1. Consider: were there mid-session corrections (filter widening/narrowing requested,
   explanation style changes, missed events the user had to paste manually, terms the
   user asked you to re-explain that should already have been covered)? Refused/redo?
   Errors talking to Monitor or jq?

2. Ask the user (in Japanese): 「今回の監視のフィードバック (1-5の評価、気になった点、または何もなければEnter)」

3. If the user provides feedback OR if corrections/issues actually occurred during the run:
   a. Create `feedback/` directory next to this SKILL.md if it does not exist.
   b. Read `feedback/log.md` (create with `# Feedback Log` header followed by a blank line
      and the comment `<!-- Append new entries at the top. Do not edit previous entries. -->`
      if it does not exist).
   c. Prepend a new entry directly after the header block, using this format:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this file's frontmatter>
      - **Task**: <1-line description of what the user asked for>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—" if not provided)
      - **Corrections**: <mid-session corrections, or "none">
      - **Issues**: <specific problems, or "none">
      - **User Note**: <user's verbatim feedback, or "—">
      ---
      ```

   d. Save and confirm in one short Japanese sentence.

4. If the user skips AND no corrections or issues occurred, end without recording.

## Behavior Scenarios

```gherkin
Scenario: Default — single session in cwd
  Given the user invokes session-watch with no arguments
  And exactly one Claude Code session is active in the current directory
  When the skill runs Step 1
  Then it picks that session, starts the monitor with the default filter,
       and begins narrating events in Japanese with full term explanations.

Scenario: Multiple sessions in cwd
  Given the user invokes session-watch with no arguments
  And two or more sessions in the current directory have been active in the last 10 minutes
  When the skill runs Step 1
  Then it shows each candidate's session ID, last-activity time, and a one-line preview,
       calls AskUserQuestion to let the user pick one, and starts the monitor on that one.

Scenario: Explicit session ID
  Given the user invokes session-watch with a UUID in the message
  When the skill runs Step 1
  Then it locates that JSONL anywhere under ~/.claude/projects/ regardless of cwd,
       and starts the monitor on that file.

Scenario: No active session
  Given the user invokes session-watch with no arguments
  And no session in cwd has activity within the last 10 minutes
  When the skill runs Step 1
  Then it tells the user no candidate was found and asks for a session ID
       or a different cwd; it does NOT start a monitor.

Scenario: Stop monitoring
  Given a monitor is running
  When the user says "監視やめて" or any equivalent stop phrase
  Then the skill calls TaskStop with the task ID, confirms in Japanese,
       then invokes session-recap with the watched session ID,
       reports the recap output paths, and finally runs the Retrospective.

Scenario: Stop monitoring, user opts out of recap
  Given a monitor is running
  When the user says "監視やめて、recapはいらない" or similar
  Then the skill stops the monitor, skips the session-recap invocation,
       and runs the Retrospective directly.

Scenario: Filter adjustment
  Given a monitor is running with the default filter
  When the user asks to also include Read/Grep events
  Then the skill stops the current monitor and starts a new one with a widened jq filter,
       reusing the same session file.

Scenario: Retrospective recorded after a run with corrections
  Given the user widened the filter mid-run and asked you to re-explain a term you had not glossed
  When the user stops the monitor
  Then the skill asks for a 1-5 rating in Japanese, creates feedback/log.md if missing,
       and prepends an entry capturing the corrections, the user's note, and the outcome.

Scenario: Retrospective skipped on a clean run
  Given the run had no corrections, no issues, and the user provides no feedback
  When the user stops the monitor
  Then the skill ends without writing to feedback/log.md.

Scenario: Feedback Check surfaces a recurring pattern
  Given feedback/log.md has 5+ entries and the same issue keyword appears in 3+ of the last 10
  When the skill is invoked
  Then it tells the user about the pattern and suggests /my-skill-factory improve session-watch,
       then continues normally.
```

## Notes and constraints

- **Read-only.** Never call `claude -p --resume <id>` from within this skill. The skill
  observes; it does not write to the watched session. If the user wants to actually message
  the other session, that is a separate explicit request.
- **No PushNotification spam.** Default to silent narration. Only push for events that
  change what the user would do right now.
- **Sidechain events.** Sub-agent activity is included by default. If the user finds it
  noisy, offer to add a `select($r.isSidechain | not)` clause.
- **Truncated tool inputs.** The transcript truncates large fields. Acknowledge truncation
  when explaining and avoid claiming certainty about content past the cut.
- **Self-watching.** If the user invokes this skill in the same session they want to watch,
  the resulting feedback loop is unsafe (every narration becomes a new event). Detect the
  case (the picked session's most recent event mentions session-watch) and refuse with a
  short explanation.
