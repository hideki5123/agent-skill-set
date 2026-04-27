# Models — per-session discovery, family heuristics, upgrade prompts

The skill **never hardcodes model names** in runtime call sites. Every API call resolves the model dynamically against `client.models.list()`, with a TTL cache so the listing API is hit at most **once per hour** per machine.

This file documents:
- The persisted preference file (`models.json`)
- The TTL cache (`.cache/models-list.json`)
- The family classification + tie-breaker heuristics
- The upgrade-prompt protocol

## Files

`~/.openai-cli/models.json` — persisted user preference per family:
```json
{
  "version": 1,
  "preferenceMode": "stable",
  "preferred": {
    "chat": "gpt-5.5",
    "reasoning": "o4-mini",
    "embeddings": "text-embedding-3-large",
    "image": "gpt-image-2",
    "transcription": "gpt-4o-transcribe",
    "tts": "tts-1-hd",
    "moderation": "omni-moderation-latest"
  },
  "lastUpgradePromptedAt": "2026-04-28T10:00:00Z"
}
```

> Values shown are illustrative — current latest stable as of 2026-04-27. The actual values come from `client.models.list()` at runtime via `lib/resolveModel.ts --init`. Don't copy these literals into TS call sites.

`preferenceMode`:
- `"stable"` (default) — excludes ids matching `/preview|alpha|beta|deprecated/i`
- `"preview"` — opt-in to bleeding-edge releases

`~/.openai-cli/.cache/models-list.json` — the TTL cache:
```json
{
  "fetchedAt": "2026-04-28T10:00:00Z",
  "data": [{ "id": "gpt-5.5", "created": 1714000000, "object": "model" }, ...]
}
```

TTL: **1 hour**. First call of a fresh agent session pays the ~200ms `models.list` cost; subsequent calls within the hour pay nothing.

## Family classification (heuristics)

`lib/resolveModel.ts` `classify(id)` returns one of: `chat | reasoning | embeddings | image | transcription | tts | moderation | null`. Order matters — first match wins:

| Order | Test | Family |
|-------|------|--------|
| 1 | `id.includes("transcribe") \|\| id.startsWith("whisper")` | `transcription` |
| 2 | `id.startsWith("tts-") \|\| /-tts(-\|$)/.test(id)` | `tts` |
| 3 | `id.startsWith("gpt-image-") \|\| id.startsWith("dall-e-")` | `image` |
| 4 | `id.startsWith("text-embedding-")` | `embeddings` |
| 5 | `id.startsWith("omni-moderation-") \|\| id.startsWith("text-moderation-")` | `moderation` |
| 6 | `/^o\d/.test(id)` | `reasoning` |
| 7 | `/^gpt-\d/.test(id)` (and not matched above) | `chat` |
| _ | else | `null` (unclassified) |

## Tie-breakers (which "newest" wins within a family)

After filtering by family and (in stable mode) excluding preview ids, candidates are sorted by:

1. **Family-specific score** (descending):
   - `moderation`: prefer `omni-` prefix over `text-moderation-` (which is deprecated)
   - `image`: prefer `gpt-image-` family over `dall-e-` (deprecated)
   - `embeddings`: prefer `*-large` over `*-small`
2. **`created` timestamp** (descending) — newest wins.

## Upgrade-prompt protocol

```
$ deno run ... lib/resolveModel.ts <family>
```

Three possible outcomes:

| Exit | Stdout | Skill action |
|------|--------|--------------|
| 0 | `<resolved-id>` | Capture the id, embed it in the per-call TS file, run the call. |
| 2 | `UPGRADE_NEEDED:<family>:<current>:<newest>` | **Mandatory: use `AskUserQuestion`** — even in auto-mode or dangerous-permission mode. Options: "Upgrade to `<newest>`", "Stay on `<current>`", "Use `<newest>` just-this-once". |
| 1 | error to stderr | Surface the error, stop the call. |

After `AskUserQuestion`:

| User choice | Skill action |
|-------------|--------------|
| Upgrade | `lib/resolveModel.ts --set <family> <newest>`, then re-resolve. |
| Stay | `lib/resolveModel.ts --set <family> <current>` (refreshes `lastUpgradePromptedAt`), use `<current>`. |
| Just-this-once | Skip `--set`. Use `<newest>` only for this call. |

The skill **never silently upgrades**. The `AskUserQuestion` step is non-negotiable.

## Initialization on first use

After the workspace is set up and `OPENAI_API_KEY` is exported:

```
deno run --allow-env=OPENAI_API_KEY --allow-net=api.openai.com --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --init
```

This calls `models.list()` once, picks the newest stable per family using the heuristics above, and writes `models.json`. No upgrade prompts on init (nothing to compare against).

## Pinning a specific model for one call

If the user says "use exactly `gpt-5.5-2026-04-24` for this call":
- Skip the resolver entirely for this invocation.
- Embed the exact id in the per-call TS file.
- Do **not** call `lib/resolveModel.ts --set` — the user pinned for this call only, not as a new default.

## Manual preference change

The user can update preferences directly:

```
deno run --allow-read --allow-write ~/.openai-cli/lib/resolveModel.ts --set chat gpt-5
```

Or by editing `~/.openai-cli/models.json` directly.

## When `models.list` fails

Network error, auth error, transient outage — `lib/resolveModel.ts` falls back to the persisted `preferred.<family>` and prints a warning to stderr (`# warn: models.list failed (...); using preferred`). If `preferred.<family>` is also missing (first-run + offline), the script exits 1 with a clear error — it **never invents a model name**.

## Re-running `--init`

Safe at any time. Overwrites the persisted preference for every family with the latest stable. Use sparingly — typically the upgrade-prompt flow handles drift incrementally.

## Why per-session, not per-call

The user explicitly noted that 0.2s × every call = noticeable overhead. Once-per-session (TTL = 1h) is the compromise: cold-call latency is paid at most once per hour, all subsequent calls reuse the cache.

If even the once-per-hour cost becomes a problem (e.g., batch workloads firing many short calls in a long session), consider the persistent-process optimization in the SKILL.md "Out of scope" list.
