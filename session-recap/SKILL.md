---
name: session-recap
version: 1.1.1
description: >
  Read a Claude Code session's transcript and produce two markdown artifacts plus a
  meta.json: a scannable Summary (TL;DR, key terms, files, decisions, open threads) and
  a complementary Detailed Note (full glossary, chronological flow, command-by-command
  annotations, pitfalls). The output language follows the watched session's dominant
  language (>= 50% Japanese characters → Japanese, otherwise English; overridable via
  --language). Standalone — pass a session ID, or omit to pick from recent sessions in
  the current directory. After generation, dispatches a configurable chain of follow-up
  skills (default ["recap-to-notion"]) read from ~/.claude/session-recaps/.recap-config.json.
  Owns the manifest schema and runs cleanup of confirmed-uploaded local recap dirs past
  retention. Read-only on the transcript itself. Use when the user says "session recap" /
  "セッションのまとめ" / "セッションサマリ" / "学びをまとめて" / "用語集を作って" /
  "summarize the session" / "recap session" / "session note" / "セッションのノート" /
  "/session-recap" / "セッション解説まとめ" / "recap掃除" / "recap cleanup" / "古いrecap削除".
---

# session-recap

Convert a Claude Code session's transcript JSONL into two markdown artifacts plus a
machine-readable `meta.json`:

- **`summary.md`** — scannable cheat sheet: TL;DR, accomplishments, key terms (with
  cross-file anchor links to detailed definitions), files, decisions, next steps.
- **`note.md`** — companion deep-dive: full glossary with named anchors, chronological
  narrative, command-by-command annotations, pitfalls.
- **`meta.json`** — structured metadata for downstream tools (recap-to-notion, etc.).

Both markdown files are written so the user can re-skim later and recover everything
technical that was encountered. Assume the user will forget — be explicit.

## Workflow

### Phase 0 — Cleanup (runs before generation, including in cleanup-only mode)

Always run this at the start of every invocation. The skill owns the recap manifest and
retention policy. Each `recap-to-X` uploader writes its own entry to the shared
manifest after a successful upload; this skill reads the manifest to decide what is safe
to delete.

1. Read `~/.claude/session-recaps/.recap-config.json` (defaults below if missing):
   ```json
   {
     "chain_after_generate": ["recap-to-notion"],
     "retention_days": 20,
     "retention_minutes_override": null
   }
   ```
2. Read `~/.claude/session-recaps/.manifest.jsonl` (skip if missing).
3. Walk `~/.claude/session-recaps/<YYYY-MM-DD>_*` directories.
4. For each dir:
   - Has at least one manifest entry whose `local_dir` matches this dir? (target type
     does not matter — any successful upload counts as evidence of preservation).
   - Is the dir's `mtime` older than the threshold? Threshold =
     `retention_minutes_override` (if non-null) else `retention_days * 1440` (minutes).
   - Both yes → `rm -rf` the dir. Otherwise → keep.
5. Report deletion count in one line in the UI language.
6. Never touch dotfiles (`.recap-config.json`, `.notion-config.json`,
   `.<other>-config.json`, `.manifest.jsonl`) or non-recap directories.

**Failure handling**:
- A single `rm -rf` failure → log it, skip that dir, continue.
- `.manifest.jsonl` parse error → skip cleanup entirely, notify the user, continue with
  generation and chain dispatch as normal.

**Cleanup-only mode**: if the user invoked the skill with phrasing like `recap掃除`,
`recap cleanup`, `古いrecap削除`, or with an explicit `--cleanup-only` flag, run Phase 0
and return immediately. Do not generate, do not chain.

### Feedback Check

If `feedback/log.md` exists alongside this SKILL.md and has 5 or more entries, read the
last 10. If a pattern is apparent (the same issue appears in 3+ entries, or average
rating is below 3):

- Tell the user (in the UI language): 「過去のフィードバックで類似パターンを検出: [簡潔に]。`/my-skill-factory improve session-recap` で改善できます。」 / English equivalent.
- Continue with normal execution.

### Step 1: Resolve target session

Look at the user's invocation message for any of:

