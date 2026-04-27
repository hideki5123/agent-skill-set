---
name: openai-cli
description: >
  Call the OpenAI Platform API from the terminal via TypeScript on deno —
  chat completions, Responses API, reasoning (o-series), embeddings, image
  generation, audio (Whisper transcription, TTS), files, batches, moderation,
  and model listing. Two-tool stack: mise + deno (no node_modules, no pnpm,
  no bash). Models are resolved dynamically per session against
  `client.models.list()` — never hardcoded — and any detected upgrade prompts
  the user via AskUserQuestion (even in auto-mode). Secrets stay outside the
  agent: existence-only key checks, scoped `--allow-env=OPENAI_API_KEY` and
  `--allow-net=api.openai.com` flags, no `.env` files.
  Trigger patterns (match any variation):
  openai / open ai / OpenAI / open-ai api /
  gpt / gpt-5 / gpt-5.5 / o1 / o3 / o4 /
  embeddings / dall-e / gpt-image / image generation / generate image /
  whisper / transcribe audio / speech-to-text /
  tts / text-to-speech / read aloud /
  moderation / content moderation /
  openai cli / openai-cli / call openai / use openai api /
  ask gpt / chat with gpt / openai chat /
  responses api / openai batch / openai files.
  Does NOT access ChatGPT chat history (the API does not expose it; use the
  Settings → Data Controls export instead).
---

# openai-cli

Call OpenAI's Platform API from the terminal. Implementation: TypeScript on **deno** with the official `openai` SDK (consumed via `npm:openai@5` — no `pnpm install`, no `node_modules`). Tool versions pinned via **mise**. Total stack: 2 tools.

## Hard rules

1. **Never hardcode model names** in any TS file you write. Always resolve via `lib/resolveModel.ts <family>` first. See `references/models.md` for family heuristics.
2. **Never read or print secrets.** Use existence checks only. Forbidden: `echo $OPENAI_API_KEY`, `printenv | grep`, `cat ~/.zshrc`, `cat .env`, logging `Authorization` headers. See `references/security.md`.
3. **Always use scoped deno permissions.** Base perms: `--allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read=$HOME/.openai-cli --allow-write=$HOME/.openai-cli`. Add `--allow-read=<input>` and `--allow-write=<output>` per use case — never blanket `--allow-read` / `--allow-net`.
4. **Cross-OS only.** All non-trivial logic lives in `assets/lib/*.ts`. No bash, no PowerShell scripts, no shell heredocs.
5. **Upgrade prompts are mandatory** even in auto-mode / dangerous-permission mode. When `resolveModel.ts` reports `UPGRADE_NEEDED`, you MUST use `AskUserQuestion`.

## Path conventions

- **Skill cache** (read-only, version-pinned): `${CLAUDE_PLUGIN_ROOT}/skills/openai-cli/assets/lib/*.ts`. Use this only for the very first `setup.ts` invocation. `${CLAUDE_PLUGIN_ROOT}` is set when Claude orchestrates the skill; in a plain user shell, resolve to `~/.claude/plugins/cache/hideki-plugins/openai-cli/<version>/skills/openai-cli/assets/lib/`.
- **User workspace** (stable, version-independent): `~/.openai-cli/lib/*.ts`. After `setup.ts` runs once, all skill scripts are copied here. Every command after first-time setup runs from this stable path.

## Preflight (before every call)

```
deno run --allow-env=OPENAI_API_KEY --allow-read --allow-run=mise,deno ~/.openai-cli/lib/preflight.ts
```

If any check fails:
- `mise` missing → instruct platform install and stop. macOS: `brew install mise`. Linux: `curl https://mise.run | sh`. Windows: `winget install jdx.mise`.
- `deno` missing → run `cd ~/.openai-cli && mise install`.
- `workspace` missing → run setup (below).
- `OPENAI_API_KEY` missing → instruct user to export it in their shell rc. **Do not** offer a `.env` fallback.

## First-time setup (run once)

From inside Claude (uses skill cache):
```
deno run --allow-read --allow-write --allow-env --allow-run=mise ${CLAUDE_PLUGIN_ROOT}/skills/openai-cli/assets/lib/setup.ts
```

