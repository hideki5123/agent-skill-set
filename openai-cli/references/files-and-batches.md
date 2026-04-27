# Files and Batches

The Files API holds artifacts (datasets, batch JSONLs, fine-tuning corpora, downloadable outputs). The Batches API runs Chat Completions / Embeddings / etc. asynchronously over a JSONL of requests at **50% the per-token price** — the right choice for any workload >1K requests.

## Permissions

Files (upload / download): base perms PLUS `--allow-read=<source>` (upload) and `--allow-write=<dest>` (download).
Batches: base perms; for `--allow-read=<jsonl-path>` when uploading the input file.

## Files — upload

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const path = "ABSOLUTE_INPUT_PATH";
const file = await Deno.open(path, { read: true });

const f = await client.files.create({
  file: file.readable,
  purpose: "batch",   // "batch" | "fine-tune" | "assistants" | "vision" | "user_data"
});

console.log(`uploaded: id=${f.id} bytes=${f.bytes}`);
console.log(`# meta: file_id=${f.id}`);
```

## Files — list / retrieve / delete

```typescript
// list
const list = await client.files.list();
for (const f of list.data) console.log(`${f.id}\t${f.bytes}\t${f.purpose}\t${f.filename}`);

// retrieve
const f = await client.files.retrieve("FILE_ID");
console.log(JSON.stringify(f, null, 2));

// download content
const stream = await client.files.content("FILE_ID");
const text = await stream.text();
await Deno.writeTextFile("OUTPUT_PATH", text);

// delete
const d = await client.files.del("FILE_ID");
console.log(`deleted: ${d.id} (deleted=${d.deleted})`);
```

## Batches — submit

The input is a JSONL where each line describes one request. Each line must include a unique `custom_id`, the API endpoint, and the body that would normally go to that endpoint:

```jsonl
{"custom_id":"req-1","method":"POST","url":"/v1/chat/completions","body":{"model":"RESOLVED_ID","messages":[{"role":"user","content":"hi"}]}}
{"custom_id":"req-2","method":"POST","url":"/v1/chat/completions","body":{"model":"RESOLVED_ID","messages":[{"role":"user","content":"bye"}]}}
```

Build → upload → submit:

```typescript
import OpenAI from "npm:openai@5";

const client = new OpenAI();
const jsonlPath = "ABSOLUTE_INPUT_JSONL";

// 1. upload
const upload = await client.files.create({
  file: (await Deno.open(jsonlPath)).readable,
  purpose: "batch",
});
console.log(`uploaded: ${upload.id}`);

// 2. submit
const batch = await client.batches.create({
  input_file_id: upload.id,
  endpoint: "/v1/chat/completions",   // or "/v1/embeddings", "/v1/responses"
  completion_window: "24h",
});
console.log(`batch submitted: id=${batch.id} status=${batch.status}`);
console.log(`# meta: batch_id=${batch.id} input_file_id=${upload.id}`);
```

## Batches — poll

```typescript
const b = await client.batches.retrieve("BATCH_ID");
console.log(`${b.id}\tstatus=${b.status}\tcompleted=${b.request_counts?.completed}/${b.request_counts?.total}`);

// status values: validating, in_progress, finalizing, completed, expired, cancelling, cancelled, failed
```

## Batches — retrieve results

When `status === "completed"`, the result file id is in `b.output_file_id`. Download via `client.files.content`:

```typescript
const stream = await client.files.content(b.output_file_id);
const text = await stream.text();
// Each line is JSON: { id, custom_id, response: { status_code, body }, error }
for (const line of text.split("\n")) {
  if (!line.trim()) continue;
  const r = JSON.parse(line);
  console.log(`${r.custom_id}\t${r.response?.status_code}`);
}
```

## Cost gate

Batch submissions ARE the high-cost case. The skill **must** before any batch submit:
1. Count requests (line count).
2. Estimate input + output tokens per request (sample a few).
3. Multiply by the model's per-token price × 0.5 (batch discount).
4. Surface the estimate via `AskUserQuestion` and require confirmation.

For users not sure about the cost, suggest a small dry-run first (e.g., 10 requests).

## Common pitfalls

- **JSONL must be valid** — one JSON object per line, newline-delimited, UTF-8. No trailing comma.
- **`custom_id` must be unique** within the batch.
- **`completion_window` is `"24h"`** today; values < 24h may be added later.
- **Errors per-row** appear in `r.error` of each output line; non-fatal — the rest of the batch completes.
- **Output ordering is NOT guaranteed** to match input — always join by `custom_id`.