- A bare UUID (8-4-4-4-12 hex) — explicit session ID.
- A path or `--cwd` mention — alternate working directory to scan instead of `$PWD`.
- An `--out <dir>` style argument — output directory override (default
  `~/.claude/session-recaps/`).
- `--language ja` / `--language en` — force the output language.
- `--no-chain` — skip the chain dispatch in Step 6.
- Otherwise → scan the current working directory's project transcript folder.

#### If a session ID was given

```bash
find ~/.claude/projects -maxdepth 2 -name "<session-id>.jsonl" 2>/dev/null
```

If found → use it. If not → tell the user the ID was not seen anywhere under
`~/.claude/projects/` and stop.

#### If no session ID was given (default)

1. Encode the target cwd: replace every `/` with `-`. Example:
   `/Users/alice/code/foo` → `-Users-alice-code-foo`.
2. The transcript directory is `~/.claude/projects/<encoded>/`.
3. List the 10 most recent sessions with their slug and last-event timestamp:

   ```bash
   ENC=$(echo "$PWD" | sed 's|/|-|g')
   DIR=~/.claude/projects/$ENC
   ls -t "$DIR"/*.jsonl 2>/dev/null | head -10 | while read f; do
     id=$(basename "$f" .jsonl)
     last=$(tail -1 "$f" | jq -r '.timestamp // "?"')
     slug=$(grep -m1 -o '"slug":"[^"]*"' "$f" | head -1 | sed 's/"slug":"//;s/"$//')
     msgs=$(wc -l < "$f")
     echo "$id | $last | $slug | $msgs lines"
   done
   ```

4. Pick:
   - **0 candidates** → tell the user no session was found in this directory; suggest
     passing a session ID or a different cwd.
   - **1 candidate** → use it; show the session ID + slug for confirmation.
   - **2+ candidates** → invoke `AskUserQuestion` with the list (session ID, last
     activity, slug, line count). Let the user pick.

#### When invoked from session-watch

`session-watch` passes the session ID directly via the Skill tool's `args`. Use it as
the explicit-ID path above and skip the picker.

### Step 2: Extract structured events

Run jq once to project the transcript into a compact event stream. Save to a temp file
so subsequent passes are cheap.

```bash
TRANSCRIPT=<resolved-jsonl-path>
SHORT=$(basename "$TRANSCRIPT" .jsonl | cut -c1-8)
TMP=/tmp/session-recap-$SHORT.events.jsonl

jq -c '
  . as $r |
  if $r.type == "user" then
    {kind: "user", ts: $r.timestamp, sc: $r.isSidechain,
     content: ($r.message.content // "")}
  elif $r.type == "assistant" then
    ($r.message.content // [])[]? |
    if .type == "text" then
      {kind: "text", ts: $r.timestamp, sc: $r.isSidechain, text: .text}
    elif .type == "tool_use" then
      {kind: "tool", ts: $r.timestamp, sc: $r.isSidechain,
       name: .name, input: .input}
    else empty end
  else empty end
' "$TRANSCRIPT" > "$TMP"

wc -l "$TMP"
```

Also pull session metadata:

```bash
head -1 "$TRANSCRIPT" | jq '{started_at: .timestamp, cwd, version, slug, gitBranch, sessionId}'
tail -1 "$TRANSCRIPT" | jq '{ended_at: .timestamp}'
grep -c '"type":"assistant"' "$TRANSCRIPT"
grep -c '"type":"user"' "$TRANSCRIPT"
```

### Step 3: Detect output language

Unless `--language` was passed (use as-is), determine the output language from the
transcript:

1. Concatenate all assistant text content (the `kind: "text"` events from `$TMP`).
2. Count Hiragana (U+3040-U+309F), Katakana (U+30A0-U+30FF), and CJK Unified Ideograph
   (U+4E00-U+9FFF) characters as "Japanese".
3. Count ASCII letters (a-z, A-Z) as "English".
4. If `Japanese / (Japanese + English) >= 0.5` → output language = `ja`.
   Otherwise → `en`.
5. If both counts are zero (or transcript is empty) → fall back to `en`.

The detected language is stored in `meta.json` and used to drive Step 4 templates.

