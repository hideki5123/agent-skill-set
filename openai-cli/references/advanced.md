# Advanced — streaming, tool calls, structured outputs (zod)

## Streaming

For chat completions and Responses API, set `stream: true` and iterate the resulting async iterator. The SDK exposes per-chunk deltas:

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const stream = await client.chat.completions.create({
  model: "RESOLVED_ID",
  messages: [{ role: "user", content: "Tell me a slow story." }],
  stream: true,
});

let model = "";
let outputTokens = 0;
for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta?.content ?? "";
  if (delta) Deno.stdout.writeSync(new TextEncoder().encode(delta));
  if (chunk.model) model = chunk.model;
  // The final chunk usually carries usage when stream_options.include_usage is set.
}
console.log("");
console.log(`# meta: model=${model} streamed=true`);
```

For finer usage tracking, pass `stream_options: { include_usage: true }` and read the `usage` field on the final chunk.

The Responses API streams via `client.responses.stream({ ... })` which gives a higher-level event interface — see SDK docs.

## Tool calls (function calling)

```typescript
const tools = [{
  type: "function" as const,
  function: {
    name: "get_weather",
    description: "Get current weather for a city.",
    parameters: {
      type: "object",
      properties: {
        city: { type: "string" },
        unit: { type: "string", enum: ["c", "f"] },
      },
      required: ["city"],
      additionalProperties: false,
    },
  },
}];

const r = await client.chat.completions.create({
  model: "RESOLVED_ID",
  messages: [{ role: "user", content: "What's the weather in Paris?" }],
  tools,
  tool_choice: "auto",
});

const calls = r.choices[0].message.tool_calls ?? [];
for (const c of calls) {
  if (c.type === "function" && c.function.name === "get_weather") {
    const args = JSON.parse(c.function.arguments);
    console.log(`call: get_weather(${JSON.stringify(args)})`);
    // Execute the tool yourself, then send the result back in a follow-up
    // turn with role: "tool" and tool_call_id: c.id.
  }
}
```

Multi-turn tool flow: append the assistant message with `tool_calls`, then a `role: "tool"` message with the tool's result, then call `create` again with the full history. Repeat until the model emits a normal `content` response.

## Structured outputs (json_schema)

```typescript
const r = await client.chat.completions.create({
  model: "RESOLVED_ID",
  messages: [{ role: "user", content: "Extract entities from: 'Alice met Bob in Paris.'" }],
  response_format: {
    type: "json_schema",
    json_schema: {
      name: "entities",
      strict: true,
      schema: {
        type: "object",
        properties: {
          people: { type: "array", items: { type: "string" } },
          locations: { type: "array", items: { type: "string" } },
        },
        required: ["people", "locations"],
        additionalProperties: false,
      },
    },
  },
});

const obj = JSON.parse(r.choices[0].message.content ?? "{}");
console.log(JSON.stringify(obj, null, 2));
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

`strict: true` constrains the output via grammar — the model cannot emit malformed JSON or extra fields.

## Structured outputs via zod (`openai.beta.chat.completions.parse`)

The SDK has a zod helper that types the parsed output:

```typescript
import OpenAI from "npm:openai@5";
import { z } from "npm:zod@3";
import { zodResponseFormat } from "npm:openai@5/helpers/zod.mjs";

const Entities = z.object({
  people: z.array(z.string()),
  locations: z.array(z.string()),
});

const client = new OpenAI();
const r = await client.beta.chat.completions.parse({
  model: "RESOLVED_ID",
  messages: [{ role: "user", content: "Extract entities from: 'Alice met Bob in Paris.'" }],
  response_format: zodResponseFormat(Entities, "entities"),
});

const obj = r.choices[0].message.parsed;
if (!obj) throw new Error("parse refused or failed");
// obj is typed: { people: string[]; locations: string[] }
console.log(obj.people, obj.locations);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

## Structured outputs (Responses API)

```typescript
const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "Extract entities from: 'Alice met Bob in Paris.'",
  text: {
    format: {
      type: "json_schema",
      name: "entities",
      strict: true,
      schema: { /* same schema as above */ },
    },
  },
});

const obj = JSON.parse(r.output_text);
```

The Responses API also has a zod helper — check the latest SDK docs for `openai.responses.parse` or equivalent. Names sometimes shift between SDK majors.

## Multi-turn streaming with tool calls

This is where flows get genuinely complex. The skill should keep these in single-purpose `~/.openai-cli/tmp/<task>.ts` files rather than trying to compose helpers, until a real abstraction need emerges. See OpenAI's official cookbook for tested templates.

## When NOT to use these patterns

- For trivial one-shot chat: skip streaming. Stream only when the user wants the answer to appear progressively.
- For simple JSON output: use `response_format: { type: "json_object" }` (less strict, simpler) instead of `json_schema`.
- For tool calls with only one tool that always fires: a regular function call in TS is simpler than the round-trip protocol.
