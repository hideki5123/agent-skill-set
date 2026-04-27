# Security — secrets are off-limits to AI agents

Hard constraint, not a soft preference. Skill-generated code and skill-issued shell commands must never read, log, or pass-through secret **values**. Existence-only checks; runtime-enforced isolation.

## Forbidden patterns (Bash / shell)

The skill must refuse these even if the user explicitly asks:

- `echo $OPENAI_API_KEY`, `echo "$OPENAI_API_KEY"`, `printf "%s" "$OPENAI_API_KEY"`
- `printenv | grep -i openai`, `env | grep OPENAI`, `set | grep OPENAI`
- `cat ~/.zshrc`, `cat ~/.bashrc`, `cat ~/.profile`, `cat ~/.config/op/...`
- Reading any `.env`, `*.secrets`, or `*.token` file
- Echoing the key to validate "did it set?" — use the boolean check below instead

## Forbidden patterns (TypeScript / generated code)

- `console.log(Deno.env.toObject())` or `console.log(Deno.env.get("OPENAI_API_KEY"))`
- `console.log(JSON.stringify(headers))` or any logging of the request `Authorization: Bearer ...` header
- `new OpenAI({ apiKey: Deno.env.get("OPENAI_API_KEY") })` — use `new OpenAI()` instead so the SDK reads env itself, never via a value the script saw
- Writing the key value into any file the skill creates

## Allowed: existence checks

```ts
// In a deno script:
const keySet = Deno.env.get("OPENAI_API_KEY") !== undefined;
console.log(keySet ? "key: set" : "key: missing");
```

```sh
# In bash/zsh (cross-OS via mise/deno scripts is preferred — but if needed):
[ -n "$OPENAI_API_KEY" ] && echo "key: set" || echo "key: missing"
```

Either form prints only `set` / `missing`, never the value.

## Refusing user requests to print the key

If the user says "show me my OPENAI_API_KEY" or "echo `$OPENAI_API_KEY`":
- The skill politely refuses.
- Points the user to their own (non-agent) terminal: "Run `echo $OPENAI_API_KEY` from a terminal where I'm not orchestrating, if you need to see it."
- Does not accept "but I really want it" — this is a hard rule.

## Generalization to any secret

Same rules apply to:
- `OPENAI_ORG_ID`, `OPENAI_PROJECT`
- OAuth tokens, refresh tokens
- Session cookies (e.g., `__Secure-next-auth.session-token`)
- Signed URLs containing tokens
- 1Password / Doppler / Vault references — even if the path is reachable, the value is not.

When in doubt, use existence checks, not value reads.

## Deno permission flags as runtime defense-in-depth

Even if a generated script is buggy or hostile, deno's permission system contains the blast radius. Each `--allow-*` flag opens one capability and can be **scoped** with `=value`.

| Flag | Without it | Scoped (e.g., `=OPENAI_API_KEY`) | Broad (no `=value`) |
|------|-----------|----------------------------------|---------------------|
| `--allow-env` | `Deno.env.get(...)` returns null | only the named var(s) readable | all env vars readable |
| `--allow-net` | `fetch()` blocked | only the named host(s) reachable | any host reachable |
| `--allow-read` | file reads denied | only named paths readable | any path readable |
| `--allow-write` | file writes denied | only named paths writable | any path writable |
| `--allow-run` | subprocess spawning denied | only named binaries runnable | any binary |
| `--allow-ffi` / `--allow-sys` | each capability denied | n/a | grants the capability |

**The skill always uses scoped flags.** Standard base perms for an OpenAI API call:

```
--allow-env=OPENAI_API_KEY
--allow-net=api.openai.com
--allow-read=$HOME/.openai-cli
--allow-write=$HOME/.openai-cli
```

Add I/O scopes per use case:
- Image gen: `--allow-write=<output-image-path>` (e.g., `--allow-write=$HOME/Downloads/cat.png`)
- Audio transcription: `--allow-read=<input-audio-path>`
- TTS: `--allow-write=<output-audio-path>`
- File upload: `--allow-read=<source>`

**Never use `--allow-all`, bare `--allow-env`, bare `--allow-net`, or bare `--allow-read`/`--allow-write`** without scoped values.

## Why this matters more for AI-generated code

A human developer writes code, reviews it, runs it. An AI agent generates code on the fly under user instructions — much harder to audit per-call. Scoped permissions give you a runtime backstop: even if the AI generates a script that tries to fetch Slack secrets and POST them to an attacker, deno's `--allow-env=OPENAI_API_KEY --allow-net=api.openai.com` flat-out denies both operations.

## Audit trail

Every call's TS file lives at `~/.openai-cli/tmp/<task>-<timestamp>.ts` after invocation. Inspect it any time:

```sh
# Just list — don't grep for "OPENAI_API_KEY" expecting to find a value;
# the file should never contain the value in the first place.
ls -t ~/.openai-cli/tmp/ | head -20
```

If you find a per-call TS file that contains the literal API key value, that's a bug — file an issue.
