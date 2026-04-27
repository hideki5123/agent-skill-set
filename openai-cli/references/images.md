# Image generation

`client.images.generate` / `.edit` / (variations are deprecated for `gpt-image-*` models). As of 2026-04, the latest is **`gpt-image-2`** (released 2026-04-21) — token-based pricing, 50% discount via Batch API. `gpt-image-1` and `dall-e-*` are deprecated.

## Family

`image` → `lib/resolveModel.ts image`. Resolves to `gpt-image-2` today.

## Permissions

Base perms PLUS `--allow-write=<output-path>` for the image file:

```
--allow-env=OPENAI_API_KEY
--allow-net=api.openai.com
--allow-read=$HOME/.openai-cli
--allow-write=$HOME/.openai-cli
--allow-write=<absolute-output-path>
```

For a path under `$HOME/Downloads`, use `--allow-write=$HOME/Downloads/<filename>` (or scope to the directory: `--allow-write=$HOME/Downloads`).

## Per-call TS template (generation)

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const outPath = "ABSOLUTE_OUTPUT_PATH";   // skill substitutes user's path

const r = await client.images.generate({
  model: "RESOLVED_ID",
  prompt: "USER_PROMPT_HERE",
  n: 1,
  size: "1024x1024",        // also supported: 1024x1536, 1536x1024, etc.
  quality: "high",          // low | medium | high (varies by model)
  response_format: "b64_json",
});

const b64 = r.data[0].b64_json;
if (!b64) throw new Error("no image data returned");
const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
await Deno.writeFile(outPath, bytes);

console.log(`wrote ${outPath} (${bytes.length} bytes)`);
console.log(`# meta: model=RESOLVED_ID prompt_tokens=${r.usage?.input_tokens ?? "?"}`);
```

> **Why `b64_json` over `url` response_format**: deno's `--allow-net=api.openai.com` forbids outbound fetches to OpenAI's CDN URLs (which use `*.oaistatic.com` or similar). Base64 returns the bytes inline so we never need a second network call.

## Image edit (with mask)

```typescript
const image = await Deno.open("INPUT_IMAGE_PATH");      // PNG with the area to edit
const mask = await Deno.open("MASK_IMAGE_PATH");        // PNG, same size, transparent in edit area

const r = await client.images.edit({
  model: "RESOLVED_ID",
  image: image.readable,
  mask: mask.readable,
  prompt: "Replace the masked area with ...",
  n: 1,
  size: "1024x1024",
  response_format: "b64_json",
});

// Same write pattern as above
```

Add `--allow-read=<input-image-path>` and `--allow-read=<mask-path>` to the permission flags.

## Cost-awareness

`gpt-image-2` is **token-priced** (input prompt tokens + output image tokens). High-quality 1024×1024 images cost $0.05-0.15 each as of 2026; 1536-side and high-quality variants more. For batches of >5 images, use the **Batches API** for 50% off — see `references/files-and-batches.md`.

Always trigger the cost gate when:
- `n > 1`
- Size larger than 1024×1024
- `quality === "high"` and `n >= 2`

## Sizes (`gpt-image-2`)

| Size | Aspect | Use |
|------|--------|-----|
| 1024x1024 | square | default |
| 1024x1536 | portrait | tall |
| 1536x1024 | landscape | wide |

Older sizes (`512x512`, `256x256`) belonged to `dall-e-2` and are not available on `gpt-image-2`.

## Variations

`client.images.createVariation` exists for `dall-e-2` only — deprecated. Don't use in v1; if a user wants a variation of a `gpt-image-2` image, ask them to write a new prompt referencing the original concept and use `images.generate` again.
