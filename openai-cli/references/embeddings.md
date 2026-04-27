# Embeddings

`client.embeddings.create` — returns dense vector representations of text. Use for similarity search, clustering, classification, retrieval-augmented generation.

## Family

`embeddings` → `lib/resolveModel.ts embeddings`. Resolves to `text-embedding-3-large` today (3072 dimensions). Resolver tie-breaker prefers `*-large` over `*-small`.

## Permissions

Base perms only:
```
--allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read=$HOME/.openai-cli --allow-write=$HOME/.openai-cli
```

## Per-call TS template (single input)

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();

const r = await client.embeddings.create({
  model: "RESOLVED_ID",
  input: "INPUT_TEXT_HERE",
});

const v = r.data[0].embedding;
console.log(`dim=${v.length} preview=${v.slice(0, 5).map((x) => x.toFixed(4)).join(",")}...`);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

## Batched inputs (preferred for ≥2 strings)

The API accepts an array of inputs in one request — much cheaper than N round-trips:

```typescript
const inputs = ["string A", "string B", "string C"];
const r = await client.embeddings.create({
  model: "RESOLVED_ID",
  input: inputs,
});
const vectors = r.data.map((d) => d.embedding);
console.log(`embedded ${vectors.length} items, dim=${vectors[0].length}`);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

Embeddings APIs typically accept up to 2048 inputs per request and ~8K tokens per input — verify in the OpenAI docs for the current model.

## Cosine similarity helper

```typescript
function cosineSim(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}
```

## "Find the closest pair" — common use case

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const inputs = ["INPUT_1", "INPUT_2", "INPUT_3"];   // skill substitutes user's strings

const r = await client.embeddings.create({
  model: "RESOLVED_ID",
  input: inputs,
});
const v = r.data.map((d) => d.embedding);

function cosineSim(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

let best = { i: 0, j: 0, sim: -1 };
for (let i = 0; i < v.length; i++) {
  for (let j = i + 1; j < v.length; j++) {
    const s = cosineSim(v[i], v[j]);
    if (s > best.sim) best = { i, j, sim: s };
  }
}

console.log(`closest pair: [${best.i}] "${inputs[best.i]}" ~ [${best.j}] "${inputs[best.j]}" (cos=${best.sim.toFixed(4)})`);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

## Dimension reduction

`text-embedding-3-large` and `-small` both support a `dimensions` parameter to truncate the output vector (Matryoshka representation). Useful for storage / latency tradeoffs:

```typescript
const r = await client.embeddings.create({
  model: "RESOLVED_ID",
  input: inputs,
  dimensions: 256,   // shrinks from 3072 → 256
});
```

## Cost-awareness

Embeddings are cheap ($0.02–0.13/1M tokens depending on model and tier as of 2026), but at high volume it adds up. Trigger the cost gate for inputs > 100K tokens total. For massive jobs (>1M tokens), use the **Batches API** for a 50% discount — see `references/files-and-batches.md`.
