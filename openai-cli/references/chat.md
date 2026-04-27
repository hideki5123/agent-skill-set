# Chat completions

`client.chat.completions.create` — the workhorse endpoint for conversational requests. The Responses API (`references/responses.md`) is the newer, recommended endpoint for greenfield code, but Chat Completions remains widely used and fully supported.

## Family

`chat` → `lib/resolveModel.ts chat`. As of 2026-04, this resolves to `gpt-5.5` (1M context, image input, prompt caching). The resolver picks newest stable; the literal id will drift over time.

## Permissions for the per-call script

```
--allow-env=OPENAI_API_KEY
--allow-net=api.openai.com
--allow-read=$HOME/.openai-cli
--allow-write=$HOME/.openai-cli
```

Add `--allow-read=<image-path>` if attaching a local image, etc.

## Per-call TS template

After resolving via `lib/resolveModel.ts chat` → say it returned `RESOLVED_ID`. Write this to `~/.openai-cli/tmp/chat-<timestamp>.ts`:

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();   // SDK reads OPENAI_API_KEY from env (deno-permitted)

const r = await client.chat.completions.create({
  model: "RESOLVED_ID",   // <- substituted by the orchestrator, not hardcoded
  messages: [
    { role: "system", content: "You are a concise assistant." },
    { role: "user", content: "USER_PROMPT_HERE" },
  ],
});

const text = r.choices[0]?.message?.content ?? "";
console.log(text);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

## Vision (multimodal input)

For image input, embed via `image_url` content parts. Local files need to be read and base64-encoded by the script (which requires `--allow-read=<image-path>`):

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const imgPath = "INPUT_IMAGE_PATH";
const bytes = await Deno.readFile(imgPath);
const b64 = btoa(String.fromCharCode(...bytes));
const mime = imgPath.endsWith(".png") ? "image/png" :
             imgPath.endsWith(".jpg") || imgPath.endsWith(".jpeg") ? "image/jpeg" :
             imgPath.endsWith(".webp") ? "image/webp" : "image/png";

const r = await client.chat.completions.create({
  model: "RESOLVED_ID",
  messages: [{
    role: "user",
    content: [
      { type: "text", text: "Describe this image." },
      { type: "image_url", image_url: { url: `data:${mime};base64,${b64}` } },
    ],
  }],
});

console.log(r.choices[0]?.message?.content ?? "");
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

For HTTPS image URLs, pass them directly without base64 — but you'll need `--allow-net=api.openai.com,<image-host>` to allow the OpenAI server to fetch (in some flows you embed a URL and OpenAI fetches; in others the SDK fetches).

## Common parameters

| Param | Notes |
|-------|-------|
| `temperature` | 0–2. Lower = more deterministic. Default 1. Set to 0 for reproducible extractions. |
| `max_completion_tokens` | Cap on output. Useful for cost control. |
| `top_p` | Alternative to temperature; usually leave at 1. |
| `seed` | Best-effort reproducibility (still not guaranteed). |
| `presence_penalty` / `frequency_penalty` | Discourage token repetition. Rarely needed for modern models. |
| `response_format` | `{ type: "json_object" }` or `{ type: "json_schema", json_schema: {...} }` for structured output. See `references/advanced.md`. |
| `tools` / `tool_choice` | Function calling. See `references/advanced.md`. |
| `stream` | Set true to receive an async iterator of chunks. See `references/advanced.md`. |

## Cost-awareness

Trigger the cost-gate (in SKILL.md) when any of:
- Input tokens > 5K (rough estimate via word count × 1.3)
- `max_completion_tokens` > 1K
- Multiple images attached (each image costs ~1.4K tokens for `gpt-5.5`)

Surface a rough estimate (input × `$/1M-input-tokens` + output × `$/1M-output-tokens`) and confirm via `AskUserQuestion` before sending. Pricing changes — link the user to https://openai.com/api/pricing/ rather than baking rates into the skill.

## Logging the meta line

Every chat-completion script must end with:
```typescript
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

This gives the user (and the feedback log) a per-call audit trail.
