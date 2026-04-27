# Responses API

`client.responses.create` — OpenAI's newer, stateful endpoint. Recommended migration target for code currently on the **Assistants API** (which is being sunset on 2026-08-26). For greenfield code, the Responses API is the preferred starting point over Chat Completions when you want server-side conversation state, hosted tools (web search, code interpreter, file search), or unified handling of text + reasoning + tool calls.

## Family

`chat` (same family as Chat Completions — both consume the chat-class models). `lib/resolveModel.ts chat` returns the resolved id.

## Permissions

Base perms (`--allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read=$HOME/.openai-cli --allow-write=$HOME/.openai-cli`). Add I/O scopes if reading inputs or writing outputs.

## Per-call TS template (one-shot)

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();

const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "USER_PROMPT_HERE",
});

console.log(r.output_text);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

`r.output_text` is a convenience accessor that flattens the response's text segments. For more granular access (reasoning, tool calls, structured output parts), iterate `r.output`.

## Stateful conversation via `previous_response_id`

```typescript
// Turn 1
const r1 = await client.responses.create({
  model: "RESOLVED_ID",
  input: "Tell me a joke about deno.",
});
console.log(r1.output_text);
console.log(`# meta: response_id=${r1.id}`);

// Turn 2 — chained via previous_response_id
const r2 = await client.responses.create({
  model: "RESOLVED_ID",
  previous_response_id: r1.id,
  input: "Now make it about TypeScript permissions.",
});
console.log(r2.output_text);
```

The skill can persist the most recent `response_id` to `~/.openai-cli/tmp/last-response.txt` so follow-ups can find it. Keep the file scope inside the workspace so `--allow-write=$HOME/.openai-cli` covers it.

## Hosted tools

The Responses API supports server-side tools without you wiring them up:

```typescript
const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "What's the latest deno release?",
  tools: [{ type: "web_search" }],
});
```

Available tool types (subject to change — verify in OpenAI docs):
- `web_search` — server-side web browsing
- `file_search` — search uploaded files (uses Vector Stores under the hood; note Vector Stores tied to Assistants are sunsetting 2026-08-26)
- `code_interpreter` — sandboxed Python execution
- Custom function tools — same shape as Chat Completions

## Reasoning effort

For chat-family models that have a reasoning mode (e.g., `gpt-5.5`):

```typescript
const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "Analyze this proof: ...",
  reasoning: { effort: "high" },   // "minimal" | "low" | "medium" | "high"
});
```

Higher effort = more thinking time, more tokens, better answers on hard problems. See `references/reasoning.md` for the o-series and the reasoning-mode comparison.

## Structured output

```typescript
const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "Extract the entities from: 'Alice met Bob in Paris.'",
  text: {
    format: {
      type: "json_schema",
      name: "entities",
      schema: {
        type: "object",
        properties: {
          people: { type: "array", items: { type: "string" } },
          locations: { type: "array", items: { type: "string" } },
        },
        required: ["people", "locations"],
        additionalProperties: false,
      },
      strict: true,
    },
  },
});
const parsed = JSON.parse(r.output_text);
```

For ergonomic zod-based schemas, see `references/advanced.md`.

## Why prefer Responses over Chat Completions for new work

- Server-side state (no need to track `messages` arrays client-side).
- Built-in hosted tools (no need to implement web_search yourself).
- Unified output structure across text, reasoning, tool calls.
- It's the official migration target post-Assistants-sunset.

But Chat Completions is fine for stateless one-shot calls, and is more universally documented.