### Step 4: Long-transcript handling

If `$TMP` has more than 2000 lines, do not load it all into context at once:

1. Read in chunks (e.g., 500 events at a time, with `sed -n 'A,Bp'` or `head/tail`).
2. For each chunk extract: tool calls, decisions ("let's do X / instead of Y"), errors,
   file edits, and a 1-2 sentence narrative summary.
3. Combine chunk summaries into the final synthesis in Step 5.

For shorter transcripts, read the whole `$TMP` and proceed directly.

### Step 5: Synthesize the artifacts

Produce three files. The two markdown files are in the language detected in Step 3.

#### Output language note

- Quoted commands, file paths, code blocks, and proper nouns stay verbatim regardless of
  language.
- Section headings, prose, term definitions, decisions, narratives are in the chosen
  language.
- The Japanese template below is shown as the primary example; for English output, use
  obvious analogues (e.g. "TL;DR" stays, "達成したこと" → "What got done", "用語集"
  → "Glossary", "コマンド逐次解説" → "Commands annotated", "つまずきと解決" →
  "Pitfalls", etc.).

#### Cross-file anchor link convention

The two files must remain navigable in any standard markdown viewer (GitHub, VS Code,
mdcat, etc.) even if Notion sync is unavailable.

- In `summary.md`, every key term and key command links to its full definition in
  `note.md` using a **cross-file anchor**: `[label](./note.md#anchor-id)`.
- Anchor IDs use kebab-case lowercase. Conventions:
  - Term: `#<term-slug>` (e.g. `#derivation`, `#flake`)
  - Command: `#cmd-<short-label>` (e.g. `#cmd-nix-build`, `#cmd-git-add-a`)
  - Pitfall: `#pitfall-<short-label>`
  - Phase: `#phase-<n>-<short-label>`
- In `note.md`, **a heading must always carry an explicit `{#kebab-id}` whenever its
  rendered text contains anything other than `[a-z0-9-]`** — that is, dots,
  underscores, slashes, spaces with mixed case, backticks, parentheses, dollar signs,
  uppercase letters, etc. Standard markdown sluggers (GitHub, VS Code, mdBook, Pandoc)
  disagree on how to slugify these, so without an explicit ID the cross-file links in
  `summary.md` will silently break. Examples:
  - `### derivation` — plain alphanumeric, auto-slug `derivation` is reliable, no
    `{#…}` needed.
  - `### home.sessionPath {#home-sessionpath}` — has a dot AND mixed case, must
    declare ID explicitly.
  - `### system.defaults.finder {#system-defaults-finder}` — has dots, must declare.
  - `### \`hm-session-vars.sh\` {#hm-session-vars-sh}` — has backticks and a dot.
  - `### \`nix build <flake>#<output>\` {#cmd-nix-build}` — has angle brackets and `#`.
  When in doubt, add the `{#…}` — it never hurts and always makes the link resolve in
  every renderer.

When recap-to-notion later merges these into a single Notion page, it rewrites the
cross-file `(./note.md#x)` form into same-page `(#x)` form. The local files keep
working independently.

#### `summary.md` template (Japanese variant — adapt to English when language=en)

```markdown
# Session Recap: <slug or short-id> — <YYYY-MM-DD>

- **Session ID**: `<full-id>`
- **期間**: `<started_at>` → `<ended_at>` (`<elapsed>`)
- **cwd**: `<cwd>`
- **イベント総数**: <N> (assistant text: <a>, user: <u>, tool calls: <t>, sidechain: <s>)

## TL;DR
<1-3行で全体を要約>

## 達成したこと
1. <フェーズまたは主要タスク 1>
2. <フェーズまたは主要タスク 2>

## 主な用語 (チートシート)
| 用語 | 一行定義 |
|------|----------|
| [`derivation`](./note.md#derivation) | <gloss> |
| [`flake`](./note.md#flake) | <gloss> |

## 触ったファイル
| パス | 操作 | 一言メモ |
|------|------|----------|
| `<path>` | created / edited / deleted | <note> |

## 注目コマンド
| コマンド | 目的 | 結果 |
|----------|------|------|
| [`nix build ...`](./note.md#cmd-nix-build) | <purpose> | <outcome> |

## 決定事項
- **<decision>**: <reasoning>

## 未解決 / 次にやること
- [ ] <item>
```

