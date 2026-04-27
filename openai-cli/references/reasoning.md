# Reasoning models (o-series)

OpenAI's o-series models (`o1`, `o3`, `o4`, etc.) are designed for hard reasoning tasks — math, code synthesis, planning. They spend tokens on hidden chain-of-thought before emitting the answer. Slower, more expensive per call, but materially better on the hardest tasks.

As of 2026-04, **`o4-mini` is the latest stable o-series**. There were no new o-series releases in Q1-Q2 2026; OpenAI is steering reasoning workloads toward the chat-family models' reasoning mode (e.g., `gpt-5.5` with `reasoning: { effort: "high" }`).

`o3`, `o3-mini`, `o3-pro`, `o1*` are deprecated.

## Family

`reasoning` → `lib/resolveModel.ts reasoning`. Returns `o4-mini` today.

## When to choose `reasoning` vs chat-family with reasoning effort

| Use case | Recommendation |
|----------|----------------|
| Pure puzzle / math / proof | `reasoning` (`o4-mini`) |
| Code synthesis with tool use | `chat` (`gpt-5.5`) with `reasoning.effort = "high"` — Responses API for tool support |
| Long-context analysis with reasoning | `chat` (`gpt-5.5`, 1M context) with `reasoning.effort = "medium"` or `"high"` |
| Cheap fast Q&A | `chat` (`gpt-5.5`) with default reasoning |
| Vision + reasoning | `chat` (`gpt-5.5`) — o-series doesn't take images well |

The user can override with an explicit pin if they want a specific model.

## Per-call TS template (Chat Completions API)

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();

const r = await client.chat.completions.create({
  model: "RESOLVED_ID",   // from `lib/resolveModel.ts reasoning`
  messages: [
    { role: "user", content: "Prove that ..." },
  ],
  reasoning_effort: "high",   // o-series accepts this directly
  max_completion_tokens: 8000,
});

console.log(r.choices[0]?.message?.content ?? "");
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

`reasoning_effort` values: `"minimal"` | `"low"` | `"medium"` | `"high"`.

## Per-call TS template (Responses API — preferred for new work)

```typescript
const r = await client.responses.create({
  model: "RESOLVED_ID",
  input: "Prove that ...",
  reasoning: { effort: "high" },
});

console.log(r.output_text);
console.log(`# meta: model=${r.model} usage=${JSON.stringify(r.usage)}`);
```

The Responses API also exposes the reasoning summary (when available) via `r.output` — iterate items where `item.type === "reasoning"`.

## Cost-awareness

Reasoning models burn hidden tokens on the chain-of-thought before the visible answer. Cost can be 2-5× a non-reasoning chat completion of the same prompt. Always:

1. Trigger the cost-gate for any reasoning call where the input is > 1K tokens or output > 500 tokens.
2. Default `effort` to `"medium"` unless the user asked for harder thinking.
3. Surface `r.usage.completion_tokens_details.reasoning_tokens` (if present) in the meta line so the user sees how much hidden reasoning happened.

Updated meta line for reasoning calls:

```typescript
const usage = r.usage;
const reasoningTokens = (usage as any)?.completion_tokens_details?.reasoning_tokens ?? 0;
console.log(`# meta: model=${r.model} usage=${JSON.stringify(usage)} reasoning_tokens=${reasoningTokens}`);
```

## Vision and tool use limitations

`o4-mini` and predecessors have limited (or no) image-input support. If the user's task is multimodal AND reasoning-heavy, prefer `chat` family with `reasoning.effort = "high"` — `gpt-5.5` is multimodal and reasoning-capable.
