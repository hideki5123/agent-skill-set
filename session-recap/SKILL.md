---
name: session-recap
version: 1.0.0
description: >
  Read a Claude Code session's transcript and produce two markdown artifacts in Japanese:
  a scannable Summary (TL;DR, what got done, key terms with one-line glosses, files touched,
  decisions, open threads) and a complementary Detailed Note (full glossary with definitions,
  chronological flow, command-by-command annotations, pitfalls and lessons). Standalone —
  the user can pass a session ID, or omit to pick from recent sessions in the current
  directory. Also auto-invoked by session-watch after a watch ends. Read-only on the
  transcript. Use when the user says "session recap" / "セッションのまとめ" /
  "セッションサマリ" / "学びをまとめて" / "用語集を作って" / "summarize the session" /
  "recap session" / "session note" / "セッションのノート" / "/session-recap" /
  "セッション解説まとめ".
---

# session-recap

Convert a Claude Code session's transcript JSONL into two markdown artifacts in Japanese:

- **`summary.md`** — scannable cheat sheet: TL;DR, accomplishments, key terms, files,
  decisions, next steps.
- **`note.md`** — companion deep-dive: full glossary, chronological narrative,
  command-by-command annotations, pitfalls.

Both are written so the user can re-skim later and recover everything technical that was
encountered: terms, commands, decisions, gotchas. Assume the user will forget — be explicit.

## Workflow

### Feedback Check

If `feedback/log.md` exists alongside this SKILL.md and has 5 or more entries, read the last
10 entries. If a pattern is apparent (the same issue appears in 3+ entries, or average rating
is below 3):

- Tell the user (in Japanese): 「過去のフィードバックで類似パターンを検出: [簡潔に]。`/my-skill-factory improve session-recap` で改善できます。」
- Continue with normal execution.

### Step 1: Resolve target session

Look at the user's invocation message for any of:

- A bare UUID (8-4-4-4-12 hex) — explicit session ID.
- A path or `--cwd` mention — alternate working directory to scan instead of `$PWD`.
- An `--out <dir>` style argument — output directory override (default
  `~/.claude/session-recaps/`).
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

`session-watch` will pass the session ID directly via the Skill tool's `args`. Use it as
the explicit-ID path above and skip the picker. Output directory still defaults to
`~/.claude/session-recaps/`.

### Step 2: Extract structured events

Run jq once to project the transcript into a compact event stream. Save to a temp file so
subsequent passes are cheap.

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

Also pull session metadata (start time, end time, slug, cwd, version):

```bash
head -1 "$TRANSCRIPT" | jq '{start: .timestamp, cwd, version, slug, gitBranch, sessionId}'
tail -1 "$TRANSCRIPT" | jq '{end: .timestamp}'
grep -c '"type":"assistant"' "$TRANSCRIPT"
grep -c '"type":"user"' "$TRANSCRIPT"
```

### Step 3: Long-transcript handling

If `$TMP` has more than 2000 lines, do not try to load it all into context at once.
Instead:

1. Read in chunks (e.g., 500 events at a time, with `sed -n 'A,Bp'` or `head/tail`).
2. For each chunk, extract: tool calls, decisions (mentions of "let's do X / instead of Y"),
   errors, file edits, and a 1-2 sentence narrative summary.
3. Combine chunk summaries into the final synthesis in Step 4.

For shorter transcripts, read the whole `$TMP` and proceed directly.

### Step 4: Synthesize the artifacts

Produce two files. Both are in Japanese. Use the templates below as scaffolding — adapt
section presence to what the session actually contained (omit "Pitfalls" if there were none,
etc.). Do not invent content; only include what the transcript supports.

#### `summary.md` template

```markdown
# Session Recap: <slug or short-id> — <YYYY-MM-DD>

- **Session ID**: `<full-id>`
- **期間**: `<start ISO>` → `<end ISO>` (`<elapsed>`)
- **cwd**: `<cwd>`
- **イベント総数**: <N> (assistant text: <a>, user: <u>, tool calls: <t>, sidechain: <s>)

## TL;DR
<1-3行で全体を要約>

## 達成したこと
1. <フェーズまたは主要タスク 1>
2. <フェーズまたは主要タスク 2>
...

## 主な用語 (チートシート)
| 用語 | 一行定義 |
|------|----------|
| `<term>` | <gloss> |
...

## 触ったファイル
| パス | 操作 | 一言メモ |
|------|------|----------|
| `<path>` | created / edited / deleted | <note> |

## 注目コマンド
| コマンド | 目的 | 結果 |
|----------|------|------|
| `<cmd>` | <purpose> | <outcome> |

## 決定事項
- **<decision>**: <reasoning>

## 未解決 / 次にやること
- [ ] <item>
```

#### `note.md` template

```markdown
# 詳細ノート: <slug> — <YYYY-MM-DD>

`summary.md` の補完。用語の本格的な定義、時系列の流れ、コマンド逐次解説、つまずきと教訓まで。

## コンテキスト
<2-3段落: ユーザは何を達成しようとしていたか、環境、スコープ、開始地点>

## 用語集

### `<term>`
<2-4行の定義>

**このsessionでの登場文脈**: <なぜ出てきたか、どこで使われたか>

**関連**: <他の用語との関係>

---

### `<term2>`
...

## 時系列の流れ

### Phase 1: <名前>
<narrative — 何をして何が起きたか、判断の根拠>

### Phase 2: <名前>
...

## コマンド逐次解説

### `<short label>`
```bash
<full command>
```
- <flag/構文 1>: <その意味>
- <flag/構文 2>: <その意味>
...

**やったこと**: <出力 / 副作用>
**学び**: <ここから抽出できる一般化>

---

## つまずきと解決

### <pitfall>
- **症状**: <観測されたこと>
- **原因**: <ルートコーズ>
- **対処**: <実際にやった修正>
- **教訓**: <次回に持っていくもの>

## 参照
- <URL 1>
- <URL 2>
```