From a user shell (manual run, version-pinned path):
```
deno run --allow-read --allow-write --allow-env --allow-run=mise ~/.claude/plugins/cache/hideki-plugins/openai-cli/1.0.0/skills/openai-cli/assets/lib/setup.ts
```

`setup.ts` creates `~/.openai-cli/{lib,.cache,tmp}/`, copies `assets/lib/*.ts` into `~/.openai-cli/lib/`, copies the `mise.toml` template into `~/.openai-cli/.mise.toml`, runs `mise trust && mise install`, and existence-checks `OPENAI_API_KEY`.

Then, once `OPENAI_API_KEY` is set, populate `models.json` (uses the stable workspace path now that setup has copied the scripts):

```
deno run --allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --init
```

Full details: `references/setup.md`.

## Per-call workflow

For every API use case:

1. **Preflight** (above). Bail if anything fails.
2. **Resolve the model** for the relevant family:
   ```
   deno run --allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts <family>
   ```
   Where `<family>` is one of: `chat`, `reasoning`, `embeddings`, `image`, `transcription`, `tts`, `moderation`.
   - **Exit 0**: stdout is the resolved model id. Capture it.
   - **Exit 2**: stdout is `UPGRADE_NEEDED:<family>:<current>:<newest>`. Use `AskUserQuestion` with options "Upgrade to `<newest>`", "Stay on `<current>`", "Use `<newest>` just-this-once". Then:
     - On Upgrade: run `deno run --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --set <family> <newest>` and re-run resolve.
     - On Stay: run `deno run --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --set <family> <current>` (refreshes the prompt-suppress timestamp) and use `<current>`.
     - On Just-this-once: skip the `--set`; use `<newest>` for this call only.
   - **Exit 1**: fatal — surface the error and stop.
3. **Write the per-call TS file** under `~/.openai-cli/tmp/<task>-<timestamp>.ts`. Do not invent model names — embed the resolved id from step 2 verbatim. Always include a final log line of the form `# meta: model=<id> usage=<json>` so the user sees what ran.
4. **Estimate cost** if the call may be expensive (input > 5K tokens, output > 1K tokens, batch, multiple images). Surface the estimate and confirm with `AskUserQuestion` before running.
5. **Run with scoped permissions**:
   ```
   deno run --allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read=$HOME/.openai-cli --allow-write=$HOME/.openai-cli [+ I/O scopes for this use case] ~/.openai-cli/tmp/<task>-<timestamp>.ts
   ```
6. **Surface the response** to the user, including the meta line for transparency.

For each endpoint's specific TS template, see the matching reference file (table below).

## Endpoint reference table

| Use case | Family | Reference |
|----------|--------|-----------|
| Chat completion | `chat` | [references/chat.md](references/chat.md) |
| Responses API | `chat` | [references/responses.md](references/responses.md) |
| Reasoning (o-series) | `reasoning` | [references/reasoning.md](references/reasoning.md) |
| Embeddings + similarity | `embeddings` | [references/embeddings.md](references/embeddings.md) |
| Image generation / edit | `image` | [references/images.md](references/images.md) |
| Audio transcription / translation / TTS | `transcription` / `tts` | [references/audio.md](references/audio.md) |
| Files (upload, list, retrieve, delete) | n/a | [references/files-and-batches.md](references/files-and-batches.md) |
| Batches | n/a | [references/files-and-batches.md](references/files-and-batches.md) |
| Moderation | `moderation` | [references/moderations.md](references/moderations.md) |
| Models (list / retrieve) | n/a | [references/models.md](references/models.md) |

For streaming, tool/function calling, structured outputs (zod), see [references/advanced.md](references/advanced.md). For error handling and rate limits: [references/error-handling.md](references/error-handling.md).

## Out of scope

The following are **deliberately deferred** from v1. If the user asks for any of these, surface this list and explain the deferral rather than silently failing:

