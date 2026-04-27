# Moderations

`client.moderations.create` — checks text (and images, on multimodal moderation models) against safety policy categories. Free to call. Use to pre-filter user input before sending to a chat completion, or to flag user-visible content before display.

## Family

`moderation` → `lib/resolveModel.ts moderation`. Resolves to `omni-moderation-latest` today. `text-moderation-*` is deprecated (resolver excludes it via the heuristic preference for `omni-` prefix).

## Permissions

Base perms only:
```
--allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read=$HOME/.openai-cli --allow-write=$HOME/.openai-cli
```

## Per-call TS template

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();

const r = await client.moderations.create({
  model: "RESOLVED_ID",
  input: "INPUT_TEXT_HERE",
});

const result = r.results[0];
console.log(`flagged: ${result.flagged}`);
console.log("categories:");
for (const [cat, on] of Object.entries(result.categories)) {
  if (on) console.log(`  ${cat}: ${result.category_scores[cat as keyof typeof result.category_scores].toFixed(4)}`);
}
console.log(`# meta: model=RESOLVED_ID`);
```

## Multimodal input (image + text)

```typescript
const r = await client.moderations.create({
  model: "RESOLVED_ID",
  input: [
    { type: "text", text: "Caption: ..." },
    { type: "image_url", image_url: { url: "data:image/png;base64,..." } },
  ],
});
```

Add `--allow-read=<image-path>` if reading from disk and base64-encoding.

## Categories (omni-moderation-latest)

The model returns scores for categories like:
- `harassment`, `harassment/threatening`
- `hate`, `hate/threatening`
- `self-harm`, `self-harm/intent`, `self-harm/instructions`
- `sexual`, `sexual/minors`
- `violence`, `violence/graphic`
- `illicit`, `illicit/violent`

Each has a boolean flag and a 0-1 score. `flagged: true` means at least one category exceeded its policy threshold (OpenAI sets the threshold; you can also set your own based on `category_scores`).

## Use as a gate before chat completions

```typescript
const mod = await client.moderations.create({
  model: "RESOLVED_MOD_ID",
  input: userPrompt,
});

if (mod.results[0].flagged) {
  console.error("input flagged by moderation");
  console.error(JSON.stringify(mod.results[0].categories, null, 2));
  Deno.exit(1);
}

// Proceed with chat completion...
```

## Cost

Free. No usage cost as of 2026-04 (verify in OpenAI docs).