#### Synthesis rules

- **言語**: 日本語。引用やコマンドはそのままラテン字。
- **専門用語の扱い**: `summary.md` の用語表は1行以内、`note.md` の用語集は段落で説明。
  両方に同じ用語が出るのは正常。`note.md` 側は「これを見れば分かる」レベルまで掘る。
- **コマンド解説**: `note.md` でフラグ・リダイレクト・ヒアドキュメント・パイプの各部分を
  逐一バラす。`summary.md` には省略形だけ。
- **副作用 / 破壊的操作**: push, kill, rm, sudo, network calls, deploy 系は明示的に
  ラベル化 (例: 「副作用: GitHubへのpush」)。
- **truncationの扱い**: transcript で truncated されている入力は、「この部分は省略
  されているため推測」と注記して扱う。
- **sidechain**: sub-agentの呼び出しは note.md の時系列で言及。重要でなければ
  summary.md からは省く。
- **失敗 → 修正パターン**: 「pitfall」項目は最も価値が高い。失敗→診断→修正の流れが
  あればそこを丁寧に記録する。
- **嘘を書かない**: transcript に無い内容は書かない。推測は明示する。

### Step 5: Write files and report

```bash
OUT_BASE=${OUT_DIR:-~/.claude/session-recaps}
DATE=$(date -u +%Y-%m-%d)
SLUG=<extracted slug, or "session" if missing>
DIR="$OUT_BASE/${DATE}_${SHORT}_${SLUG}"
mkdir -p "$DIR"
# Write summary.md and note.md via the Write tool
```

Then tell the user (in Japanese):

- Output directory path
- File names and approximate sizes
- A 2-3 line preview of the TL;DR
- One-line invitation to ask follow-up questions about specific terms or phases

### Retrospective

After the artifacts are written:

1. Consider: were there mid-session corrections (rewrote sections, expanded glossary,
   user pointed out missed terms)? Was the long-transcript chunking needed and did it
   work? Did jq fail on any line?

2. Ask the user (in Japanese): 「今回のrecapのフィードバック (1-5の評価、抜け落ちた点、または何もなければEnter)」

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
  And exactly one session in cwd has any prior activity
  When the skill runs Step 1
  Then it picks that session, extracts events, synthesizes summary.md and note.md
       in Japanese, writes them to ~/.claude/session-recaps/<date>_<short>_<slug>/,
       and reports the paths.

Scenario: Standalone — explicit session ID
  Given the user passes a UUID in the message
  When the skill runs Step 1
  Then it locates the JSONL anywhere under ~/.claude/projects/ regardless of cwd,
       and produces the recap from it.

Scenario: Standalone — multiple recent sessions in cwd
  Given two or more sessions exist in the cwd's project transcript dir
  When the skill runs Step 1
  Then it presents the top 10 by recency via AskUserQuestion (id + slug + line count),
       and recaps the chosen one.

Scenario: Auto-invoked from session-watch
  Given session-watch has just stopped after watching session <X>
  When session-watch invokes session-recap with <X> as the session ID
  Then this skill skips the picker, recaps session <X>, and returns the output paths
       so session-watch can include them in its closing summary.

Scenario: Long transcript
  Given the resolved transcript has more than 2000 events
  When the skill runs Step 3
  Then it reads in chunks, summarizes per-chunk first, and only assembles the final
       artifacts after chunked synthesis.

Scenario: No usable transcript
  Given the resolved JSONL has fewer than 5 events
  When the skill runs Step 4
  Then it produces a minimal summary.md noting the session was too short to extract
       structured learnings, and skips writing note.md.

Scenario: Output directory override
  Given the user passes "--out ~/notes/sessions"
  When the skill runs Step 5
  Then it writes the artifacts under ~/notes/sessions/<date>_<short>_<slug>/.

Scenario: Retrospective on a clean run
  Given the run had no corrections, no issues, and the user provides no feedback
  When Step 5 reports completion
  Then the skill ends without writing to feedback/log.md.

Scenario: Feedback Check surfaces a pattern
  Given feedback/log.md has 5+ entries with a recurring issue keyword in 3+ of the last 10
  When the skill is invoked
  Then it surfaces the pattern in Japanese and suggests /my-skill-factory improve session-recap.
```

## Notes and constraints

- **Read-only on the watched session.** Do not write back into the transcript or message
  the watched session. Only produce markdown artifacts on local disk.
- **Default output dir**: `~/.claude/session-recaps/`. Created if missing.
- **Naming**: `<YYYY-MM-DD>_<short-id>_<slug>/` (slug omitted if not present in transcript).
  `<short-id>` is the first 8 chars of the session UUID.
- **Language**: Japanese in artifact bodies. Frontmatter / headings can mix English where
  natural (e.g., "TL;DR"). Quoted commands and code stay verbatim.
- **No invention**: never describe a tool call or decision that is not present in the
  transcript. When in doubt, say so explicitly.
- **Truncated inputs**: transcript fields can be truncated. Note this when relevant.
- **Sidechain depth**: sub-agent activity is captured but not exhaustively expanded;
  surface their results, not their inner monologue.
- **Idempotent rewrites**: if invoked again on the same session ID, overwrite the previous
  artifacts in the same directory (do not pile up duplicates).