- [ ] **Fine-tuning** (`client.fineTuning.jobs.*`) — high-cost, error-prone. Likely a separate `openai-finetune` skill in future, with cost gates.
- [ ] **Realtime API** (websocket, voice agents) — stateful and complex. Likely a dedicated `openai-realtime` skill.
- [ ] **Assistants API** (`client.beta.assistants.*`, threads, runs) — **OpenAI is sunsetting this on 2026-08-26**. Note: this is OpenAI's stateful-assistants product, unrelated to Claude or any Claude skill feature. The v1 skill refuses Assistants calls and steers users to the **Responses API**, OpenAI's official migration target.
- [ ] **Vector Stores** — tied to Assistants on the same deprecation track. Same handling.
- [ ] **ChatGPT chat history** — the API does not expose chats from chat.openai.com / mobile / desktop. The only sanctioned route is **Settings → Data Controls → Export Data**, which emails you a ZIP with `conversations.json`. Future work: a separate `chatgpt-export-reader` skill that parses that file locally.
- [ ] **Persistent-process optimization** — currently each `deno run` cold-starts. If session latency becomes a problem, consider `deno compile`-ing a single binary or running a localhost daemon.

## Behavior scenarios

```gherkin
Scenario: Chat completion
  When the user asks the skill a question
  Then the skill returns the model's answer using the per-session-resolved chat model

Scenario: Vision request
  When the user attaches an image and asks for a description
  Then the skill returns the model's description with the image attached as chat content

Scenario: Structured output
  When the user asks for a JSON-shaped response (e.g., extract entities into a schema)
  Then the skill returns a typed object matching the requested shape

Scenario: Embeddings and similarity
  When the user asks to embed N strings and find the closest pair
  Then the skill returns the closest pair and their similarity score

Scenario: Image generation
  When the user asks to generate an image and gives an output path
  Then the skill writes the image file to that path and reports the location

Scenario: Audio transcription
  When the user provides an audio file and asks for a transcript
  Then the skill returns the transcript text and (optionally) writes a .txt/.vtt sidecar

Scenario: Text-to-speech
  When the user asks to convert text to speech and gives an output path
  Then the skill writes the audio file to that path and reports the location

Scenario: Moderation
  When the user asks to moderate a string
  Then the skill returns category scores from the moderation model

Scenario: Batch submission
  When the user asks to run an embedding/completion job over thousands of records
  Then the skill estimates cost, asks for confirmation, submits the batch, and returns the batch ID

Scenario: Cost gate triggered
  When a request would consume substantial tokens (large input, big output, batch)
  Then the skill surfaces a cost estimate and asks for confirmation before sending

Scenario: Newer model detected
  When resolveModel.ts emits UPGRADE_NEEDED
  Then the skill asks the user "Upgrade / Stay / Just-this-once" via AskUserQuestion —
       even in auto-mode or dangerous-permission mode
  And the skill never silently upgrades

Scenario: User pins a specific model
  When the user names an exact model id for a single call
  Then the skill uses that id for this call only and does not update the persisted preference

Scenario: User asks the skill to read the API key
  When the user asks to print or reveal OPENAI_API_KEY
  Then the skill refuses and points the user to their own (non-agent) terminal

Scenario: User asks for ChatGPT chat history
  When the user asks the skill to read their ChatGPT chats
  Then the skill explains that no API exposes that data and describes the Data Controls export route

Scenario: User asks for Assistants API features
  When the user mentions OpenAI's Assistants / Threads / Runs / Vector Stores
  Then the skill explains those are OpenAI products being sunset on 2026-08-26
       (unrelated to Claude or this skill) and steers the user to the Responses API

Scenario: API key missing
  When the user invokes any use case without OPENAI_API_KEY exported
  Then the skill stops and explains how to export the key in their shell rc (no .env fallback)

Scenario: API failure mid-call
  When the OpenAI API returns a rate-limit, auth error, or network failure
  Then the skill surfaces a sanitized error message (no auth header / key value leakage)
       and suggests the appropriate retry or fix
```

## Retrospective

After completing a non-trivial use case, briefly note in `feedback/log.md`:
- What the user asked
- Which family/model resolved
- Any unexpected behavior (rate limit, missing scope, surprising response)

This feeds the improvement loop — see `references/error-handling.md` for the format.