#### `note.md` template

```markdown
# 詳細ノート: <slug> — <YYYY-MM-DD>

`summary.md` の補完。

## コンテキスト
<2-3段落>

## 用語集

### derivation
<2-4行の定義>

**このsessionでの登場文脈**: <文脈>

**関連**: <他の用語>

---

### flake
...

## 時系列の流れ

### Phase 1: <名前> {#phase-1-<short-label>}
<narrative>

## コマンド逐次解説

### `nix build <flake>#<output>` {#cmd-nix-build}
\`\`\`bash
<full command>
\`\`\`
- <flag/構文 1>: <意味>
- <flag/構文 2>: <意味>

**やったこと**: <出力 / 副作用>
**学び**: <一般化>

---

## つまずきと解決

### <pitfall> {#pitfall-<short-label>}
- **症状**: <観測>
- **原因**: <ルートコーズ>
- **対処**: <修正>
- **教訓**: <次回に持っていくもの>

## 参照
- <URL 1>
```

#### `meta.json` schema (machine-readable)

Write this alongside the two markdown files. Downstream skills (recap-to-notion etc.)
read it instead of re-parsing markdown.

```json
{
  "session_id": "<uuid>",
  "short_id": "<8 chars>",
  "slug": "<slug or empty>",
  "cwd": "<absolute path>",
  "language": "ja",
  "started_at": "<ISO-8601 with time and timezone>",
  "ended_at": "<ISO-8601 with time and timezone>",
  "duration_seconds": 1234,
  "total_events": 290,
  "events": {"user": 12, "assistant_text": 45, "tool": 200, "sidechain": 33},
  "generator_version": "1.1.0"
}
```

#### Synthesis rules

- **Output language**: matches the result of Step 3 (or `--language` override).
- **Term cross-references**: every term that appears in `summary.md`'s 用語表 must have
  a corresponding `### <term>` heading in `note.md` and link to it via
  `[term](./note.md#term-slug)`. Same for commands.
- **Command breakdown**: in `note.md`, decompose flags, redirections, heredocs, pipes
  one by one. In `summary.md` keep entries one-line.
- **Side effects / destructive ops**: push, kill, rm, sudo, network calls, deploys are
  surfaced explicitly (e.g. "副作用: GitHubへのpush" / "side effect: git push to GitHub").
- **Truncation**: when transcript content is truncated, note "省略あり" / "truncated"
  and avoid claiming certainty about content past the cut.
- **Sidechain**: sub-agent activity goes into note.md timeline; surface results, not
  inner monologue.
- **Failure → fix patterns**: pitfalls are the highest-value content. Always record
  symptom → root cause → fix → lesson.
- **Never invent**: only describe tool calls / decisions actually present in the
  transcript.

### Step 5b: Write files and report

```bash
OUT_BASE=${OUT_DIR:-~/.claude/session-recaps}
DATE=$(date -u +%Y-%m-%d)
SLUG=<extracted slug, or "session" if missing>
DIR="$OUT_BASE/${DATE}_${SHORT}_${SLUG}"
mkdir -p "$DIR"
# Use the Write tool to create:
#   $DIR/summary.md
#   $DIR/note.md
#   $DIR/meta.json
```

Then tell the user (in UI language):
- Output directory path
- File names + approximate sizes
- A 2-3 line preview of the TL;DR
- One-line invitation to ask follow-ups about specific terms or phases

### Step 6 — Chain dispatch

After local files are written, dispatch any user-configured follow-up skills.

1. Read `~/.claude/session-recaps/.recap-config.json` (default
   `chain_after_generate = ["recap-to-notion"]` if file is missing).
2. Determine if the chain should be skipped:
   - `--no-chain` argument was passed → skip.
   - The user's recent invocation contains any of these opt-out phrases → skip:
     `アップロードしないで`, `Notionいらない`, `ローカルだけ`,
     `no upload`, `skip notion`, `local only`, `no chain`.
   - `chain_after_generate` is an empty list `[]` → skip (no-op).
