# Auth Setup — `codex login`

**Read only when `~/.codex/auth.json` is missing** (the skill prints the
login guide and points here). Not needed during normal operation.

## TL;DR

```bash
codex login
```

The browser opens; sign in with your **ChatGPT account** (Plus / Pro / Team).
After you return to the terminal, `~/.codex/auth.json` is written. Re-invoke
the skill. Done.

## Why ChatGPT login (and not API key)?

`codex-server` is ChatGPT-subscription-only **by design**. The whole point of
using Codex App Server is that the user's ChatGPT subscription powers turns —
no `OPENAI_API_KEY` billing is consumed.

We enforce this two ways:

1. `OPENAI_API_KEY` is not in `--allow-env`. Even if exported in your shell,
   the deno process literally cannot read it.
2. The skill's `setup.ts` and every `chat.ts` subcommand existence-check
   `~/.codex/auth.json` and refuse to proceed otherwise.

## Supported account types

- **ChatGPT Plus** — works
- **ChatGPT Pro** — works
- **ChatGPT Team / Enterprise** — works
- **Free ChatGPT account** — may not have Codex access; check your account
- **OpenAI Platform account (API only)** — **not supported** for this skill;
  use `codex-cli` (which accepts `OPENAI_API_KEY`) if you need API-key auth.

## Troubleshooting

### "browser didn't open"

`codex login` opens the system default browser. If you're on a headless host
(SSH, container), `codex login` typically prints a URL to paste into a browser
on another machine, then waits for the callback. Read codex's own login flow
docs — `codex login --help` for current options.

### "I already ran codex login but auth.json isn't there"

Check the actual path:

```bash
ls -la ~/.codex/auth.json
```

The codex CLI writes there by default. If your `HOME` is unusual (e.g., in a
container), the file may be under a different `$HOME/.codex/auth.json`. The
skill uses `Deno.env.get("HOME") ?? Deno.env.get("USERPROFILE")` to locate it,
so it follows the standard env conventions.

### "I want to log out"

```bash
codex logout
```

Deletes the auth file. Re-run `codex login` to get a new one.

### "I want to switch accounts"

`codex logout && codex login` — sign in with a different account in the
browser flow.

## What ends up in auth.json

The skill **never reads** the contents of `auth.json`. We only check
existence via `Deno.stat`. The actual auth tokens / cookies / signed
credentials are consumed by the codex binary when it spawns the app-server.

We deliberately keep the secret off the deno process for defence in depth —
even if a future bug in deno or the SDK tried to log env vars, there are
none related to auth to leak.
