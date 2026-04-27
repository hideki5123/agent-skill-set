# Error handling

OpenAI API errors fall into a few categories. Handle them sanitized — never echo headers or auth-bearing content into Claude's tool output.

## Common HTTP errors

| Status | Class | Cause | Response |
|--------|-------|-------|----------|
| 400 | `BadRequestError` | malformed request, invalid params | inspect `e.message`, fix the request body |
| 401 | `AuthenticationError` | missing / wrong API key | tell the user to verify `OPENAI_API_KEY`; do not print the value |
| 403 | `PermissionDeniedError` | API key valid but lacks scope | check org/project setup |
| 404 | `NotFoundError` | resource (file/batch/model) not found | verify the id |
| 409 | `ConflictError` | resource state conflict | usually transient — retry once |
| 422 | `UnprocessableEntityError` | validation error in body | check the schema in the SDK docs |
| 429 | `RateLimitError` | request rate / token rate exceeded | back off (see below) |
| 500 / 502 / 503 / 504 | `InternalServerError` / `APIError` | OpenAI-side issue | retry with exponential backoff |

The official `openai` npm package exports typed error classes. Catch them specifically:

```typescript
import OpenAI, { APIError, RateLimitError, AuthenticationError } from "npm:openai@5";

try {
  const r = await client.chat.completions.create({ /* ... */ });
} catch (e) {
  if (e instanceof RateLimitError) {
    console.error("rate-limited; back off and retry");
  } else if (e instanceof AuthenticationError) {
    console.error("auth failed — verify OPENAI_API_KEY is set in your shell rc");
  } else if (e instanceof APIError) {
    console.error(`OpenAI error ${e.status}: ${sanitize(e.message)}`);
  } else {
    console.error(`unexpected error: ${(e as Error).message}`);
  }
  Deno.exit(1);
}
```

## Sanitizing error messages

The SDK's error message generally doesn't leak the API key, but headers and request payloads sometimes appear in error context. Always strip auth-bearing fragments before logging:

```typescript
function sanitize(msg: string): string {
  return msg
    .replace(/Bearer\s+[A-Za-z0-9_\-\.]+/g, "Bearer [REDACTED]")
    .replace(/sk-[A-Za-z0-9_\-]{10,}/g, "sk-[REDACTED]")
    .replace(/Authorization:\s*\S+/g, "Authorization: [REDACTED]");
}
```

Use `sanitize` on every `console.error` of an `APIError` or unknown exception.

## Retry policy

The SDK has automatic retries for 429 / 5xx via the `maxRetries` option (default 2). For long-running batch polling or stateful flows, use exponential backoff yourself:

```typescript
async function withRetry<T>(fn: () => Promise<T>, opts = { tries: 5, base: 500 }): Promise<T> {
  for (let i = 0; i < opts.tries; i++) {
    try {
      return await fn();
    } catch (e) {
      const retriable = e instanceof RateLimitError || (e instanceof APIError && e.status && e.status >= 500);
      if (!retriable || i === opts.tries - 1) throw e;
      const delay = opts.base * Math.pow(2, i) + Math.random() * opts.base;
      await new Promise((res) => setTimeout(res, delay));
    }
  }
  throw new Error("unreachable");
}
```

## Timeouts

Set explicit timeouts for long-running streaming or reasoning calls:

```typescript
const client = new OpenAI({
  timeout: 60_000,  // ms; default is 600_000 (10 min)
  maxRetries: 2,
});
```

## Network-failure fallback for the model resolver

`lib/resolveModel.ts` already handles `models.list()` failures by falling back to the persisted preference. If both the API call and `models.json` are unavailable (e.g., first run + offline), the resolver prints a fatal error and exits 1 — the skill must surface this to the user, not silently continue with an invented model name.

## Feedback log

After every non-trivial use case, the skill should append to `feedback/log.md` (in the skill source dir, OR in `~/.openai-cli/feedback/log.md` for runtime — pick one and stick to it):

```markdown
## 2026-04-28T10:34:12Z

- Use case: chat completion
- Family: chat → resolved gpt-5.5
- Result: success | rate-limit | auth-fail | other
- Notes: <one line about anything surprising>
```

This feeds the improvement loop over time — patterns help us detect drift in the OpenAI surface (model deprecations, parameter changes, new error classes).