3. Otherwise, for each skill name in the list, in order:
   - Verify it is installed (skill list lookup). If not, emit a one-line skip note in
     UI language and continue with the next.
   - Invoke `Skill(skill: "<name>", args: "<absolute path to recap dir>")`.
   - Surface the returned one-line status in UI language.
4. The chain runs sequentially. A failure in one chain skill does not stop the others
   (they are independent).

This skill never references `recap-to-notion` (or any other uploader) by name in the
code path — only the names listed in the user's `.recap-config.json`. Adding a new
uploader is a config change, not a source change.

### Retrospective

After Step 6 returns:

1. Consider: were there mid-session corrections (rewrote sections, expanded glossary,
   user pointed out missed terms)? Did chain dispatch fail anywhere? Did jq fail on
   any line?
2. Ask the user (in UI language): 「今回のrecapのフィードバック (1-5の評価、抜け落ちた点、または何もなければEnter)」 / English equivalent.
3. If feedback OR corrections occurred:
   a. Create `feedback/` next to this SKILL.md if missing.
   b. Read or create `feedback/log.md` with the standard header.
   c. Prepend a new entry:

      ```markdown
      ## <ISO-8601 timestamp>
      - **Skill Version**: <version from this file's frontmatter>
      - **Task**: <1-line description>
      - **Outcome**: success | partial-success | failure | error
      - **Rating**: <N>/5 (or "—")
      - **Corrections**: <session corrections, or "none">
      - **Issues**: <issues, or "none">
      - **User Note**: <verbatim, or "—">
      ---
      ```

4. Skip recording if the user passes AND no corrections/issues occurred.

## Behavior Scenarios

