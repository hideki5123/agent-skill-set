# Error handling

The Notion API uses standard HTTP status codes plus a structured `code` string. The SDK's `APIErrorCode` enum maps to these. The CLI surfaces both `status` and `code` (and a sanitized `message`) on failure.

## Decoding common errors

### 401 — `unauthorized`

Token is wrong, revoked, or empty.

- Re-copy the Internal Integration Secret from <https://www.notion.so/profile/integrations> → your integration → Configuration → Show.
- Make sure your active token source is in the **same shell** that's running deno. Setting `NOTION_TOKEN` in `~/.zshrc` doesn't apply to an already-open terminal; for `NOTION_TOKEN_FILE`, the file must be present (e.g. agenix mounts at activation time — check with `[ -r "$NOTION_TOKEN_FILE" ]`).
- If you regenerated the token recently, every other terminal session also needs to re-source. For agenix / sops-nix, run `darwin-rebuild switch` (or `home-manager switch` / `nixos-rebuild switch`) so the new file is materialized.

### 403 — `restricted_resource`

The token is valid, but the integration lacks the required capability.

- Open the integration → Capabilities tab.
- For reads: enable **Read content**.
- For creates/updates: enable **Insert content** + **Update content**.
- For user listing: enable **Read user information**.

Save and retry. Capability changes take effect immediately.

### 404 — `object_not_found`

This is the most common error after first-time setup. It means **the integration has not been added to the page or database** (not that the page doesn't exist). It's the same response Notion uses when you try to access a deleted resource — the API doesn't disambiguate, on purpose.

Fix:

1. Open the page or database in Notion.
2. Click `•••` (top-right) → **Connections** → **Add connections** → pick the integration.
3. Retry the call.

For databases, the integration also needs access to any **related** databases referenced by relation properties.

### 409 — `conflict_error`

Two writes raced. The CLI doesn't auto-retry.

- For `page update`, fetch the latest version with `page get`, merge your change, and retry.
- For `blocks append`, simply retry; the SDK is idempotent only for create-by-explicit-id, which the CLI does not use.

### 429 — `rate_limited`

Notion publishes "average 3 requests per second per integration." Bursts above that get throttled.

- Read the `Retry-After` header (the SDK exposes it on `error.headers`). Sleep that many seconds and retry once.
- For batch operations, insert a `setTimeout` of ~350 ms between requests to stay under the limit.
- If you're paginating a large database, prefer a tighter filter over walking thousands of rows.

### 400 — `validation_error`

Body shape is wrong. The error message includes the offending field.

- For property updates, re-check the property's type with `db get`. A `select`-typed property rejects a `status` body and vice-versa.
- For block append, check shapes against `references/property-types.md`. The most common mistake is forgetting that `rich_text` is always an array of objects (not a string).
- For status values, run `db get` to see the allowed option names; status options can't be created via API — only edited in the UI.

### `gateway_timeout`, 502, 503

Transient. Retry once after 1–2 seconds. If it persists, check <https://status.notion.so/>.

## Error-output shape

The CLI exits non-zero and prints to stderr a JSON envelope:

```json
{ "error": { "status": 404, "code": "object_not_found", "message": "Could not find ..." } }
```

This is intentionally machine-readable. With `--format text`:

```
error: 404 object_not_found: Could not find ...
hint: share the page with the integration in Notion (••• → Connections)
```

For 401/403/404 the CLI appends a one-line hint pointing to the most likely fix.

### `missing_token` / `empty_token_file` / `token_file_unreadable` (status 0)

These are emitted by the CLI itself before any HTTP call. They mean the token resolution chain failed before reaching the API.

- `missing_token`: none of `NOTION_TOKEN`, `NOTION_API_KEY`, or `NOTION_TOKEN_FILE` is satisfied. Pick one route in `references/auth-setup.md`.
- `empty_token_file`: `NOTION_TOKEN_FILE` is set but the file is empty. Re-materialize via your secrets manager (`darwin-rebuild switch` for agenix, `sops -d` round-trip for sops-nix, etc.) or check the source `.age` / `.sops.yaml` artifact for the right entry.
- `token_file_unreadable`: deno could not open the file. The most common cause is a missing `--allow-read=$NOTION_TOKEN_FILE` permission (deno does not auto-grant read access to paths outside `$HOME/.notion-cli`). Other causes: the file was not yet materialized at the time of the call, the file mode is `0000`, or the file is owned by another user. The error message includes the underlying OS error.

## Sanitization

The CLI never prints:

- The `Authorization` header.
- The full token value (even partially masked).
- Cookie or Set-Cookie headers (Notion's API doesn't return these, but be defensive).

If you write your own one-off scripts using the SDK, keep this rule. The SDK error objects are safe to log only AFTER you delete `error.headers` and any `error.config` field.