```gherkin
Scenario: Standalone — single recent session in cwd
  Given the user invokes session-recap with no arguments
  And exactly one session in cwd has prior activity
  When Step 1 runs
  Then the skill picks that session, generates summary.md / note.md / meta.json
       under ~/.claude/session-recaps/<date>_<short>_<slug>/, and dispatches the
       configured chain.

Scenario: Standalone — explicit session ID
  Given the user passes a UUID in the message
  When Step 1 runs
  Then the skill locates the JSONL anywhere under ~/.claude/projects/ regardless
       of cwd, and produces the recap from it.

Scenario: Standalone — multiple recent sessions in cwd
  Given two or more sessions exist in the cwd's project transcript dir
  When Step 1 runs
  Then the skill presents the top 10 by recency via AskUserQuestion and recaps
       the chosen one.

Scenario: Auto-invoked from session-watch
  Given session-watch has just stopped after watching session <X>
  When session-watch invokes session-recap with <X> as the session ID
  Then this skill generates the recap and dispatches the configured chain.

Scenario: Output language matches session — Japanese >= 50%
  Given the watched session's assistant text is dominantly Japanese
  When Step 3 runs
  Then language is set to "ja" and the artifacts are produced in Japanese.

Scenario: Output language defaults to English when Japanese < 50%
  Given the watched session is mostly English
  When Step 3 runs
  Then language is set to "en" and the artifacts are produced in English.

Scenario: --language argument overrides automatic detection
  Given the user passes --language ja against an English session
  Then artifacts are produced in Japanese regardless of the detected ratio.

Scenario: Local cross-file anchors work in standard markdown viewers
  Given a recap was generated and Notion sync was skipped or failed
  When the user opens summary.md in VS Code or GitHub
  Then clicking a term link navigates to the corresponding heading in note.md.

Scenario: Chain dispatch — default chain runs recap-to-notion
  Given .recap-config.json is missing or chain is the default
  When Step 6 runs
  Then session-recap invokes recap-to-notion with the recap dir absolute path
       and surfaces its one-line status.

Scenario: Chain dispatch — skipped when user says "no upload" or similar
  Given the user's invocation contains an opt-out phrase
  When Step 6 evaluates skip conditions
  Then the chain is fully skipped.

Scenario: Chain dispatch — skipped via --no-chain argument
  Given --no-chain was passed
  When Step 6 runs
  Then the chain is fully skipped.

Scenario: Chain dispatch — empty chain in .recap-config.json runs no follow-up
  Given chain_after_generate is []
  When Step 6 runs
  Then no chain skills are invoked.

Scenario: Chain dispatch — chained skill not installed → log and continue
  Given the chain references a skill that is not installed
  When Step 6 attempts to invoke it
  Then the skill emits a one-line skip note and proceeds to the next chain entry.

Scenario: Cleanup — confirmed in manifest + past retention → deleted
  Given a recap dir has at least one manifest entry
  And its mtime is older than the retention threshold
  When Phase 0 runs
  Then the dir is deleted and the count is reported.

Scenario: Cleanup — confirmed in manifest + within retention → kept
  Given a recap dir has at least one manifest entry
  And its mtime is within the retention threshold
  When Phase 0 runs
  Then the dir is kept.

Scenario: Cleanup — no manifest entry + past retention → kept
  Given a recap dir has no manifest entry of any target
  When Phase 0 runs
  Then the dir is kept regardless of age.

Scenario: Cleanup-only mode — invoked via "recap cleanup" runs Phase 0 only
  Given the user invokes the skill with "recap cleanup" or similar
  When the skill starts
  Then it runs Phase 0 and exits without generating or chaining.

Scenario: Cleanup never touches dotfiles or non-recap directories
  Given .recap-config.json, .notion-config.json, .manifest.jsonl exist alongside dirs
  When Phase 0 runs
  Then only directories matching <YYYY-MM-DD>_* are considered for deletion.

Scenario: Long transcript
  Given the resolved transcript has more than 2000 events
  When Step 4 runs
  Then chunked synthesis is used.

Scenario: No usable transcript
  Given the resolved JSONL has fewer than 5 events
  When Step 5 runs
  Then a minimal summary.md is produced and note.md is skipped.

Scenario: Output directory override
  Given the user passes --out ~/notes/sessions
  When Step 5b runs
  Then artifacts are written under ~/notes/sessions/<date>_<short>_<slug>/.

Scenario: Retrospective on a clean run
  Given no corrections, no issues, and no user feedback
  When the Retrospective runs
  Then nothing is written to feedback/log.md.

Scenario: Feedback Check surfaces a pattern
  Given feedback/log.md has 5+ entries with a recurring issue keyword
  When the skill is invoked
  Then it surfaces the pattern in UI language and suggests
       /my-skill-factory improve session-recap.
```

## Notes and constraints

- **Read-only on the watched session.** Do not write back into the transcript or
  message the watched session.
- **Default output dir**: `~/.claude/session-recaps/`.
- **Naming**: `<YYYY-MM-DD>_<short-id>_<slug>/` (slug omitted if not present).
  `<short-id>` is the first 8 chars of the session UUID.
- **No invention**: never describe a tool call or decision that is not present in the
  transcript. When in doubt, say so explicitly.
- **Truncated inputs**: transcript fields can be truncated; mark them.
- **Sidechain depth**: sub-agent activity is captured but not exhaustively expanded.
- **Idempotent rewrites**: invoking again on the same session ID overwrites the
  previous artifacts in the same directory (no duplicates).
- **Manifest is shared**: each `recap-to-X` uploader appends an entry on success. This
  skill defines the schema and reads the file for cleanup; uploaders only append.
- **Manifest schema** (`~/.claude/session-recaps/.manifest.jsonl`, append-only):
  ```jsonl
  {"target": "<name>", "session_id": "<uuid>", "local_dir": "<absolute path>", "target_id": "<id>", "target_url": "<url>", "uploaded_at": "<ISO-8601 with time>", "status": "created"|"updated"}
  ```
- **Cleanup policy**: a recap dir is deletable if it has at least one manifest entry
  (regardless of target) AND mtime exceeds the retention threshold. This is intentional
  — we trust that any successful upload preserves the data.
- **OCP**: adding a new uploader (e.g. `recap-to-confluence`) requires no edits to this
  skill's source. The user adds the new skill name to `chain_after_generate` in their
  `.recap-config.json`.
